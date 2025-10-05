/**
 * WebSocket Client Module
 *
 * Handles real-time communication between the browser and Flask-SocketIO server
 * for live cube state synchronization and move animations.
 */

class SocketClient {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second

        this.init();
    }

    init() {
        this.connect();
        console.log('SocketClient initialized');
    }

    connect() {
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: false
            });

            this.bindEvents();
        } catch (error) {
            console.error('Failed to initialize socket connection:', error);
            this.handleConnectionError();
        }
    }

    bindEvents() {
        // Connection events
        this.socket.on('connect', () => this.handleConnect());
        this.socket.on('disconnect', (reason) => this.handleDisconnect(reason));
        this.socket.on('connect_error', (error) => this.handleConnectionError(error));

        // Cube events
        this.socket.on('session_created', (data) => this.handleSessionCreated(data));
        this.socket.on('move_executed', (data) => this.handleMoveExecuted(data));
        this.socket.on('cube_scrambled', (data) => this.handleCubeScrambled(data));
        this.socket.on('cube_reset', (data) => this.handleCubeReset(data));
        this.socket.on('scrambled_state_restored', (data) => this.handleScrambledStateRestored(data));

        // Solver events
        this.socket.on('solve_started', (data) => this.handleSolveStarted(data));
        this.socket.on('solve_step', (data) => this.handleSolveStep(data));
        this.socket.on('solve_completed', (data) => this.handleSolveCompleted(data));
        this.socket.on('solve_result', (data) => this.handleSolveResult(data));

        // Error handling
        this.socket.on('error', (data) => this.handleError(data));
    }

    // Connection Management

    handleConnect() {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;

        console.log('WebSocket connected successfully');

        if (window.uiControls) {
            window.uiControls.showToast('Connected to server', 'success');
        }
    }

    handleDisconnect(reason) {
        this.isConnected = false;

        console.log('WebSocket disconnected:', reason);

        if (window.uiControls) {
            window.uiControls.showToast('Disconnected from server', 'warning');
        }

        // Attempt to reconnect for certain disconnect reasons
        if (reason === 'io server disconnect') {
            // Server initiated disconnect - don't reconnect automatically
            return;
        }

        this.attemptReconnect();
    }

    handleConnectionError(error) {
        console.error('WebSocket connection error:', error);

        if (window.uiControls) {
            window.uiControls.showToast('Connection error - using fallback mode', 'error');
        }

        if (!this.isConnected) {
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            if (window.uiControls) {
                window.uiControls.showToast('Connection failed - using offline mode', 'error');
            }
            return;
        }

        this.reconnectAttempts++;

        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

        setTimeout(() => {
            if (!this.isConnected) {
                this.socket.connect();
            }
        }, this.reconnectDelay);

        // Exponential backoff
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
    }

    // Event Handlers

    handleSessionCreated(data) {
        console.log('Session created:', data.session_id);

        // Update 3D cube with initial state
        if (window.cube3d && data.cube_state) {
            window.cube3d.updateCubeState(data.cube_state);
        }

        // Update UI
        if (window.uiControls) {
            window.uiControls.updateCubeStatus(data.is_solved ? 'solved' : 'scrambled');
            window.uiControls.updateMoveCounter(data.move_history ? data.move_history.length : 0);
        }
    }

    handleMoveExecuted(data) {
        if (data.success) {
            console.log('Move executed:', data.move);

            // Log the move
            if (window.moveLog) {
                window.moveLog.logMove(data.move);
            }

            // Fixed approach: animate first, then update colors via callback
            if (window.cube3d && data.cube_state) {
                // Show visual animation with current colors, update after completion
                window.cube3d.animateMove(data.move, () => {
                    // This callback runs exactly when animation finishes
                    window.cube3d.updateCubeState(data.cube_state);
                    console.log('🎨 Colors updated after animation completion');
                });
            }

            // Update UI status
            if (window.uiControls) {
                window.uiControls.updateCubeStatus(data.is_solved ? 'solved' : 'scrambled');
                window.uiControls.updateMoveCounter(data.move_history ? data.move_history.length : 0);

                if (data.is_solved) {
                    window.uiControls.showToast('🎉 Cube solved!', 'success');
                }
            }
        } else {
            console.error('Move execution failed:', data.error);

            // Log the error
            if (window.moveLog) {
                window.moveLog.logError(`Move failed: ${data.error || 'Unknown error'}`);
            }

            if (window.uiControls) {
                window.uiControls.showToast(data.error || 'Move execution failed', 'error');
            }
        }
    }

    handleCubeScrambled(data) {
        if (data.success) {
            console.log('Cube scrambled with moves:', data.scramble_moves);

            // Log the scramble
            if (window.moveLog && data.scramble_moves) {
                window.moveLog.logScramble(data.scramble_moves);
            }

            // Update 3D cube state
            if (window.cube3d && data.cube_state) {
                window.cube3d.updateCubeState(data.cube_state);
            }

            // Update UI
            if (window.uiControls) {
                window.uiControls.updateCubeStatus('scrambled');
                window.uiControls.showToast(`Cube scrambled with ${data.scramble_moves.length} moves`, 'success');
                window.uiControls.showRevealScrambleButton();  // Show reveal scramble button
                window.uiControls.enableControls();
            }
        } else {
            console.error('Scramble failed:', data.error);

            // Log the error
            if (window.moveLog) {
                window.moveLog.logError(`Scramble failed: ${data.error || 'Unknown error'}`);
            }

            if (window.uiControls) {
                window.uiControls.showToast(data.error || 'Scramble failed', 'error');
                window.uiControls.enableControls();
            }
        }
    }

    handleCubeReset(data) {
        if (data.success) {
            console.log('Cube reset to solved state');

            // Log the reset
            if (window.moveLog) {
                window.moveLog.logReset();
            }

            // Update 3D cube state
            if (window.cube3d && data.cube_state) {
                window.cube3d.updateCubeState(data.cube_state);
            }

            // Update UI
            if (window.uiControls) {
                window.uiControls.updateCubeStatus('solved');
                window.uiControls.updateMoveCounter(0);
                window.uiControls.hideSolution();
                window.uiControls.hideRevealScrambleButton();  // Hide reveal scramble button
                window.uiControls.showToast('Cube reset to solved state', 'success');
                window.uiControls.enableControls();
            }
        } else {
            console.error('Reset failed:', data.error);

            // Log the error
            if (window.moveLog) {
                window.moveLog.logError(`Reset failed: ${data.error || 'Unknown error'}`);
            }

            if (window.uiControls) {
                window.uiControls.showToast(data.error || 'Reset failed', 'error');
                window.uiControls.enableControls();
            }
        }
    }

    handleScrambledStateRestored(data) {
        if (data.success) {
            console.log('Scrambled state restored');

            // Update 3D cube state
            if (window.cube3d && data.cube_state) {
                window.cube3d.updateCubeState(data.cube_state);
            }

            // Update UI
            if (window.uiControls) {
                window.uiControls.updateCubeStatus('scrambled');
                window.uiControls.updateMoveCounter(data.move_history ? data.move_history.length : 0);
            }

            // Reset solution step highlighting
            const solutionSteps = document.querySelectorAll('.solution-step');
            solutionSteps.forEach(step => {
                step.classList.remove('active', 'completed');
            });

            // Log the restoration
            if (window.moveLog) {
                window.moveLog.addEntry('Restored to scrambled state', 'info');
            }
        } else {
            console.error('Restore failed:', data.error);

            if (window.uiControls) {
                window.uiControls.showToast(data.error || 'Failed to restore scrambled state', 'error');
            }

            // Log the error
            if (window.moveLog) {
                window.moveLog.logError(`Restore failed: ${data.error || 'Unknown error'}`);
            }
        }
    }

    handleSolveStarted(data) {
        console.log('Solve started:', data);

        // Log the solve start
        if (window.moveLog) {
            window.moveLog.logSolve(`${data.algorithm} algorithm`, null);
        }

        if (window.uiControls) {
            window.uiControls.updateCubeStatus('solving');
            window.uiControls.showToast(
                `Starting ${data.algorithm} solver (${data.total_moves} moves)`,
                'info'
            );
        }
    }

    handleSolveStep(data) {
        console.log(`Solve step ${data.step}/${data.total_steps}: ${data.move}`);

        // Log the solve step
        if (window.moveLog) {
            window.moveLog.logSolveStep(data.move, data.step, data.total_steps);
        }

        // Fixed: Use callback to ensure state updates after animation
        if (window.cube3d && data.cube_state) {
            // Show visual animation with callback for state update
            window.cube3d.animateMove(data.move, () => {
                // Update state only after animation completes
                window.cube3d.updateCubeState(data.cube_state);
                console.log(`Step ${data.step}/${data.total_steps} animation and state update complete`);
            });
        }

        // Update UI with progress
        if (window.uiControls) {
            window.uiControls.updateCubeStatus(
                data.is_solved ? 'solved' : 'solving'
            );

            // Highlight current step in solution display
            const solutionSteps = document.querySelectorAll('.solution-step');
            solutionSteps.forEach((step, index) => {
                step.classList.remove('active', 'completed');
                if (index < data.step - 1) {
                    step.classList.add('completed');
                } else if (index === data.step - 1) {
                    step.classList.add('active');
                }
            });
        }
    }

    handleSolveCompleted(data) {
        console.log('Solve completed successfully');

        // Log the completion
        if (window.moveLog) {
            window.moveLog.addEntry('Solve completed successfully!', 'solve');
        }

        if (window.uiControls) {
            window.uiControls.updateCubeStatus('solved');
            window.uiControls.showToast('🎉 Cube solved successfully!', 'success');
            // CRITICAL: Reset the solve button state
            window.uiControls.enableControls();

            // Mark all solution steps as completed
            const solutionSteps = document.querySelectorAll('.solution-step');
            solutionSteps.forEach(step => {
                step.classList.remove('active');
                step.classList.add('completed');
            });
        }
    }

    handleSolveResult(data) {
        if (data.success) {
            console.log('Solution found:', data.solution);

            // Log the solution
            if (window.moveLog) {
                window.moveLog.logSolve(data.algorithm_used, data.solution);
            }

            if (window.uiControls) {
                window.uiControls.displaySolution(data.solution);
                window.uiControls.showToast(
                    `Solution found: ${data.solution.length} moves (${data.algorithm_used})`,
                    'success'
                );
                // CRITICAL: Reset the solve button state
                window.uiControls.enableControls();
            }
        } else {
            console.error('Solve failed:', data.error);

            // Log the error
            if (window.moveLog) {
                window.moveLog.logError(`Solve failed: ${data.error || 'Unknown error'}`);
            }

            if (window.uiControls) {
                window.uiControls.showToast(data.error || 'Solve failed', 'error');
                window.uiControls.updateCubeStatus('scrambled');
                // CRITICAL: Reset the solve button state even on failure
                window.uiControls.enableControls();
            }
        }
    }

    handleError(data) {
        console.error('Server error:', data);

        // Log the error
        if (window.moveLog) {
            window.moveLog.logError(data.message || 'Server error occurred');
        }

        if (window.uiControls) {
            window.uiControls.showToast(data.message || 'Server error occurred', 'error');
        }
    }

    // Public API Methods

    executeMove(data) {
        if (this.isConnected) {
            this.socket.emit('execute_move', data);
        } else {
            console.warn('Not connected - using fallback API');
            if (window.uiControls) {
                window.uiControls.executeMoveViaAPI(data.move);
            }
        }
    }

    scramble(data) {
        if (this.isConnected) {
            this.socket.emit('scramble', data);
        } else {
            console.warn('Not connected - using fallback API');
            if (window.uiControls) {
                window.uiControls.scrambleViaAPI(data.moves);
            }
        }
    }

    solve(data) {
        if (this.isConnected) {
            this.socket.emit('solve', data);
        } else {
            console.warn('Not connected - using fallback API');
            if (window.uiControls) {
                window.uiControls.solveViaAPI(data.algorithm, data.max_depth);
            }
        }
    }

    reset() {
        if (this.isConnected) {
            this.socket.emit('reset');
        } else {
            console.warn('Not connected - using fallback API');
            if (window.uiControls) {
                window.uiControls.resetViaAPI();
            }
        }
    }

    restoreScrambled() {
        if (this.isConnected) {
            this.socket.emit('restore_scrambled');
        } else {
            console.warn('Not connected - restore scrambled not available via fallback');
        }
    }

    // Utility methods

    getConnectionStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            socketId: this.socket ? this.socket.id : null
        };
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// Initialize socket client when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if SocketIO is available
    if (typeof io !== 'undefined') {
        window.socketClient = new SocketClient();
    } else {
        console.warn('SocketIO not available - using REST API fallback');
    }
});

// Export for use in other modules
window.SocketClient = SocketClient;