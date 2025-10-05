/**
 * UI Controls Module
 *
 * Handles all user interface interactions, form controls, and visual feedback
 * for the Rubik's Cube web application.
 */

class UIControls {
    constructor() {
        this.elements = {};
        this.state = {
            isAdvancedOpen: false,
            moveHistory: [],
            isSolving: false,
            currentSolution: []
        };

        this.init();
    }

    init() {
        this.cacheElements();
        this.bindEvents();
        this.initializeControls();

        // Solution playback state
        this.solutionPlayback = {
            isPlaying: false,
            isPaused: false,
            currentStep: 0,
            intervalId: null
        };

        console.log('UI Controls initialized');
    }

    cacheElements() {
        // Quick actions
        this.elements.scrambleBtn = document.getElementById('scramble-btn');
        this.elements.revealScrambleBtn = document.getElementById('reveal-scramble-btn');
        this.elements.solveBtn = document.getElementById('solve-btn');
        this.elements.resetBtn = document.getElementById('reset-btn');

        // Scramble modal
        this.elements.scrambleModal = document.getElementById('scramble-modal');
        this.elements.closeScrambleModal = document.getElementById('close-scramble-modal');
        this.elements.scrambleSequenceText = document.getElementById('scramble-sequence-text');
        this.elements.copyScrambleBtn = document.getElementById('copy-scramble-btn');

        // Advanced controls
        this.elements.advancedToggle = document.getElementById('advanced-toggle');
        this.elements.advancedPanel = document.getElementById('advanced-panel');

        // Move input
        this.elements.moveInput = document.getElementById('move-input');
        this.elements.executeMoveBtn = document.getElementById('execute-move-btn');
        this.elements.moveBtns = document.querySelectorAll('.move-btn');

        // Solver options
        this.elements.algorithmSelect = document.getElementById('algorithm-select');
        this.elements.maxDepth = document.getElementById('max-depth');
        this.elements.depthValue = document.getElementById('depth-value');
        this.elements.stepByStep = document.getElementById('step-by-step');

        // Scramble options
        this.elements.scrambleMoves = document.getElementById('scramble-moves');
        this.elements.scrambleValue = document.getElementById('scramble-value');

        // Status elements
        this.elements.cubeState = document.getElementById('cube-state');
        this.elements.moveCounter = document.getElementById('move-counter');

        // Solution section
        this.elements.solutionSection = document.getElementById('solution-section');
        this.elements.solutionSteps = document.getElementById('solution-steps');
        this.elements.playSolution = document.getElementById('play-solution');
        this.elements.pauseSolution = document.getElementById('pause-solution');
        this.elements.stopSolution = document.getElementById('stop-solution');
        this.elements.restoreScrambledBtn = document.getElementById('restore-scrambled-btn');

        // Toast container
        this.elements.toastContainer = document.getElementById('toast-container');
    }

    bindEvents() {
        // Quick actions
        this.elements.scrambleBtn.addEventListener('click', () => this.handleScramble());
        this.elements.revealScrambleBtn.addEventListener('click', () => this.handleRevealScramble());
        this.elements.solveBtn.addEventListener('click', () => this.handleSolve());
        this.elements.resetBtn.addEventListener('click', () => this.handleReset());

        // Scramble modal
        this.elements.closeScrambleModal.addEventListener('click', () => this.closeScrambleModal());
        this.elements.scrambleModal.addEventListener('click', (e) => {
            if (e.target === this.elements.scrambleModal) this.closeScrambleModal();
        });
        this.elements.copyScrambleBtn.addEventListener('click', () => this.handleCopyScramble());

        // Advanced toggle
        this.elements.advancedToggle.addEventListener('click', () => this.toggleAdvanced());

        // Move input
        this.elements.moveInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleExecuteMove();
        });
        this.elements.executeMoveBtn.addEventListener('click', () => this.handleExecuteMove());

        // Move suggestion buttons
        this.elements.moveBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const move = btn.dataset.move;
                this.elements.moveInput.value = move;
                this.handleExecuteMove();
            });
        });

        // Range inputs
        this.elements.maxDepth.addEventListener('input', (e) => {
            this.elements.depthValue.textContent = e.target.value;
        });

        this.elements.scrambleMoves.addEventListener('input', (e) => {
            this.elements.scrambleValue.textContent = e.target.value;
        });

        // Solution controls
        this.elements.playSolution.addEventListener('click', () => this.handlePlaySolution());
        this.elements.pauseSolution.addEventListener('click', () => this.handlePauseSolution());
        this.elements.stopSolution.addEventListener('click', () => this.handleStopSolution());
        this.elements.restoreScrambledBtn.addEventListener('click', () => this.handleRestoreScrambled());

        // Cube rotation controls
        const interactionModeBtn = document.getElementById('interaction-mode-btn');
        const autoRotateBtn = document.getElementById('auto-rotate-btn');
        const resetCameraBtn = document.getElementById('reset-camera-btn');

        if (interactionModeBtn) {
            interactionModeBtn.addEventListener('click', () => this.handleInteractionModeToggle());
        }

        if (autoRotateBtn) {
            autoRotateBtn.addEventListener('click', () => this.handleAutoRotateToggle());
        }

        if (resetCameraBtn) {
            resetCameraBtn.addEventListener('click', () => this.handleCameraReset());
        }
    }

    initializeControls() {
        // Load available algorithms
        this.loadAlgorithms();

        // Set initial values
        this.updateMoveCounter(0);
        this.updateCubeStatus('solved');
    }

    async loadAlgorithms() {
        try {
            const response = await fetch('/api/algorithms');
            const data = await response.json();

            if (data.algorithms) {
                this.populateAlgorithmSelect(data.algorithms);
            }
        } catch (error) {
            console.error('Failed to load algorithms:', error);
            this.showToast('Failed to load solver algorithms', 'error');
        }
    }

    populateAlgorithmSelect(algorithms) {
        // Clear existing options except auto-select
        const autoOption = this.elements.algorithmSelect.querySelector('option[value="auto"]');
        this.elements.algorithmSelect.innerHTML = '';
        this.elements.algorithmSelect.appendChild(autoOption);

        // Add algorithm options
        algorithms.forEach(algo => {
            const option = document.createElement('option');
            option.value = algo.name;
            option.textContent = `${algo.name} - ${algo.description}`;
            option.title = `Max recommended depth: ${algo.max_recommended_depth}`;
            this.elements.algorithmSelect.appendChild(option);
        });
    }

    // Event Handlers

    handleScramble() {
        const moves = parseInt(this.elements.scrambleMoves.value) || 20;

        this.disableControls();
        this.showToast(`Scrambling cube with ${moves} moves...`, 'info');

        // Emit scramble event
        if (window.socketClient) {
            window.socketClient.scramble({ moves });
        } else {
            // Fallback to REST API
            this.scrambleViaAPI(moves);
        }
    }

    async scrambleViaAPI(moves) {
        try {
            const response = await fetch('/api/scramble', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ moves })
            });

            const result = await response.json();

            if (result.success) {
                this.showToast(`Cube scrambled with ${result.scramble_moves.length} moves`, 'success');
                this.updateCubeStatus('scrambled');
            } else {
                this.showToast(result.error || 'Scramble failed', 'error');
            }
        } catch (error) {
            console.error('Scramble error:', error);
            this.showToast('Network error during scramble', 'error');
        } finally {
            this.enableControls();
        }
    }

    async handleRevealScramble() {
        try {
            // Use the socket's session ID (request.sid from server)
            const sessionId = window.socketClient?.socket?.id || 'default';
            const response = await fetch('/api/scramble_sequence', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });

            const result = await response.json();

            if (result.scramble && result.scramble.length > 0) {
                this.elements.scrambleSequenceText.textContent = result.scramble_text;
                this.showScrambleModal();
            } else {
                this.showToast('No scramble sequence available', 'warning');
            }
        } catch (error) {
            console.error('Error fetching scramble sequence:', error);
            this.showToast('Failed to retrieve scramble sequence', 'error');
        }
    }

    showScrambleModal() {
        this.elements.scrambleModal.style.display = 'flex';
    }

    closeScrambleModal() {
        this.elements.scrambleModal.style.display = 'none';
    }

    async handleCopyScramble() {
        const scrambleText = this.elements.scrambleSequenceText.textContent;

        try {
            await navigator.clipboard.writeText(scrambleText);
            this.showToast('Scramble copied to clipboard!', 'success');
        } catch (error) {
            console.error('Failed to copy scramble:', error);
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = scrambleText;
            textArea.style.position = 'fixed';
            textArea.style.opacity = '0';
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                this.showToast('Scramble copied to clipboard!', 'success');
            } catch (err) {
                this.showToast('Failed to copy scramble', 'error');
            }
            document.body.removeChild(textArea);
        }
    }

    showRevealScrambleButton() {
        this.elements.revealScrambleBtn.style.display = 'inline-flex';
    }

    hideRevealScrambleButton() {
        this.elements.revealScrambleBtn.style.display = 'none';
    }

    handleSolve() {
        if (this.state.isSolving) {
            this.showToast('Solve already in progress', 'warning');
            return;
        }

        const algorithm = this.elements.algorithmSelect.value;
        const maxDepth = parseInt(this.elements.maxDepth.value);
        const stepByStep = this.elements.stepByStep.checked;

        this.state.isSolving = true;
        this.disableControls();
        this.updateCubeStatus('solving');
        this.showToast('Solving cube...', 'info');

        // Emit solve event
        if (window.socketClient) {
            window.socketClient.solve({
                algorithm,
                max_depth: maxDepth,
                step_by_step: stepByStep
            });
        } else {
            // Fallback to REST API
            this.solveViaAPI(algorithm, maxDepth);
        }
    }

    async solveViaAPI(algorithm, maxDepth) {
        try {
            const response = await fetch('/api/solve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ algorithm, max_depth: maxDepth })
            });

            const result = await response.json();

            if (result.success) {
                this.displaySolution(result.solution);
                this.showToast(`Solution found: ${result.solution.length} moves`, 'success');
            } else {
                this.showToast(result.error || 'Solve failed', 'error');
            }
        } catch (error) {
            console.error('Solve error:', error);
            this.showToast('Network error during solve', 'error');
        } finally {
            this.state.isSolving = false;
            this.enableControls();
        }
    }

    handleReset() {
        this.disableControls();
        this.showToast('Resetting cube...', 'info');

        // Clear solution display
        this.hideSolution();

        // Emit reset event
        if (window.socketClient) {
            window.socketClient.reset();
        } else {
            // Fallback to REST API
            this.resetViaAPI();
        }
    }

    async resetViaAPI() {
        try {
            const response = await fetch('/api/reset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });

            const result = await response.json();

            if (result.success) {
                this.showToast('Cube reset to solved state', 'success');
                this.updateCubeStatus('solved');
                this.updateMoveCounter(0);
            } else {
                this.showToast(result.error || 'Reset failed', 'error');
            }
        } catch (error) {
            console.error('Reset error:', error);
            this.showToast('Network error during reset', 'error');
        } finally {
            this.enableControls();
        }
    }

    handleExecuteMove() {
        const move = this.elements.moveInput.value.trim();
        if (!move) {
            this.showToast('Please enter a move', 'warning');
            return;
        }

        // Emit move event
        if (window.socketClient) {
            window.socketClient.executeMove({ move });
        } else {
            // Fallback to REST API
            this.executeMoveViaAPI(move);
        }

        // Clear input
        this.elements.moveInput.value = '';
    }

    async executeMoveViaAPI(move) {
        try {
            const response = await fetch('/api/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ move })
            });

            const result = await response.json();

            if (result.success) {
                this.showToast(`Executed: ${move}`, 'success');
                this.updateCubeStatus(result.is_solved ? 'solved' : 'scrambled');
            } else {
                this.showToast(result.error || 'Move failed', 'error');
            }
        } catch (error) {
            console.error('Move execution error:', error);
            this.showToast('Network error during move execution', 'error');
        }
    }

    toggleAdvanced() {
        this.state.isAdvancedOpen = !this.state.isAdvancedOpen;

        if (this.state.isAdvancedOpen) {
            this.elements.advancedPanel.classList.add('open');
            this.elements.advancedToggle.classList.add('active');
        } else {
            this.elements.advancedPanel.classList.remove('open');
            this.elements.advancedToggle.classList.remove('active');
        }
    }

    // Solution handling

    displaySolution(solution) {
        this.state.currentSolution = solution;

        if (!solution || solution.length === 0) {
            this.hideSolution();
            return;
        }

        // Clear existing steps
        this.elements.solutionSteps.innerHTML = '';

        // Add solution steps
        solution.forEach((move, index) => {
            const stepElement = document.createElement('div');
            stepElement.className = 'solution-step';
            stepElement.textContent = move;
            stepElement.dataset.index = index;

            stepElement.addEventListener('click', () => {
                this.executeSolutionStep(index);
            });

            this.elements.solutionSteps.appendChild(stepElement);
        });

        // Show solution section
        this.elements.solutionSection.classList.remove('hidden');
    }

    hideSolution() {
        this.elements.solutionSection.classList.add('hidden');
        this.state.currentSolution = [];
    }

    executeSolutionStep(index) {
        if (!this.state.currentSolution[index]) return;

        const move = this.state.currentSolution[index];

        // Highlight step
        const stepElements = this.elements.solutionSteps.querySelectorAll('.solution-step');
        stepElements.forEach(el => el.classList.remove('active'));
        stepElements[index].classList.add('active');

        // Execute move
        if (window.socketClient) {
            window.socketClient.executeMove({ move });
        }
    }

    handlePlaySolution() {
        if (!this.state.currentSolution || this.state.currentSolution.length === 0) {
            this.showToast('No solution to play', 'warning');
            return;
        }

        if (this.solutionPlayback.isPlaying) {
            // Resume if paused
            if (this.solutionPlayback.isPaused) {
                this.solutionPlayback.isPaused = false;
                this.showToast('Resuming solution playback', 'info');
                this.playSolutionStep();
            }
            return;
        }

        this.startSolutionPlayback();
    }

    handleRestoreScrambled() {
        if (window.socketClient) {
            this.showToast('Restoring to scrambled state...', 'info');
            window.socketClient.restoreScrambled();

            // Stop any current playback
            if (this.solutionPlayback.isPlaying) {
                this.handleStopSolution();
            }
        } else {
            this.showToast('Not connected to server', 'error');
        }
    }

    startSolutionPlayback() {
        // Start playback from beginning
        this.solutionPlayback.isPlaying = true;
        this.solutionPlayback.isPaused = false;
        this.solutionPlayback.currentStep = 0;
        this.showToast('Playing solution...', 'info');

        // Update button states
        this.elements.playSolution.disabled = true;
        this.elements.pauseSolution.disabled = false;
        this.elements.stopSolution.disabled = false;

        this.playSolutionStep();
    }

    playSolutionStep() {
        if (!this.solutionPlayback.isPlaying || this.solutionPlayback.isPaused) {
            return;
        }

        if (this.solutionPlayback.currentStep >= this.state.currentSolution.length) {
            // Solution complete - mark as completed but don't reset currentStep to 0
            this.solutionPlayback.isPlaying = false;
            this.solutionPlayback.isPaused = false;

            // Update button states
            this.elements.playSolution.disabled = false;
            this.elements.pauseSolution.disabled = true;
            this.elements.stopSolution.disabled = true;

            this.showToast('Solution playback complete!', 'success');
            return;
        }

        const move = this.state.currentSolution[this.solutionPlayback.currentStep];

        // Highlight current step
        const stepElements = this.elements.solutionSteps.querySelectorAll('.solution-step');
        stepElements.forEach((el, idx) => {
            el.classList.remove('active');
            if (idx < this.solutionPlayback.currentStep) {
                el.classList.add('completed');
            }
        });
        if (stepElements[this.solutionPlayback.currentStep]) {
            stepElements[this.solutionPlayback.currentStep].classList.add('active');
        }

        // Execute the move
        if (window.socketClient) {
            window.socketClient.executeMove({ move });
        }

        this.solutionPlayback.currentStep++;

        // Schedule next step (600ms matches animation duration + small gap)
        this.solutionPlayback.intervalId = setTimeout(() => {
            this.playSolutionStep();
        }, 600);
    }

    handlePauseSolution() {
        if (!this.solutionPlayback.isPlaying) {
            return;
        }

        this.solutionPlayback.isPaused = true;

        if (this.solutionPlayback.intervalId) {
            clearTimeout(this.solutionPlayback.intervalId);
            this.solutionPlayback.intervalId = null;
        }

        this.showToast('Solution playback paused', 'info');

        // Update button states
        this.elements.playSolution.disabled = false;
        this.elements.pauseSolution.disabled = true;
    }

    handleStopSolution() {
        this.solutionPlayback.isPlaying = false;
        this.solutionPlayback.isPaused = false;
        this.solutionPlayback.currentStep = 0;

        if (this.solutionPlayback.intervalId) {
            clearTimeout(this.solutionPlayback.intervalId);
            this.solutionPlayback.intervalId = null;
        }

        // Update button states
        this.elements.playSolution.disabled = false;
        this.elements.pauseSolution.disabled = true;
        this.elements.stopSolution.disabled = true;

        // Clear step highlighting
        const stepElements = this.elements.solutionSteps.querySelectorAll('.solution-step');
        stepElements.forEach(el => {
            el.classList.remove('active', 'completed');
        });
    }

    handleAutoRotateToggle() {
        if (window.cube3d && typeof window.cube3d.toggleAutoRotate === 'function') {
            const isRotating = window.cube3d.toggleAutoRotate();
            const autoRotateBtn = document.getElementById('auto-rotate-btn');

            if (autoRotateBtn) {
                if (isRotating) {
                    autoRotateBtn.classList.add('active');
                    this.showToast('Auto-rotation enabled', 'info');
                } else {
                    autoRotateBtn.classList.remove('active');
                    this.showToast('Auto-rotation disabled', 'info');
                }
            }
        } else {
            this.showToast('3D controls not available', 'warning');
        }
    }

    handleCameraReset() {
        if (window.cube3d && typeof window.cube3d.resetCamera === 'function') {
            window.cube3d.resetCamera();
            this.showToast('Camera view reset', 'success');
        } else {
            this.showToast('3D controls not available', 'warning');
        }
    }

    handleInteractionModeToggle() {
        if (window.cube3d && typeof window.cube3d.toggleInteractionMode === 'function') {
            const mode = window.cube3d.toggleInteractionMode();
            const interactionModeBtn = document.getElementById('interaction-mode-btn');

            if (interactionModeBtn) {
                const icon = interactionModeBtn.querySelector('.control-icon');
                if (mode === 'cube') {
                    interactionModeBtn.classList.add('active');
                    icon.textContent = '🎯'; // Target icon for cube mode
                    this.showToast('Cube Mode: Click faces to rotate', 'info');
                    this.updateTouchHint('Click face: Rotate • Drag background: Move camera • Middle-click: Back to View');
                } else {
                    interactionModeBtn.classList.remove('active');
                    icon.textContent = '👁️'; // Eye icon for view mode
                    this.showToast('View Mode: Drag to rotate camera', 'info');
                    this.updateTouchHint('Drag to rotate • Scroll to zoom • Right-click: Cube Mode');
                }
            }
        } else {
            this.showToast('3D controls not available', 'warning');
        }
    }

    updateTouchHint(text) {
        const touchHint = document.querySelector('.touch-hint p');
        if (touchHint) {
            touchHint.textContent = text;
        }
    }

    // UI State Management

    updateCubeStatus(status) {
        this.elements.cubeState.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        this.elements.cubeState.className = `status-badge status-${status}`;
    }

    updateMoveCounter(count) {
        this.elements.moveCounter.textContent = `${count} move${count !== 1 ? 's' : ''}`;
    }

    disableControls() {
        this.elements.scrambleBtn.disabled = true;
        this.elements.solveBtn.disabled = true;
        this.elements.resetBtn.disabled = true;
        this.elements.executeMoveBtn.disabled = true;
    }

    enableControls() {
        this.elements.scrambleBtn.disabled = false;
        this.elements.solveBtn.disabled = false;
        this.elements.resetBtn.disabled = false;
        this.elements.executeMoveBtn.disabled = false;
        // CRITICAL: Reset solving state
        this.state.isSolving = false;
    }

    // Toast Notifications

    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icon = this.getToastIcon(type);
        toast.innerHTML = `
            <span class="toast-icon">${icon}</span>
            <span class="toast-message">${message}</span>
        `;

        this.elements.toastContainer.appendChild(toast);

        // Auto remove after duration
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, duration);

        // Click to dismiss
        toast.addEventListener('click', () => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        });
    }

    getToastIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

}

// Initialize UI controls when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.uiControls = new UIControls();
});

// Export for use in other modules
window.UIControls = UIControls;