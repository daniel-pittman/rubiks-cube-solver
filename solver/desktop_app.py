"""
Rubik's Cube Desktop Application
Phase 5: Professional desktop interface using PySide6 and OpenGL
"""

# pylint: disable=broad-exception-caught,import-outside-toplevel,too-few-public-methods
# pylint: disable=too-many-instance-attributes

import copy
import logging
import sys

# pylint: disable=no-name-in-module
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from solver.core.cube import Cube
from solver.core.solver import CubeSolver
from solver.desktop.cube_gl_widget import CubeGLWidget

# pylint: enable=no-name-in-module


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SolverThread(QThread):
    """Background thread for running cube solver without blocking UI"""

    # Signals to communicate with main thread
    solution_found = Signal(list)  # Emits solution moves list
    solution_failed = Signal(str)  # Emits error message

    def __init__(self, cube, solver, algorithm, max_depth):
        super().__init__()
        self.cube = cube
        self.solver = solver
        self.algorithm = algorithm
        self.max_depth = max_depth

    def run(self):
        """Run solver in background thread"""
        try:
            logger.info(
                "Solver thread started: algorithm=%s, max_depth=%d",
                self.algorithm,
                self.max_depth,
            )
            solution = self.solver.solve(
                self.cube, algorithm=self.algorithm, max_depth=self.max_depth
            )

            if solution:
                logger.info("Solution found: %d moves", len(solution))
                self.solution_found.emit(solution)
            else:
                logger.warning("No solution found within depth limit")
                self.solution_failed.emit("No solution found within depth limit")
        except Exception as e:
            logger.error("Solver thread error: %s", e)
            self.solution_failed.emit(f"Solver error: {str(e)}")


class SolutionDialog(QDialog):
    """Dialog to display solution and control playback"""

    def __init__(self, solution, scrambled_state, parent=None):
        super().__init__(parent)
        self.solution = solution
        self.scrambled_state = scrambled_state  # Save scrambled cube state
        self.parent_app = parent
        self.current_step = 0
        self.is_playing = False
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.play_next_step)

        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Solution Found")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel(f"Solution: {len(self.solution)} moves")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Solution steps display
        steps_label = QLabel("Moves:")
        layout.addWidget(steps_label)

        self.steps_text = QTextEdit()
        self.steps_text.setReadOnly(True)
        self.steps_text.setMaximumHeight(100)
        self.steps_text.setText(" ".join(self.solution))
        layout.addWidget(self.steps_text)

        # Progress label
        self.progress_label = QLabel("Ready to play")
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)

        # Control buttons
        btn_layout = QHBoxLayout()

        self.play_btn = QPushButton("▶️ Play")
        self.play_btn.clicked.connect(self.start_playback)
        btn_layout.addWidget(self.play_btn)

        self.pause_btn = QPushButton("⏸️ Pause")
        self.pause_btn.clicked.connect(self.pause_playback)
        self.pause_btn.setEnabled(False)
        btn_layout.addWidget(self.pause_btn)

        self.reset_btn = QPushButton("🔄 Reset")
        self.reset_btn.clicked.connect(self.reset_playback)
        btn_layout.addWidget(self.reset_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def start_playback(self):
        """Start or resume solution playback"""
        if self.current_step >= len(self.solution):
            # Restart from beginning
            self.current_step = 0

        self.is_playing = True
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)

        # Get speed from parent's slider
        speed = self.parent_app.speed_slider.value()
        self.playback_timer.start(speed + 100)  # Slightly longer than animation

    def pause_playback(self):
        """Pause solution playback"""
        self.is_playing = False
        self.playback_timer.stop()
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.progress_label.setText(
            f"Paused at step {self.current_step + 1}/{len(self.solution)}"
        )

    def reset_playback(self):
        """Reset cube to scrambled state and playback to beginning"""
        self.pause_playback()

        # Restore scrambled cube state
        from solver.core.cube import Face

        for face_enum in Face:
            self.parent_app.cube.stickers[face_enum] = self.scrambled_state[
                face_enum
            ].copy()

        # Update display
        self.parent_app.cube_widget.update_cube_state(animate=False)
        self.parent_app.update_status()

        # Reset playback position
        self.current_step = 0
        self.progress_label.setText("Ready to play - Cube restored to scrambled state")

    def play_next_step(self):
        """Execute next move in solution"""
        if self.current_step < len(self.solution):
            move = self.solution[self.current_step]
            self.parent_app.execute_move(move)
            self.current_step += 1
            self.progress_label.setText(
                f"Step {self.current_step}/{len(self.solution)}: {move}"
            )
        else:
            # Playback complete
            self.pause_playback()
            self.progress_label.setText("Solution complete!")
            self.play_btn.setText("▶️ Replay")


# pylint: disable=too-many-instance-attributes
class RubiksCubeDesktopApp(QMainWindow):
    """Main desktop application window for Rubik's Cube solver"""

    def __init__(self):
        super().__init__()
        self.cube = Cube()
        self.solver = CubeSolver()
        self.solution_steps = []
        self.current_step = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.play_next_solution_step)
        self.solver_thread = None  # Track background solver thread
        self.scramble_moves = []  # Store last scramble sequence

        self.init_ui()
        logger.info("Desktop application initialized")

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Rubik's Cube Solver - Desktop Edition")
        self.setGeometry(100, 100, 1400, 900)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Controls
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)

        # Right panel - 3D Cube View with tooltip
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.cube_widget = CubeGLWidget(self.cube)
        self.cube_widget.on_face_clicked = self.handle_face_click
        right_layout.addWidget(self.cube_widget)

        # Tooltip label at bottom (fixed height, readable font)
        self.tooltip_label = QLabel(
            "💡 Left-click: Clockwise | Right-click: Counter-clockwise | Drag: Rotate view"
        )
        self.tooltip_label.setAlignment(Qt.AlignCenter)
        self.tooltip_label.setFixedHeight(30)  # Fixed height to prevent stretching
        self.tooltip_label.setStyleSheet("""
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 6px;
            border-top: 2px solid #34495e;
            font-size: 12px;
            font-weight: bold;
            """)
        right_layout.addWidget(self.tooltip_label)

        splitter.addWidget(right_panel)

        # Set initial sizes (30% controls, 70% cube view)
        splitter.setSizes([400, 1000])

        main_layout.addWidget(splitter)

        # Status bar
        self.status_label = QLabel("Ready | Cube is solved")
        self.statusBar().addWidget(self.status_label)

        logger.info("UI initialized")

    # pylint: disable=too-many-locals,too-many-statements,attribute-defined-outside-init
    def create_control_panel(self):
        """Create the left control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)

        # Title
        title = QLabel("Rubik's Cube Solver")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Cube status
        self.status_box = QLabel("🟢 Solved")
        self.status_box.setFont(QFont("Arial", 12, QFont.Bold))
        self.status_box.setAlignment(Qt.AlignCenter)
        self.status_box.setStyleSheet("""
            background-color: #d4edda;
            color: #155724;
            padding: 10px;
            border-radius: 5px;
            border: 2px solid #c3e6cb;
            """)
        layout.addWidget(self.status_box)

        # Move counter
        self.move_counter = QLabel("0 moves")
        self.move_counter.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.move_counter)

        # Quick Actions Group
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout()

        self.scramble_btn = QPushButton("🎲 Scramble")
        self.scramble_btn.clicked.connect(self.handle_scramble)
        actions_layout.addWidget(self.scramble_btn)

        self.reveal_scramble_btn = QPushButton("🔍 Reveal Scramble")
        self.reveal_scramble_btn.setToolTip("Show the scramble sequence")
        self.reveal_scramble_btn.clicked.connect(self.handle_reveal_scramble)
        self.reveal_scramble_btn.setVisible(False)  # Hidden initially
        actions_layout.addWidget(self.reveal_scramble_btn)

        self.solve_btn = QPushButton("🧠 Solve")
        self.solve_btn.clicked.connect(self.handle_solve)
        actions_layout.addWidget(self.solve_btn)

        self.reset_btn = QPushButton("🔄 Reset")
        self.reset_btn.clicked.connect(self.handle_reset)
        actions_layout.addWidget(self.reset_btn)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        # Move Input Group
        move_group = QGroupBox("Execute Moves")
        move_layout = QVBoxLayout()

        move_input_layout = QHBoxLayout()
        self.move_input = QLineEdit()
        self.move_input.setPlaceholderText("R U R' U'")
        self.move_input.returnPressed.connect(self.handle_execute_move)
        move_input_layout.addWidget(self.move_input)

        execute_btn = QPushButton("Execute")
        execute_btn.clicked.connect(self.handle_execute_move)
        move_input_layout.addWidget(execute_btn)

        move_layout.addLayout(move_input_layout)

        # Quick move buttons
        quick_moves_label = QLabel("Quick Moves:")
        move_layout.addWidget(quick_moves_label)

        quick_moves_layout1 = QHBoxLayout()
        for move in ["R", "L", "U", "D", "F", "B"]:
            btn = QPushButton(move)
            btn.clicked.connect(lambda checked, m=move: self.execute_move(m))
            quick_moves_layout1.addWidget(btn)
        move_layout.addLayout(quick_moves_layout1)

        quick_moves_layout2 = QHBoxLayout()
        for move in ["R'", "L'", "U'", "D'", "F'", "B'"]:
            btn = QPushButton(move)
            btn.clicked.connect(lambda checked, m=move: self.execute_move(m))
            quick_moves_layout2.addWidget(btn)
        move_layout.addLayout(quick_moves_layout2)

        move_group.setLayout(move_layout)
        layout.addWidget(move_group)

        # Solver Options Group
        solver_group = QGroupBox("Solver Options")
        solver_layout = QVBoxLayout()

        algorithm_layout = QHBoxLayout()
        algorithm_layout.addWidget(QLabel("Algorithm:"))
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(["Auto-select", "IDDFS"])
        algorithm_layout.addWidget(self.algorithm_combo)
        solver_layout.addLayout(algorithm_layout)

        depth_layout = QHBoxLayout()
        depth_layout.addWidget(QLabel("Max Depth:"))
        self.max_depth_spin = QSpinBox()
        self.max_depth_spin.setRange(4, 12)
        self.max_depth_spin.setValue(5)
        depth_layout.addWidget(self.max_depth_spin)
        solver_layout.addLayout(depth_layout)

        self.auto_play_check = QCheckBox("Auto-play solution")
        self.auto_play_check.setChecked(True)
        solver_layout.addWidget(self.auto_play_check)

        solver_group.setLayout(solver_layout)
        layout.addWidget(solver_group)

        # Scramble Options Group
        scramble_group = QGroupBox("Scramble Options")
        scramble_layout = QHBoxLayout()
        scramble_layout.addWidget(QLabel("Moves:"))
        self.scramble_moves_spin = QSpinBox()
        self.scramble_moves_spin.setRange(5, 50)
        self.scramble_moves_spin.setValue(5)
        scramble_layout.addWidget(self.scramble_moves_spin)
        scramble_group.setLayout(scramble_layout)
        layout.addWidget(scramble_group)

        # Animation Speed Group
        anim_group = QGroupBox("Animation Speed")
        anim_layout = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(100, 2000)
        self.speed_slider.setValue(500)
        self.speed_slider.setInvertedAppearance(True)  # Faster on right
        self.speed_slider.valueChanged.connect(self.update_animation_speed)
        anim_layout.addWidget(QLabel("Slow"))
        anim_layout.addWidget(self.speed_slider)
        anim_layout.addWidget(QLabel("Fast"))
        anim_group.setLayout(anim_layout)
        layout.addWidget(anim_group)

        # Move Log
        log_group = QGroupBox("Move History")
        log_layout = QVBoxLayout()
        self.move_log = QTextEdit()
        self.move_log.setReadOnly(True)
        self.move_log.setMaximumHeight(150)
        log_layout.addWidget(self.move_log)

        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.move_log.clear)
        log_layout.addWidget(clear_log_btn)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        layout.addStretch()
        return panel

    def update_animation_speed(self):
        """Update the OpenGL widget's animation speed from slider"""
        speed = self.speed_slider.value()
        self.cube_widget.animation_speed = speed

    def handle_face_click(self, move):
        """Handle face click from cube widget"""
        self.execute_move(move)
        self.log_move(f"Face clicked: {move}")

    def execute_move(self, move_notation):
        """Execute a single move on the cube"""
        try:
            # Save cube state BEFORE move for animation
            self.cube_widget.save_cube_state_for_animation()
            # Execute move to update cube state
            self.cube.execute_move(move_notation)
            # Now animate - will use saved state during animation, new state at end
            self.cube_widget.update_cube_state(
                animate=True, move_notation=move_notation
            )
            self.update_status()
            self.log_move(f"Move: {move_notation}")
            logger.info("Executed move: %s", move_notation)
        except Exception as e:
            self.log_move(f"Error: {str(e)}", error=True)
            logger.error("Move execution failed: %s", e)

    def handle_execute_move(self):
        """Handle move input from text field"""
        moves = self.move_input.text().strip()
        if not moves:
            return

        move_list = moves.split()
        for move in move_list:
            self.execute_move(move)

        self.move_input.clear()

    def handle_scramble(self):
        """Scramble the cube"""
        num_moves = self.scramble_moves_spin.value()
        self.scramble_moves = self.cube.scramble(num_moves)  # Store scramble sequence
        self.cube_widget.update_cube_state()
        self.update_status()
        self.log_move(f"Scrambled with {num_moves} moves")
        self.reveal_scramble_btn.setVisible(True)  # Show reveal scramble button
        logger.info("Cube scrambled with %s moves", num_moves)

    def handle_solve(self):
        """Solve the cube in background thread"""
        if self.cube.is_solved():
            self.log_move("Cube is already solved!")
            return

        # Check if already solving
        if self.solver_thread is not None and self.solver_thread.isRunning():
            self.log_move("Solve already in progress...", error=True)
            return

        self.log_move("Solving cube...")
        self.status_label.setText("Solving... (UI remains responsive)")
        self.solve_btn.setEnabled(False)  # Disable solve button during solving

        # Get solver parameters
        algorithm = (
            self.algorithm_combo.currentText().upper().replace("-", "")
            if self.algorithm_combo.currentIndex() > 0
            else None
        )
        max_depth = self.max_depth_spin.value()

        # Create a copy of the cube for the solver thread to avoid UI blocking
        cube_copy = copy.deepcopy(self.cube)

        # Create and start solver thread
        self.solver_thread = SolverThread(cube_copy, self.solver, algorithm, max_depth)
        self.solver_thread.solution_found.connect(self.on_solution_found)
        self.solver_thread.solution_failed.connect(self.on_solution_failed)
        self.solver_thread.finished.connect(self.on_solver_finished)
        self.solver_thread.start()

    def on_solution_found(self, solution):
        """Handle solution found from background thread"""
        self.solution_steps = solution
        self.log_move(f"Solution found: {len(solution)} moves - {' '.join(solution)}")

        if self.auto_play_check.isChecked():
            # Auto-play: execute moves automatically
            self.current_step = 0
            speed = self.speed_slider.value()
            self.animation_timer.start(speed)
        else:
            # Manual control: save scrambled state and show solution dialog
            from solver.core.cube import Face

            scrambled_state = {}
            for face_enum in Face:
                scrambled_state[face_enum] = self.cube.stickers[face_enum].copy()

            dialog = SolutionDialog(solution, scrambled_state, self)
            dialog.exec()

        self.update_status()

    def on_solution_failed(self, error_message):
        """Handle solution failure from background thread"""
        self.log_move(error_message, error=True)
        self.update_status()

    def on_solver_finished(self):
        """Handle solver thread completion"""
        self.solve_btn.setEnabled(True)  # Re-enable solve button
        self.status_label.setText("Ready")
        logger.info("Solver thread finished")

    def play_next_solution_step(self):
        """Play next step in solution animation"""
        if self.current_step < len(self.solution_steps):
            move = self.solution_steps[self.current_step]
            self.execute_move(move)
            self.current_step += 1
        else:
            self.animation_timer.stop()
            self.log_move("Solution complete!")

    def handle_reset(self):
        """Reset cube to solved state"""
        self.cube.reset()
        self.cube_widget.update_cube_state()
        self.update_status()
        self.log_move("Cube reset to solved state")
        self.scramble_moves = []  # Clear scramble sequence
        self.reveal_scramble_btn.setVisible(False)  # Hide reveal scramble button
        logger.info("Cube reset")

    def handle_reveal_scramble(self):
        """Show dialog with scramble sequence"""
        from PySide6.QtWidgets import (  # pylint: disable=import-outside-toplevel
            QMessageBox,
        )

        if not self.scramble_moves:
            QMessageBox.warning(
                self,
                "No Scramble",
                "No scramble sequence available.\nPlease scramble the cube first.",
            )
            return

        scramble_text = " ".join(self.scramble_moves)

        # Create custom message box with copy button
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("🎲 Scramble Sequence")
        msg_box.setText("This is the scramble sequence that was applied to the cube:")
        msg_box.setInformativeText(scramble_text)
        msg_box.setIcon(QMessageBox.Information)

        # Add copy to clipboard button
        copy_btn = msg_box.addButton("📋 Copy to Clipboard", QMessageBox.ActionRole)
        msg_box.addButton(QMessageBox.Ok)

        msg_box.exec()

        # Check if copy button was clicked
        if msg_box.clickedButton() == copy_btn:
            clipboard = QApplication.clipboard()
            clipboard.setText(scramble_text)
            self.log_move("Scramble sequence copied to clipboard")

    def update_status(self):
        """Update status display"""
        move_count = len(self.cube.move_history)
        self.move_counter.setText(f"{move_count} moves")

        if self.cube.is_solved():
            self.status_box.setText("🟢 Solved")
            self.status_box.setStyleSheet("""
                background-color: #d4edda;
                color: #155724;
                padding: 10px;
                border-radius: 5px;
                border: 2px solid #c3e6cb;
                font-weight: bold;
                """)
            self.status_label.setText("Ready | Cube is solved")
        else:
            self.status_box.setText("🔴 Scrambled")
            self.status_box.setStyleSheet("""
                background-color: #f8d7da;
                color: #721c24;
                padding: 10px;
                border-radius: 5px;
                border: 2px solid #f5c6cb;
                font-weight: bold;
                """)
            self.status_label.setText("Ready | Cube is scrambled")

    def log_move(self, message, error=False):
        """Add message to move log"""
        if error:
            self.move_log.append(f"<span style='color: red;'>❌ {message}</span>")
        else:
            self.move_log.append(f"✓ {message}")


def main():
    """Main entry point for desktop application"""
    logger.info("Starting Rubik's Cube Desktop Application...")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern cross-platform style

    window = RubiksCubeDesktopApp()
    window.show()

    logger.info("Application window displayed")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
