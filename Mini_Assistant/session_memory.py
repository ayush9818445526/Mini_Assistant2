import threading
import re
from collections import deque
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class SessionMemory:
    """
    Lightweight, thread-safe in-session memory for:
    - Last 20 messages (user and assistant)
    - Last 10 search queries with parsed results [{title, url, snippet}]
    - Resolving references like "first article", "second result", "last search", "this/that video"
    """

    ORDINAL_MAP = {
        "first": 1,
        "second": 2,
        "third": 3,
        "fourth": 4,
        "fifth": 5,
        "sixth": 6,
        "seventh": 7,
        "eighth": 8,
        "ninth": 9,
        "tenth": 10,
        # numeric ordinals like 1st, 2nd, 3rd, 4th... handled separately
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._messages: deque = deque(maxlen=20)
        self._search_history: deque = deque(maxlen=10)
        self._last_reference: Optional[Tuple[int, int]] = None  # (search_index, result_index)

    def clear(self):
        with self._lock:
            self._messages.clear()
            self._search_history.clear()
            self._last_reference = None
            print("[SessionMemory] Cleared for fresh session")

    # ------------------ Messages ------------------
    def add_user_message(self, text: str):
        with self._lock:
            self._messages.append({
                "role": "user",
                "text": text,
                "timestamp": datetime.now().isoformat()
            })
            print(f"[SessionMemory] User message stored: {text[:80]}")

    def add_assistant_message(self, text: str):
        with self._lock:
            self._messages.append({
                "role": "assistant",
                "text": text,
                "timestamp": datetime.now().isoformat()
            })
            print(f"[SessionMemory] Assistant message stored: {text[:80]}")

    def get_last_user_message(self) -> Optional[str]:
        with self._lock:
            for m in reversed(self._messages):
                if m.get("role") == "user":
                    return m.get("text")
        return None

    # ------------------ Search Results ------------------
    def add_search_results(self, query: str, results: List[Dict[str, str]]):
        """Store parsed search results for a query. Results are list of {title, url, snippet}."""
        if results is None:
            results = []
        with self._lock:
            self._search_history.append({
                "query": query,
                "results": results,
                "timestamp": datetime.now().isoformat()
            })
            print(f"[SessionMemory] Stored search results: '{query}' with {len(results)} results")

    def get_search_result_item(self, search_index: int, result_index: int) -> Optional[Dict[str, str]]:
        """
        Get an item by search_index (0 = most recent) and result_index (0-based).
        Returns dict {title, url, snippet} or None.
        """
        with self._lock:
            if not self._search_history:
                return None
            if search_index < 0 or search_index >= len(self._search_history):
                return None
            results = self._search_history[-1 - search_index]["results"]
            if result_index < 0 or result_index >= len(results):
                return None
            item = results[result_index]
            # Remember last reference
            abs_search_index = len(self._search_history) - 1 - search_index
            self._last_reference = (abs_search_index, result_index)
            return item

    # ------------------ Reference Resolution ------------------
    def resolve_reference(self, ref_text: str) -> Optional[Dict[str, object]]:
        """
        Resolve references like "first article", "second result", "last search",
        and pronouns like "this/that video" or "earlier result".
        Returns dict with keys: { item, search_index, result_index } or None.
        """
        text = (ref_text or "").lower().strip()
        if not text:
            return None

        with self._lock:
            if not self._search_history:
                print("[SessionMemory] No search history to resolve references")
                return None

            # Determine search target: default = last search
            search_sel = 0  # 0 means most recent, 1 means previous, etc.
            if any(k in text for k in ["last search", "recent search", "previous search", "earlier search"]):
                search_sel = 0
            elif "second last search" in text or "previous" in text:
                search_sel = 1

            # Detect ordinal or numeric selection
            ordinal = self._extract_ordinal(text)
            if ordinal is None:
                # Pronouns like "this", "that" try last reference first
                if any(p in text for p in ["this", "that", "these", "those", "earlier", "previous"]):
                    if self._last_reference is not None:
                        s_idx, r_idx = self._last_reference
                        if 0 <= s_idx < len(self._search_history):
                            item = self._search_history[s_idx]["results"][r_idx] if r_idx < len(self._search_history[s_idx]["results"]) else None
                            if item:
                                print(f"[SessionMemory] Resolved pronoun to last referenced result #{r_idx+1}")
                                return {"item": item, "search_index": s_idx, "result_index": r_idx}
                    # Fallback to first result of last search
                    ordinal = 1
                else:
                    # Default fallback: first result of last search
                    ordinal = 1

            result_index = max(0, ordinal - 1)

            # Try to map content type hints but currently not filtering by type
            # Select from chosen search set
            target_abs_search_idx = len(self._search_history) - 1 - search_sel
            results = self._search_history[target_abs_search_idx]["results"]
            if not results:
                print("[SessionMemory] Selected search has no results to resolve")
                return None
            if result_index >= len(results):
                result_index = len(results) - 1

            item = results[result_index]
            self._last_reference = (target_abs_search_idx, result_index)
            print(f"[SessionMemory] Resolved reference -> search[{target_abs_search_idx}] result[{result_index}] -> {item.get('title','')[:60]}")
            return {"item": item, "search_index": target_abs_search_idx, "result_index": result_index}

    # ------------------ Helpers ------------------
    def _extract_ordinal(self, text: str) -> Optional[int]:
        # Try word ordinals
        for word, num in self.ORDINAL_MAP.items():
            if re.search(rf"\b{word}\b", text):
                return num
        # Try numeric ordinals like 1st, 2nd, 3rd, 4th
        m = re.search(r"\b(\d+)(st|nd|rd|th)?\b", text)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                pass
        # Try explicit mentions like "result number 3"
        m2 = re.search(r"result\s+number\s+(\d+)", text)
        if m2:
            try:
                return int(m2.group(1))
            except Exception:
                pass
        # Detect "last"
        if re.search(r"\blast\b", text):
            # We'll handle by returning a sentinel -1 and caller will map to last index
            return 10**9  # large number to clamp to last
        return None
