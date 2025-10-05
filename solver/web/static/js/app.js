/**
 * Main Application Module
 *
 * Orchestrates the entire web application, initializing all components
 * and managing the application lifecycle.
 */

class RubiksCubeApp {
    constructor() {
        this.isInitialized = false;
        this.loadingScreen = null;
        this.cube3d = null;
        this.uiControls = null;
        this.socketClient = null;

        this.init();
    }

    async init() {
        try {
            console.log('Initializing Rubik\'s Cube App...');

            this.showLoadingScreen();

            // Wait for all dependencies to be ready
            await this.waitForDependencies();

            // Initialize components in order
            await this.initializeComponents();

            // Set up global error handling
            this.setupErrorHandling();

            // Hide loading screen
            this.hideLoadingScreen();

            this.isInitialized = true;
            console.log('✅ Rubik\'s Cube App initialized successfully!');

        } catch (error) {
            console.error('❌ Failed to initialize app:', error);
            this.showInitializationError(error);
        }
    }

    showLoadingScreen() {
        this.loadingScreen = document.getElementById('loading-screen');
        if (this.loadingScreen) {
            this.loadingScreen.style.display = 'flex';
        }
    }

    hideLoadingScreen() {
        if (this.loadingScreen) {
            // Fade out animation
            this.loadingScreen.style.transition = 'opacity 0.5s ease-out';
            this.loadingScreen.style.opacity = '0';

            setTimeout(() => {
                this.loadingScreen.style.display = 'none';
            }, 500);
        }
    }

    async waitForDependencies() {
        // Check for required dependencies
        const requiredGlobals = ['THREE', 'io'];
        const optionalGlobals = ['Cube3D', 'UIControls', 'SocketClient'];

        // Wait for required external libraries
        for (const global of requiredGlobals) {
            await this.waitForGlobal(global, 5000);
        }

        // Wait for our own modules (they should load quickly)
        for (const global of optionalGlobals) {
            await this.waitForGlobal(global, 2000, false);
        }

        console.log('✅ All dependencies loaded');
    }

    waitForGlobal(globalName, timeout = 5000, required = true) {
        return new Promise((resolve, reject) => {
            if (window[globalName]) {
                resolve(window[globalName]);
                return;
            }

            const checkInterval = 100;
            let elapsed = 0;

            const checker = setInterval(() => {
                if (window[globalName]) {
                    clearInterval(checker);
                    resolve(window[globalName]);
                } else if (elapsed >= timeout) {
                    clearInterval(checker);
                    const message = `${globalName} not available after ${timeout}ms`;

                    if (required) {
                        reject(new Error(message));
                    } else {
                        console.warn(`⚠️ ${message} - continuing without it`);
                        resolve(null);
                    }
                }
                elapsed += checkInterval;
            }, checkInterval);
        });
    }

    async initializeComponents() {
        // Initialize 3D cube visualization
        if (window.Cube3D) {
            console.log('🎮 Initializing 3D cube...');
            this.cube3d = new window.Cube3D('cube-container');
            window.cube3d = this.cube3d; // Make globally accessible
        } else {
            console.warn('⚠️ Cube3D not available - 3D visualization disabled');
        }

        // UI Controls should already be initialized by DOMContentLoaded
        if (window.uiControls) {
            this.uiControls = window.uiControls;
            console.log('🎛️ UI Controls ready');
        } else {
            console.warn('⚠️ UI Controls not available');
        }

        // Socket client should already be initialized
        if (window.socketClient) {
            this.socketClient = window.socketClient;
            console.log('🔌 Socket client ready');
        } else {
            console.warn('⚠️ Socket client not available - using REST API only');
        }

        // Set up component interactions
        this.setupComponentInteractions();
    }

    setupComponentInteractions() {
        // Sync 3D cube with UI state
        if (this.cube3d && this.uiControls) {
            // Any additional cross-component setup can go here
            console.log('🔗 Component interactions configured');
        }
    }

    setupErrorHandling() {
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);

            if (this.uiControls) {
                this.uiControls.showToast(
                    'An unexpected error occurred',
                    'error'
                );
            }
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);

            if (this.uiControls) {
                this.uiControls.showToast(
                    'A network or processing error occurred',
                    'error'
                );
            }

            // Prevent the default behavior (console error)
            event.preventDefault();
        });

        console.log('🛡️ Error handling configured');
    }

    showInitializationError(error) {
        // Hide loading screen
        if (this.loadingScreen) {
            this.loadingScreen.style.display = 'none';
        }

        // Show error message
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: linear-gradient(135deg, #dc2626, #991b1b);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: system-ui, sans-serif;
            z-index: 10000;
        `;

        errorDiv.innerHTML = `
            <div style="text-align: center; max-width: 500px; padding: 2rem;">
                <h1 style="font-size: 2rem; margin-bottom: 1rem;">⚠️ Initialization Failed</h1>
                <p style="margin-bottom: 1rem; opacity: 0.9;">
                    The application failed to load properly. This might be due to:
                </p>
                <ul style="text-align: left; margin-bottom: 2rem; opacity: 0.8;">
                    <li>Network connectivity issues</li>
                    <li>Browser compatibility problems</li>
                    <li>Missing required resources</li>
                </ul>
                <button onclick="location.reload()" style="
                    background: white;
                    color: #dc2626;
                    border: none;
                    padding: 0.75rem 1.5rem;
                    border-radius: 0.5rem;
                    font-weight: 600;
                    cursor: pointer;
                    font-size: 1rem;
                ">
                    Reload Page
                </button>
                <details style="margin-top: 2rem; opacity: 0.7;">
                    <summary style="cursor: pointer;">Technical Details</summary>
                    <pre style="margin-top: 1rem; font-size: 0.8rem; text-align: left;">${error.message}</pre>
                </details>
            </div>
        `;

        document.body.appendChild(errorDiv);
    }

    // Public API

    getStatus() {
        return {
            initialized: this.isInitialized,
            components: {
                cube3d: !!this.cube3d,
                uiControls: !!this.uiControls,
                socketClient: !!this.socketClient
            },
            connection: this.socketClient ? this.socketClient.getConnectionStatus() : null
        };
    }

    restart() {
        console.log('🔄 Restarting application...');

        // Clean up existing components
        if (this.cube3d && typeof this.cube3d.dispose === 'function') {
            this.cube3d.dispose();
        }

        if (this.socketClient && typeof this.socketClient.disconnect === 'function') {
            this.socketClient.disconnect();
        }

        // Reload the page for a fresh start
        setTimeout(() => {
            location.reload();
        }, 500);
    }

    // Performance and debugging utilities

    getPerformanceInfo() {
        if (!performance || !performance.timing) {
            return null;
        }

        const timing = performance.timing;
        const navigationStart = timing.navigationStart;

        return {
            pageLoad: timing.loadEventEnd - navigationStart,
            domReady: timing.domContentLoadedEventEnd - navigationStart,
            firstByte: timing.responseStart - navigationStart,
            memory: performance.memory ? {
                used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
                limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
            } : null
        };
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.rubiksCubeApp = new RubiksCubeApp();
});

// Development helpers (only in development mode)
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // Expose debugging utilities
    window.debugCube = {
        getStatus: () => window.rubiksCubeApp?.getStatus(),
        getPerf: () => window.rubiksCubeApp?.getPerformanceInfo(),
        restart: () => window.rubiksCubeApp?.restart(),

        // Component access
        get cube3d() { return window.cube3d; },
        get ui() { return window.uiControls; },
        get socket() { return window.socketClient; },

        // Quick actions
        scramble: (moves = 20) => window.socketClient?.scramble({ moves }),
        solve: () => window.socketClient?.solve({ algorithm: 'auto' }),
        reset: () => window.socketClient?.reset(),
        move: (move) => window.socketClient?.executeMove({ move })
    };

    console.log('🔧 Debug utilities available at window.debugCube');
}

// Export for external use
window.RubiksCubeApp = RubiksCubeApp;