/**
 * Move Log Manager
 * Handles the move history log panel in the UI
 */

class MoveLog {
    constructor() {
        this.panel = document.querySelector('.move-log-panel');
        this.logContent = document.getElementById('log-content');
        this.clearBtn = document.getElementById('clear-log-btn');
        this.toggleBtn = document.getElementById('toggle-log-btn');
        this.logHeader = document.querySelector('.log-header');
        this.maxEntries = 100;
        this.moveHistory = [];
        this.isCollapsed = false;

        // Dragging state
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;
        this.panelStartX = 0;
        this.panelStartY = 0;

        this.init();
    }

    init() {
        // Bind clear button
        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => this.clear());
        }

        // Bind toggle button
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => this.toggle());
        }

        // Make panel draggable by the header
        if (this.logHeader) {
            this.logHeader.style.cursor = 'move';
            this.logHeader.addEventListener('mousedown', (e) => this.startDrag(e));
            document.addEventListener('mousemove', (e) => this.drag(e));
            document.addEventListener('mouseup', () => this.stopDrag());
        }
    }

    /**
     * Toggle collapsed state
     */
    toggle() {
        this.isCollapsed = !this.isCollapsed;

        if (this.isCollapsed) {
            this.logContent.style.display = 'none';
            this.panel.style.height = 'auto';
            this.toggleBtn.innerHTML = '▲';
            this.toggleBtn.title = 'Expand log';
        } else {
            this.logContent.style.display = 'block';
            this.panel.style.height = '250px';
            this.toggleBtn.innerHTML = '▼';
            this.toggleBtn.title = 'Collapse log';
        }
    }

    /**
     * Start dragging the panel
     */
    startDrag(e) {
        // Only drag if clicking directly on header, not buttons
        if (e.target.tagName === 'BUTTON') return;

        this.isDragging = true;
        this.dragStartX = e.clientX;
        this.dragStartY = e.clientY;

        // Get current position
        const rect = this.panel.getBoundingClientRect();
        this.panelStartX = rect.left;
        this.panelStartY = rect.top;

        // Change to absolute positioning if not already
        this.panel.style.position = 'fixed';
        this.panel.style.left = `${this.panelStartX}px`;
        this.panel.style.top = `${this.panelStartY}px`;
        this.panel.style.bottom = 'auto';

        this.logHeader.style.cursor = 'grabbing';
        e.preventDefault();
    }

    /**
     * Drag the panel
     */
    drag(e) {
        if (!this.isDragging) return;

        const deltaX = e.clientX - this.dragStartX;
        const deltaY = e.clientY - this.dragStartY;

        const newX = this.panelStartX + deltaX;
        const newY = this.panelStartY + deltaY;

        // Keep panel within viewport bounds
        const maxX = window.innerWidth - this.panel.offsetWidth;
        const maxY = window.innerHeight - this.panel.offsetHeight;

        const clampedX = Math.max(0, Math.min(newX, maxX));
        const clampedY = Math.max(0, Math.min(newY, maxY));

        this.panel.style.left = `${clampedX}px`;
        this.panel.style.top = `${clampedY}px`;
    }

    /**
     * Stop dragging the panel
     */
    stopDrag() {
        if (this.isDragging) {
            this.isDragging = false;
            this.logHeader.style.cursor = 'move';
        }
    }

    /**
     * Add an entry to the log
     * @param {string} message - The message to log
     * @param {string} type - Type of entry (move, scramble, solve, reset, error)
     * @param {Object} details - Additional details
     */
    addEntry(message, type = 'info', details = {}) {
        const timestamp = new Date().toLocaleTimeString();
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;

        // Format message based on type
        let formattedMessage = `[${timestamp}] `;

        switch(type) {
            case 'move':
                formattedMessage += `Move: <span class="move-notation">${message}</span>`;
                this.moveHistory.push(message);
                break;
            case 'scramble':
                formattedMessage += `🎲 Scrambled with ${details.count || 'unknown'} moves`;
                if (details.moves) {
                    formattedMessage += `<br>→ ${details.moves.join(' ')}`;
                }
                break;
            case 'solve':
                formattedMessage += `🧠 ${message}`;
                if (details.solution) {
                    formattedMessage += `<br>→ Solution: ${details.solution.join(' ')}`;
                }
                break;
            case 'reset':
                formattedMessage += `🔄 ${message}`;
                this.moveHistory = [];
                break;
            case 'error':
                formattedMessage += `❌ ${message}`;
                break;
            default:
                formattedMessage += message;
        }

        entry.innerHTML = formattedMessage;

        // Add to log
        this.logContent.appendChild(entry);

        // Limit entries
        while (this.logContent.children.length > this.maxEntries) {
            this.logContent.removeChild(this.logContent.firstChild);
        }

        // Scroll to bottom
        this.logContent.scrollTop = this.logContent.scrollHeight;
    }

    /**
     * Log a move execution
     */
    logMove(move) {
        this.addEntry(move, 'move');
    }

    /**
     * Log a scramble operation
     */
    logScramble(moves) {
        // Create spoiler text for scramble moves
        const scrambleText = moves.join(' ');
        const spoilerHtml = `<span class="scramble-spoiler" title="Click to reveal">[Click to reveal scramble]</span><span class="scramble-revealed" style="display: none;">${scrambleText}</span>`;

        this.addEntry(`Cube scrambled (${moves.length} moves) ${spoilerHtml}`, 'scramble', {
            count: moves.length,
            isScramble: true
        });

        // Add click handler to the last entry
        setTimeout(() => {
            const lastEntry = this.logContent.lastElementChild;
            if (lastEntry) {
                const spoiler = lastEntry.querySelector('.scramble-spoiler');
                const revealed = lastEntry.querySelector('.scramble-revealed');
                if (spoiler && revealed) {
                    spoiler.style.cursor = 'pointer';
                    spoiler.style.textDecoration = 'underline';
                    spoiler.addEventListener('click', () => {
                        spoiler.style.display = 'none';
                        revealed.style.display = 'inline';
                    });
                }
            }
        }, 50);
    }

    /**
     * Log a solve operation
     */
    logSolve(algorithm, solution) {
        if (solution && solution.length > 0) {
            this.addEntry(`Solved using ${algorithm} (${solution.length} moves)`, 'solve', {
                solution: solution.slice(0, 10) // Show first 10 moves
            });
        } else {
            this.addEntry(`Solving with ${algorithm}...`, 'solve');
        }
    }

    /**
     * Log solve progress
     */
    logSolveStep(step, current, total) {
        this.addEntry(`Step ${current}/${total}: ${step}`, 'solve');
    }

    /**
     * Log a reset operation
     */
    logReset() {
        this.addEntry('Cube reset to solved state', 'reset');
    }

    /**
     * Log an error
     */
    logError(message) {
        this.addEntry(message, 'error');
    }

    /**
     * Clear the log
     */
    clear() {
        this.logContent.innerHTML = '<div class="log-entry">Log cleared. Ready for new moves...</div>';
        this.moveHistory = [];
    }

    /**
     * Get the move history
     */
    getHistory() {
        return this.moveHistory;
    }
}

// Initialize move log when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.moveLog = new MoveLog();
});