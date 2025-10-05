/**
 * Three.js 3D Rubik's Cube Visualization
 *
 * Professional 3D cube renderer with smooth animations, mobile touch controls,
 * and real-time state synchronization.
 */

class Cube3D {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.canvas = this.container.querySelector('.cube-canvas');

        // Three.js core objects
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;

        // Cube objects
        this.cubeGroup = null;
        this.cubies = []; // Individual cube pieces
        this.size = 3;

        // Animation
        this.animationQueue = [];
        this.isAnimating = false;
        this.animationSpeed = 500; // ms

        // Interaction modes - start in hybrid cube mode
        this.interactionMode = 'cube'; // 'view' or 'cube' - hybrid mode with both enabled
        this.selectedFace = null;
        this.boundHandleFaceClick = this.handleFaceClick.bind(this);

        // Track drag state using OrbitControls events
        this.isDragging = false;

        // Double-tap detection for mobile
        this.lastTapTime = 0;
        this.lastTapPosition = { x: 0, y: 0 };
        this.lastTapFace = null;
        this.tapTimeout = null;
        this.doubleTapDelay = 300; // milliseconds

        // Colors mapping (WCA standard)
        this.colors = {
            'WHITE': 0xffffff,
            'YELLOW': 0xffd500,
            'RED': 0xff0000,
            'ORANGE': 0xff4500,  // More vibrant orange (OrangeRed) - much more distinct from yellow
            'GREEN': 0x00ff00,
            'BLUE': 0x0000ff,
            'BLACK': 0x000000 // For internal/hidden faces
        };

        this.init();
    }

    init() {
        this.initScene();
        this.initCamera();
        this.initRenderer();
        this.initControls();
        this.initCube();
        this.initLighting();

        // Start render loop
        this.animate();

        // Handle resize
        window.addEventListener('resize', () => this.handleResize());

        // Use ResizeObserver for container size changes (better for responsive CSS)
        if (typeof ResizeObserver !== 'undefined') {
            const resizeObserver = new ResizeObserver(() => {
                this.handleResize();
            });
            resizeObserver.observe(this.container);
        }

        // Trigger initial resize after a short delay to ensure CSS has applied
        setTimeout(() => this.handleResize(), 100);

        // Smart mode toggle based on current mode:
        // - In VIEW mode: Right-click toggles to CUBE mode
        // - In CUBE mode: Middle-click toggles to VIEW mode
        this.renderer.domElement.addEventListener('contextmenu', (event) => {
            // Only handle right-click in VIEW mode
            if (this.interactionMode === 'view') {
                event.preventDefault();
                event.stopPropagation();
                if (window.uiControls && typeof window.uiControls.handleInteractionModeToggle === 'function') {
                    window.uiControls.handleInteractionModeToggle();
                }
            }
            // In CUBE mode, right-click is used for counter-clockwise rotation, so don't toggle
        });

        // Use OrbitControls events to track drag state - they can't be blocked!
        this.controls.addEventListener('start', () => {
            // Save camera position at start to detect actual movement
            this.cameraStartPosition = this.camera.position.clone();
            this.cameraStartTarget = this.controls.target.clone();
            this.cameraChangeCount = 0;
        });

        this.controls.addEventListener('change', () => {
            // Count how many times the camera changed
            this.cameraChangeCount++;
        });

        this.controls.addEventListener('end', () => {
            // Check if camera actually moved significantly
            const positionDelta = this.camera.position.distanceTo(this.cameraStartPosition);
            const targetDelta = this.controls.target.distanceTo(this.cameraStartTarget);
            const totalMovement = positionDelta + targetDelta;

            // Consider it a drag if camera moved more than a small threshold OR had many changes
            this.isDragging = totalMovement > 0.3 || this.cameraChangeCount > 8;
        });

        // Handle middle-click for optional mode toggle (legacy support)
        window.addEventListener('mousedown', (event) => {
            if (event.button === 1 && this.interactionMode === 'cube') {
                event.preventDefault();
                event.stopPropagation();
                if (window.uiControls && typeof window.uiControls.handleInteractionModeToggle === 'function') {
                    window.uiControls.handleInteractionModeToggle();
                }
            }
        }, true);

        // Prevent auxclick default on middle-click only in CUBE mode
        this.renderer.domElement.addEventListener('auxclick', (event) => {
            if (event.button === 1 && this.interactionMode === 'cube') {
                event.preventDefault();
                event.stopPropagation();
            }
        }, true);

        // Enable face interaction immediately for hybrid mode
        this.enableFaceInteraction();
    }

    initScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf0f4f8);

        // Add fog for depth perception
        this.scene.fog = new THREE.Fog(0xf0f4f8, 10, 50);
    }

    initCamera() {
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 1000);
        this.camera.position.set(-3.5, 3.5, -3.5);
        this.camera.lookAt(0, 0, 0);
    }

    initRenderer() {
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true,
            alpha: true
        });

        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputEncoding = THREE.sRGBEncoding;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.2;
    }

    initControls() {
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.enableZoom = true;
        this.controls.enablePan = false;
        this.controls.minDistance = 2;
        this.controls.maxDistance = 12;
        this.controls.maxPolarAngle = Math.PI;
        this.controls.autoRotate = false;
        this.controls.autoRotateSpeed = 2.0;
        this.controls.target.set(0, 0, 0); // Ensure camera targets center

        // Touch support
        this.controls.touches = {
            ONE: THREE.TOUCH.ROTATE,
            TWO: THREE.TOUCH.DOLLY_PAN
        };

        // Ensure controls are enabled by default (view mode)
        this.controls.enabled = true;

        // Enhanced interaction feedback (disabled for production)
        // this.controls.addEventListener('start', () => { });
        // this.controls.addEventListener('change', () => { });
        // this.controls.addEventListener('end', () => { });

    }

    initLighting() {
        // Ambient light for overall illumination
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);

        // Main directional light
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 10, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 50;
        this.scene.add(directionalLight);

        // Fill light from opposite side
        const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
        fillLight.position.set(-5, -5, -5);
        this.scene.add(fillLight);

        // Rim light for edge definition
        const rimLight = new THREE.DirectionalLight(0xffffff, 0.2);
        rimLight.position.set(0, 0, -10);
        this.scene.add(rimLight);
    }

    initCube() {
        this.cubeGroup = new THREE.Group();
        this.scene.add(this.cubeGroup);

        this.createCubies();
        this.updateCubeState({
            faces: this.getDefaultSolvedState(),
            size: 3,
            solved: true
        });
    }

    createCubies() {
        this.cubies = [];
        const cubeSize = 0.98; // Slightly smaller than 1 to show gaps
        const spacing = 1;

        for (let x = 0; x < this.size; x++) {
            for (let y = 0; y < this.size; y++) {
                for (let z = 0; z < this.size; z++) {
                    const geometry = new THREE.BoxGeometry(cubeSize, cubeSize, cubeSize);

                    // Create materials for each face
                    const materials = this.createCubieMaterials();

                    const cubie = new THREE.Mesh(geometry, materials);
                    cubie.position.set(
                        (x - 1) * spacing,
                        (y - 1) * spacing,
                        (z - 1) * spacing
                    );

                    cubie.castShadow = true;
                    cubie.receiveShadow = true;

                    // Store position for state mapping
                    cubie.userData = { gridPosition: [x, y, z] };

                    this.cubies.push(cubie);
                    this.cubeGroup.add(cubie);
                }
            }
        }
    }

    createCubieMaterials() {
        // Materials for each face: [+X, -X, +Y, -Y, +Z, -Z]
        // Three.js face order: [right, left, top, bottom, front, back]
        return [
            new THREE.MeshLambertMaterial({ color: 0x333333 }), // Right (+X)
            new THREE.MeshLambertMaterial({ color: 0x333333 }), // Left (-X)
            new THREE.MeshLambertMaterial({ color: 0x333333 }), // Top (+Y)
            new THREE.MeshLambertMaterial({ color: 0x333333 }), // Bottom (-Y)
            new THREE.MeshLambertMaterial({ color: 0x333333 }), // Front (+Z)
            new THREE.MeshLambertMaterial({ color: 0x333333 })  // Back (-Z)
        ];
    }

    getDefaultSolvedState() {
        // Return a solved cube state for initialization
        return {
            'U': Array(9).fill('WHITE'),   // Top face
            'D': Array(9).fill('YELLOW'),  // Bottom face
            'R': Array(9).fill('RED'),     // Right face
            'L': Array(9).fill('ORANGE'),  // Left face
            'F': Array(9).fill('GREEN'),   // Front face
            'B': Array(9).fill('BLUE')     // Back face
        };
    }

    updateCubeState(cubeState) {
        if (!cubeState || !cubeState.faces) {
            console.warn('Invalid cube state provided');
            return;
        }


        const faces = cubeState.faces;

        // Store the new state for future reference
        this.currentCubeState = cubeState;

        // Solution: Always rebuild cube with current state
        // This ensures colors are always correct and synchronized with server state
        this.rebuildCubeWithState(faces);

    }

    rebuildCubeWithState(faces) {

        // Clear existing cubies
        this.cubies.forEach(cubie => {
            this.cubeGroup.remove(cubie);
            if (cubie.geometry) cubie.geometry.dispose();
            if (Array.isArray(cubie.material)) {
                cubie.material.forEach(mat => mat.dispose());
            }
        });
        this.cubies = [];

        // Recreate all cubies with correct colors from the state
        for (let x = 0; x < 3; x++) {
            for (let y = 0; y < 3; y++) {
                for (let z = 0; z < 3; z++) {
                    const cubie = this.createCubieWithStateColors(x, y, z, faces);
                    this.cubeGroup.add(cubie);
                    this.cubies.push(cubie);
                }
            }
        }
    }

    // Note: This function is no longer used, but kept for reference
    // The material update approach had issues with Three.js not reflecting changes
    // We now use rebuildCubeWithState() for all updates to ensure visual consistency
    updateCubieColorsOnly(faces) {
        this.rebuildCubeWithState(faces);
    }

    createCubieWithStateColors(x, y, z, faces) {
        const geometry = new THREE.BoxGeometry(0.95, 0.95, 0.95);

        // Create materials array with state-based colors
        const materials = [
            new THREE.MeshLambertMaterial({ color: 0x333333 }), // Right (+X)
            new THREE.MeshLambertMaterial({ color: 0x333333 }), // Left (-X)
            new THREE.MeshLambertMaterial({ color: 0x333333 }), // Top (+Y)
            new THREE.MeshLambertMaterial({ color: 0x333333 }), // Bottom (-Y)
            new THREE.MeshLambertMaterial({ color: 0x333333 }), // Front (+Z)
            new THREE.MeshLambertMaterial({ color: 0x333333 })  // Back (-Z)
        ];

        // SIMPLIFIED APPROACH: Use only the working U pattern and direct mappings
        // Working U formula: (2-z) * 3 + x

        // Apply colors ONLY to visible faces for each cubie position
        // This prevents coordinate mapping conflicts between faces

        if (x === 2) { // Right face - ONLY color the +X material
            // R face: correct mapping for viewing from outside
            const faceIndex = (2-y) * 3 + (2-z);
            if (faces.R && faces.R[faceIndex]) {
                materials[0].color.setHex(this.colors[faces.R[faceIndex]] || 0x333333);
            }
        }

        if (x === 0) { // Left face - ONLY color the -X material
            // L face: when looking from -X direction
            // [0,2,0] should map to index 0 (top-left), [0,0,2] to index 8
            const faceIndex = (2-y) * 3 + z;
            if (faces.L && faces.L[faceIndex]) {
                materials[1].color.setHex(this.colors[faces.L[faceIndex]] || 0x333333);
            }
        }

        if (y === 2) { // Top face - ONLY color the +Y material
            // U face: looking from above, top-left is [0,2,0], bottom-right is [2,2,2]
            // Standard face indexing: row-major order
            const faceIndex = z * 3 + x;
            if (faces.U && faces.U[faceIndex]) {
                materials[2].color.setHex(this.colors[faces.U[faceIndex]] || 0x333333);
            }
        }

        if (y === 0) { // Bottom face - ONLY color the -Y material
            // D face: when looking from -Y direction (below)
            // Need to invert z because we're looking from below
            const faceIndex = (2-z) * 3 + x;
            if (faces.D && faces.D[faceIndex]) {
                materials[3].color.setHex(this.colors[faces.D[faceIndex]] || 0x333333);
            }
        }

        if (z === 2) { // Front face - ONLY color the +Z material
            // F face: looking from front, top-left is [0,2,2], bottom-right is [2,0,2]
            const faceIndex = (2-y) * 3 + x;
            if (faces.F && faces.F[faceIndex]) {
                materials[4].color.setHex(this.colors[faces.F[faceIndex]] || 0x333333);
            }
        }

        if (z === 0) { // Back face - ONLY color the -Z material
            // B face: looking from back, top-left is [2,2,0], bottom-right is [0,0,0]
            const faceIndex = (2-y) * 3 + (2-x);
            if (faces.B && faces.B[faceIndex]) {
                materials[5].color.setHex(this.colors[faces.B[faceIndex]] || 0x333333);
            }
        }


        const cubie = new THREE.Mesh(geometry, materials);
        cubie.position.set(x - 1, y - 1, z - 1);

        // Store grid position for reference
        cubie.userData = { gridPosition: [x, y, z] };

        return cubie;
    }

    getFaceIndex(coord1, coord2) {
        // Convert 3D coordinates to face index (0-8)
        // Standard 3x3 grid layout: [0,1,2; 3,4,5; 6,7,8]
        // coord1 = row (0-2), coord2 = col (0-2)
        return coord1 * 3 + coord2;
    }

    animateMove(move, onComplete = null) {
        if (this.isAnimating) {
            this.animationQueue.push({move, onComplete});
            return;
        }

        this.isAnimating = true;

        // Store the completion callback
        this.currentAnimationCallback = onComplete;

        // Parse move notation
        const { face, clockwise, double } = this.parseMove(move);

        // Get cubies to rotate
        const cubiesToRotate = this.getCubiesForFace(face);

        // Create rotation group
        const rotationGroup = new THREE.Group();
        this.scene.add(rotationGroup);

        // Move cubies to rotation group
        cubiesToRotate.forEach(cubie => {
            this.cubeGroup.remove(cubie);
            rotationGroup.add(cubie);
        });

        // Determine rotation angle
        let angle = Math.PI / 2; // 90 degrees
        if (double) angle *= 2;
        if (!clockwise) angle *= -1;

        // Fix rotation directions for Three.js conventions
        // Three.js rotates counter-clockwise for positive angles
        // We need clockwise for standard Rubik's cube moves

        if (face === 'R') {
            angle *= -1; // Need negative for clockwise when viewed from +X
        }
        if (face === 'L') {
            // L needs positive angle (looking from -X, want clockwise)
        }
        if (face === 'U') {
            angle *= -1; // Need negative for clockwise when viewed from +Y
        }
        if (face === 'D') {
            // D needs positive angle (looking from -Y, want clockwise)
        }
        if (face === 'F') {
            angle *= -1; // Need negative for clockwise when viewed from +Z
        }
        if (face === 'B') {
            // B needs positive angle (looking from -Z, want clockwise)
        }

        // Get rotation axis
        const axis = this.getRotationAxis(face);

        // Animate rotation
        const startRotation = rotationGroup.rotation.clone();
        const targetRotation = startRotation.clone();
        targetRotation[axis] += angle;

        const startTime = Date.now();
        const duration = this.animationSpeed;

        const animateRotation = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function (ease-out)
            const easeProgress = 1 - Math.pow(1 - progress, 3);

            rotationGroup.rotation[axis] = startRotation[axis] +
                (targetRotation[axis] - startRotation[axis]) * easeProgress;

            if (progress < 1) {
                requestAnimationFrame(animateRotation);
            } else {
                // Animation complete - move cubies back to main group
                cubiesToRotate.forEach(cubie => {
                    rotationGroup.remove(cubie);
                    this.cubeGroup.add(cubie);
                });

                this.scene.remove(rotationGroup);
                this.isAnimating = false;

                // Call completion callback if provided
                if (this.currentAnimationCallback) {
                    this.currentAnimationCallback();
                    this.currentAnimationCallback = null;
                }

                // Process next animation in queue
                if (this.animationQueue.length > 0) {
                    const nextItem = this.animationQueue.shift();
                    const nextMove = typeof nextItem === 'string' ? nextItem : nextItem.move;
                    const nextCallback = typeof nextItem === 'string' ? null : nextItem.onComplete;
                    setTimeout(() => this.animateMove(nextMove, nextCallback), 50);
                }
            }
        };

        animateRotation();
    }

    parseMove(move) {
        const face = move.charAt(0).toUpperCase();
        const modifiers = move.slice(1);

        return {
            face: face,
            clockwise: !modifiers.includes("'"),
            double: modifiers.includes('2')
        };
    }

    getCubiesForFace(face) {
        // Return cubies that belong to the specified face
        return this.cubies.filter(cubie => {
            const [x, y, z] = cubie.userData.gridPosition;

            switch (face) {
                case 'R': return x === 2;
                case 'L': return x === 0;
                case 'U': return y === 2;
                case 'D': return y === 0;
                case 'F': return z === 2;
                case 'B': return z === 0;
                default: return false;
            }
        });
    }

    getRotationAxis(face) {
        switch (face) {
            case 'R':
            case 'L':
                return 'x';
            case 'U':
            case 'D':
                return 'y';
            case 'F':
            case 'B':
                return 'z';
            default:
                return 'y';
        }
    }

    // Animation and render loop
    animate() {
        requestAnimationFrame(() => this.animate());

        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    handleResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();

        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    }

    // Public methods for external control
    setAnimationSpeed(speed) {
        this.animationSpeed = speed;
    }

    resetCamera() {
        this.camera.position.set(-3.5, 3.5, -3.5);
        this.camera.lookAt(0, 0, 0);
        this.controls.target.set(0, 0, 0);
        this.controls.reset();
    }

    toggleAutoRotate() {
        this.controls.autoRotate = !this.controls.autoRotate;
        return this.controls.autoRotate;
    }

    setAutoRotate(enabled) {
        this.controls.autoRotate = enabled;
        return this.controls.autoRotate;
    }

    setAutoRotateSpeed(speed) {
        this.controls.autoRotateSpeed = speed;
        return speed;
    }

    toggleInteractionMode() {
        const previousMode = this.interactionMode;
        this.interactionMode = this.interactionMode === 'view' ? 'cube' : 'view';

        console.log('🔄 MODE TOGGLE:', previousMode, '→', this.interactionMode);

        if (this.interactionMode === 'cube') {
            // In cube mode, keep controls enabled but make them lower priority
            // We'll manually check for cube hits and let controls handle non-cube interactions
            this.controls.enabled = true;
            this.enableFaceInteraction();
            console.log('🎯 Switched to CUBE mode - controls enabled (fallback), face interaction enabled');
        } else {
            this.controls.enabled = true; // Enable camera controls
            this.disableFaceInteraction();
            console.log('👁️ Switched to VIEW mode - controls enabled, face interaction disabled');
        }

        console.log('📊 Controls enabled status:', this.controls.enabled, '| Event listeners:', this.renderer.domElement.onclick ? 'ATTACHED' : 'NOT ATTACHED');
        return this.interactionMode;
    }

    enableFaceInteraction() {
        // Add click detection for cube faces
        this.renderer.domElement.addEventListener('click', this.boundHandleFaceClick);
        this.renderer.domElement.addEventListener('contextmenu', this.boundHandleFaceClick);
        // Add touch support for mobile
        this.renderer.domElement.addEventListener('touchend', this.boundHandleFaceClick);
        this.renderer.domElement.style.cursor = 'pointer';
    }

    disableFaceInteraction() {
        // Remove click detection
        this.renderer.domElement.removeEventListener('click', this.boundHandleFaceClick);
        this.renderer.domElement.removeEventListener('contextmenu', this.boundHandleFaceClick);
        this.renderer.domElement.removeEventListener('touchend', this.boundHandleFaceClick);
        this.renderer.domElement.style.cursor = 'grab';
    }

    handleFaceClick(event) {
        if (this.interactionMode !== 'cube') {
            return;
        }

        // Check if OrbitControls was dragging
        if (this.isDragging) {
            this.isDragging = false; // Reset for next interaction
            return;
        }

        // Calculate mouse/touch position in normalized device coordinates
        const rect = this.renderer.domElement.getBoundingClientRect();
        const mouse = new THREE.Vector2();

        // Handle touch events
        if (event.type === 'touchend') {
            // Use the last touch position from changedTouches
            const touch = event.changedTouches[0];
            mouse.x = ((touch.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((touch.clientY - rect.top) / rect.height) * 2 + 1;
        } else {
            // Handle mouse events
            mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        }
        // Cast ray from camera through mouse position
        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(mouse, this.camera);

        // Find intersected cubie
        const intersects = raycaster.intersectObjects(this.cubies, false);

        if (intersects.length > 0) {
            // We hit a cube! Prevent the event from reaching OrbitControls and execute move
            // Prevent context menu on right-click and stop propagation
            if (event.type === 'contextmenu') {
                event.preventDefault();
            }
            event.stopPropagation();

            const face = this.detectFaceFromIntersection(intersects[0]);

            if (face) {
                let move = face;

                // Handle different input types
                if (event.type === 'touchend') {
                    // Mobile: delay execution to detect double-tap
                    const touch = event.changedTouches[0];
                    const currentTime = Date.now();
                    const timeDiff = currentTime - this.lastTapTime;
                    const positionDiff = Math.abs(touch.clientX - this.lastTapPosition.x) +
                                        Math.abs(touch.clientY - this.lastTapPosition.y);

                    // Check if this is a double-tap (within time and position threshold)
                    if (timeDiff < this.doubleTapDelay && positionDiff < 30 && this.lastTapFace === face) {
                        // Double-tap detected! Cancel the pending single tap and execute counter-clockwise
                        if (this.tapTimeout) {
                            clearTimeout(this.tapTimeout);
                            this.tapTimeout = null;
                        }
                        move += "'";  // Counter-clockwise on double-tap
                        this.rotateFace(move);
                        this.lastTapTime = 0; // Reset to prevent triple-tap
                        this.lastTapFace = null;
                    } else {
                        // Potential first tap - delay execution to see if second tap comes
                        this.lastTapTime = currentTime;
                        this.lastTapPosition = { x: touch.clientX, y: touch.clientY };
                        this.lastTapFace = face;

                        // Clear any existing timeout
                        if (this.tapTimeout) {
                            clearTimeout(this.tapTimeout);
                        }

                        // Set timeout to execute single tap if no second tap comes
                        this.tapTimeout = setTimeout(() => {
                            this.rotateFace(move); // Clockwise on single tap
                            this.tapTimeout = null;
                        }, this.doubleTapDelay);
                    }
                    return; // Don't execute immediately for touch events
                } else if (event.type === 'contextmenu') {
                    // Right-click (contextmenu) = counter-clockwise (prime)
                    move += "'";
                } else if (event.ctrlKey || event.metaKey) {
                    // Ctrl/Cmd + click = double rotation
                    move += "2";
                }
                // Default left-click is clockwise (just the face letter)

                // Execute immediately for non-touch events
                this.rotateFace(move);
            }
        }
    }

    detectFaceFromIntersection(intersection) {
        // Determine which face was clicked based on the intersection normal
        const normal = intersection.face.normal.clone();
        normal.transformDirection(intersection.object.matrixWorld);

        // Map normals to face names
        const faces = {
            'R': new THREE.Vector3(1, 0, 0),   // Right
            'L': new THREE.Vector3(-1, 0, 0),  // Left
            'U': new THREE.Vector3(0, 1, 0),   // Up
            'D': new THREE.Vector3(0, -1, 0),  // Down
            'F': new THREE.Vector3(0, 0, 1),   // Front
            'B': new THREE.Vector3(0, 0, -1)   // Back
        };

        let closestFace = null;
        let maxDot = -1;

        for (const [faceName, faceNormal] of Object.entries(faces)) {
            const dot = normal.dot(faceNormal);
            if (dot > maxDot) {
                maxDot = dot;
                closestFace = faceName;
            }
        }

        return maxDot > 0.5 ? closestFace : null; // Threshold for face detection
    }

    rotateFace(face) {
        // Execute face rotation through the socket or API
        console.log(`Rotating face: ${face}`);

        // Send move to backend
        if (window.socketClient) {
            window.socketClient.executeMove({ move: face });
        } else if (window.uiControls) {
            window.uiControls.executeMoveViaAPI(face);
        }
    }

    showMoveSelectionPopup(x, y, faceName) {
        console.log('🎯 SHOWING MOVE SELECTION POPUP for face:', faceName, 'at position:', x, y);

        const popup = document.getElementById('move-selection-popup');
        const title = popup.querySelector('.move-selection-title');
        const buttons = popup.querySelectorAll('.move-selection-btn');

        if (!popup) {
            console.error('❌ Move selection popup element not found!');
            return;
        }

        // Set title
        title.textContent = `${faceName} Face`;

        // Calculate safe position within viewport
        const popupWidth = 150; // from CSS min-width
        const popupHeight = 100; // estimated height
        const margin = 20;

        // Get viewport dimensions
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        // Calculate position, keeping within viewport bounds
        let left = x + 10;
        let top = y - 50;

        // Adjust if popup would go off-screen
        if (left + popupWidth > viewportWidth - margin) {
            left = x - popupWidth - 10; // Show to left of click
        }
        if (top < margin) {
            top = margin; // Move down from top edge
        }
        if (top + popupHeight > viewportHeight - margin) {
            top = y - popupHeight - 10; // Show above click
        }

        // Position popup
        popup.style.left = `${Math.max(margin, left)}px`;
        popup.style.top = `${Math.max(margin, top)}px`;

        // Set up button handlers
        buttons.forEach(btn => {
            btn.onclick = () => {
                const moveType = btn.dataset.moveType;
                let move = faceName;

                if (moveType === 'counter') {
                    move += "'";
                } else if (moveType === 'double') {
                    move += "2";
                }
                // clockwise is just the face name

                this.rotateFace(move);
                this.hideMoveSelectionPopup();
            };
        });

        // Show popup
        popup.classList.add('visible');
        console.log('✅ POPUP SHOULD NOW BE VISIBLE - Position:', popup.style.left, popup.style.top);

        // Add click-outside handler
        const clickOutsideHandler = (event) => {
            if (!popup.contains(event.target)) {
                this.hideMoveSelectionPopup();
                document.removeEventListener('click', clickOutsideHandler);
            }
        };
        setTimeout(() => {
            document.addEventListener('click', clickOutsideHandler);
        }, 100);

        // Auto-hide after 3 seconds
        setTimeout(() => {
            this.hideMoveSelectionPopup();
            document.removeEventListener('click', clickOutsideHandler);
        }, 3000);
    }

    hideMoveSelectionPopup() {
        const popup = document.getElementById('move-selection-popup');
        popup.classList.remove('visible');
    }

    dispose() {
        // Clean up resources
        this.renderer.dispose();
        this.controls.dispose();

        // Dispose geometries and materials
        this.scene.traverse(object => {
            if (object.geometry) object.geometry.dispose();
            if (object.material) {
                if (Array.isArray(object.material)) {
                    object.material.forEach(material => material.dispose());
                } else {
                    object.material.dispose();
                }
            }
        });
    }
}

// Export for use in other modules
window.Cube3D = Cube3D;