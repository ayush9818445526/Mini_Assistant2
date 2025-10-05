class TaraAvatar {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.avatar = null;
        this.mixer = null;
        this.clock = new THREE.Clock();
        
        // Animation states
        this.currentEmotion = 'neutral';
        this.isSpeaking = false;
        this.mouthAnimation = null;
        this.eyeAnimation = null;
        
        // WebSocket connection
        this.ws = null;
        this.reconnectInterval = null;
        
        // UI elements
        this.statusBar = document.getElementById('connection-status');
        this.actionBar = document.getElementById('current-action');
        this.emotionIndicator = document.getElementById('emotion-indicator');
        this.loadingDiv = document.getElementById('loading');
        
        this.init();
    }
    
    async init() {
        console.log('[Avatar] Initializing TARA 3D Avatar...');
        
        try {
            this.setupScene();
            await this.loadAvatar();
            this.setupLighting();
            this.setupWebSocket();
            this.animate();
            
            // Hide loading screen
            this.loadingDiv.style.display = 'none';
            this.updateStatus('Connected', 'Ready');
            
        } catch (error) {
            console.error('[Avatar] Initialization failed:', error);
            this.showError('Failed to load avatar');
        }
    }
    
    setupScene() {
        // Create scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x000000);
        this.scene.background = null; // Transparent background
        
        // Create camera
        this.camera = new THREE.PerspectiveCamera(
            75, 
            window.innerWidth / window.innerHeight, 
            0.1, 
            1000
        );
        this.camera.position.set(0, 1.6, 3);
        this.camera.lookAt(0, 1.6, 0);
        
        // Create renderer
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true, 
            alpha: true 
        });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        
        document.getElementById('avatar-container').appendChild(this.renderer.domElement);
        
        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());
    }
    
    async loadAvatar() {
        console.log('[Avatar] Loading 3D model...');
        
        // Create a simple geometric avatar since we can't guarantee GLTF model availability
        await this.createGeometricAvatar();
    }
    
    async createGeometricAvatar() {
        // Create avatar group
        this.avatar = new THREE.Group();
        
        // Head
        const headGeometry = new THREE.SphereGeometry(0.5, 32, 32);
        const headMaterial = new THREE.MeshPhongMaterial({ 
            color: 0xffdbac,
            shininess: 30
        });
        const head = new THREE.Mesh(headGeometry, headMaterial);
        head.position.y = 1.6;
        head.castShadow = true;
        this.avatar.add(head);
        
        // Eyes
        const eyeGeometry = new THREE.SphereGeometry(0.08, 16, 16);
        const eyeMaterial = new THREE.MeshPhongMaterial({ color: 0x000000 });
        
        const leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
        leftEye.position.set(-0.15, 1.7, 0.35);
        this.avatar.add(leftEye);
        
        const rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
        rightEye.position.set(0.15, 1.7, 0.35);
        this.avatar.add(rightEye);
        
        // Store eye references for animations
        this.leftEye = leftEye;
        this.rightEye = rightEye;
        
        // Mouth
        const mouthGeometry = new THREE.SphereGeometry(0.06, 16, 8);
        const mouthMaterial = new THREE.MeshPhongMaterial({ color: 0x8B0000 });
        const mouth = new THREE.Mesh(mouthGeometry, mouthMaterial);
        mouth.position.set(0, 1.45, 0.4);
        mouth.scale.set(1.5, 0.5, 0.8);
        this.avatar.add(mouth);
        this.mouth = mouth;
        
        // Body (simple cylinder)
        const bodyGeometry = new THREE.CylinderGeometry(0.3, 0.4, 1.2, 16);
        const bodyMaterial = new THREE.MeshPhongMaterial({ color: 0x4169E1 });
        const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
        body.position.y = 0.6;
        body.castShadow = true;
        this.avatar.add(body);
        
        // Add avatar to scene
        this.scene.add(this.avatar);
        
        // Add subtle idle animation
        this.startIdleAnimation();
        
        console.log('[Avatar] Geometric avatar created successfully');
    }
    
    setupLighting() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);
        
        // Directional light
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 10, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);
        
        // Point light for face illumination
        const pointLight = new THREE.PointLight(0xffffff, 0.5, 10);
        pointLight.position.set(0, 2, 2);
        this.scene.add(pointLight);
    }
    
    setupWebSocket() {
        this.connectWebSocket();
        
        // Reconnect on connection loss
        this.reconnectInterval = setInterval(() => {
            if (!this.ws || this.ws.readyState === WebSocket.CLOSED) {
                this.connectWebSocket();
            }
        }, 5000);
    }
    
    connectWebSocket() {
        try {
            this.ws = new WebSocket('ws://localhost:8765');
            
            this.ws.onopen = () => {
                console.log('[Avatar] WebSocket connected');
                this.updateStatus('Connected', 'Listening');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('[Avatar] Failed to parse message:', error);
                }
            };
            
            this.ws.onclose = () => {
                console.log('[Avatar] WebSocket disconnected');
                this.updateStatus('Disconnected', 'Waiting for connection');
            };
            
            this.ws.onerror = (error) => {
                console.error('[Avatar] WebSocket error:', error);
            };
            
        } catch (error) {
            console.error('[Avatar] Failed to create WebSocket:', error);
            this.updateStatus('Connection Failed', 'Retrying...');
        }
    }
    
    handleMessage(data) {
        console.log('[Avatar] Received message:', data);
        
        switch (data.type) {
            case 'speak':
                this.startSpeaking(data.text, data.duration || 3000);
                this.updateStatus('Connected', `Speaking: "${data.text.substring(0, 30)}..."`);
                break;
                
            case 'emotion':
                this.setEmotion(data.emotion);
                break;
                
            case 'action':
                this.updateStatus('Connected', data.action);
                break;
                
            case 'stop_speaking':
                this.stopSpeaking();
                break;
        }
    }
    
    startSpeaking(text, duration) {
        console.log(`[Avatar] Speaking: "${text}"`);
        this.isSpeaking = true;
        
        // Add speaking class to emotion indicator
        this.emotionIndicator.classList.add('speaking');
        
        // Start mouth animation
        this.startMouthAnimation();
        
        // Stop speaking after duration
        setTimeout(() => {
            this.stopSpeaking();
        }, duration);
    }
    
    stopSpeaking() {
        console.log('[Avatar] Stopped speaking');
        this.isSpeaking = false;
        
        // Remove speaking class
        this.emotionIndicator.classList.remove('speaking');
        
        // Stop mouth animation
        this.stopMouthAnimation();
        
        this.updateStatus('Connected', 'Listening');
    }
    
    startMouthAnimation() {
        if (this.mouthAnimation) {
            this.mouthAnimation.kill();
        }
        
        // Simple mouth open/close animation
        this.mouthAnimation = gsap.to(this.mouth.scale, {
            y: 1.2,
            duration: 0.15,
            repeat: -1,
            yoyo: true,
            ease: "power2.inOut"
        });
    }
    
    stopMouthAnimation() {
        if (this.mouthAnimation) {
            this.mouthAnimation.kill();
            // Reset mouth scale
            gsap.to(this.mouth.scale, {
                y: 0.5,
                duration: 0.2,
                ease: "power2.out"
            });
        }
    }
    
    setEmotion(emotion) {
        if (this.currentEmotion === emotion) return;
        
        console.log(`[Avatar] Expression changed: ${emotion}`);
        this.currentEmotion = emotion;
        
        // Update emotion indicator
        const emotionEmojis = {
            'neutral': '😐 Neutral',
            'happy': '😊 Happy',
            'thinking': '🤔 Thinking',
            'surprised': '😲 Surprised',
            'sad': '😔 Sad',
            'excited': '😄 Excited'
        };
        
        this.emotionIndicator.textContent = emotionEmojis[emotion] || '😐 Neutral';
        
        // Animate facial expression changes
        this.animateExpression(emotion);
    }
    
    animateExpression(emotion) {
        // Kill existing eye animations
        if (this.eyeAnimation) {
            this.eyeAnimation.kill();
        }
        
        switch (emotion) {
            case 'happy':
                // Squint eyes slightly for smile
                this.eyeAnimation = gsap.to([this.leftEye.scale, this.rightEye.scale], {
                    y: 0.7,
                    duration: 0.5,
                    ease: "power2.out"
                });
                break;
                
            case 'surprised':
                // Wide eyes
                this.eyeAnimation = gsap.to([this.leftEye.scale, this.rightEye.scale], {
                    x: 1.3,
                    y: 1.3,
                    z: 1.3,
                    duration: 0.3,
                    ease: "back.out(1.7)"
                });
                break;
                
            case 'thinking':
                // Slight eye movement
                this.eyeAnimation = gsap.timeline({ repeat: -1, yoyo: true })
                    .to([this.leftEye.position, this.rightEye.position], {
                        y: "+=0.02",
                        duration: 1,
                        ease: "power2.inOut"
                    });
                break;
                
            case 'sad':
                // Droopy eyes
                this.eyeAnimation = gsap.to([this.leftEye.position, this.rightEye.position], {
                    y: "-=0.05",
                    duration: 0.5,
                    ease: "power2.out"
                });
                break;
                
            default: // neutral
                // Reset to normal
                this.eyeAnimation = gsap.to([this.leftEye.scale, this.rightEye.scale], {
                    x: 1,
                    y: 1,
                    z: 1,
                    duration: 0.5,
                    ease: "power2.out"
                });
                gsap.to([this.leftEye.position, this.rightEye.position], {
                    y: 1.7,
                    duration: 0.5,
                    ease: "power2.out"
                });
                break;
        }
    }
    
    startIdleAnimation() {
        // Subtle breathing animation
        gsap.to(this.avatar.scale, {
            y: 1.02,
            duration: 3,
            repeat: -1,
            yoyo: true,
            ease: "power2.inOut"
        });
        
        // Gentle head movement
        gsap.to(this.avatar.rotation, {
            y: 0.05,
            duration: 4,
            repeat: -1,
            yoyo: true,
            ease: "power2.inOut"
        });
    }
    
    updateStatus(connection, action) {
        this.statusBar.textContent = connection;
        this.actionBar.textContent = action;
    }
    
    showError(message) {
        this.loadingDiv.innerHTML = `
            <div style="color: #ff6b6b; text-align: center;">
                <div style="font-size: 24px; margin-bottom: 10px;">⚠️</div>
                <div>${message}</div>
                <div style="font-size: 12px; margin-top: 10px; opacity: 0.7;">
                    Check console for details
                </div>
            </div>
        `;
    }
    
    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        const delta = this.clock.getDelta();
        
        // Update mixer if available
        if (this.mixer) {
            this.mixer.update(delta);
        }
        
        this.renderer.render(this.scene, this.camera);
    }
    
    destroy() {
        if (this.ws) {
            this.ws.close();
        }
        if (this.reconnectInterval) {
            clearInterval(this.reconnectInterval);
        }
        if (this.mouthAnimation) {
            this.mouthAnimation.kill();
        }
        if (this.eyeAnimation) {
            this.eyeAnimation.kill();
        }
    }
}

// Initialize avatar when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.taraAvatar = new TaraAvatar();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.taraAvatar) {
        window.taraAvatar.destroy();
    }
});
