#!/usr/bin/env python3
"""
Interactive Command Line Interface for Rubik's Cube Solver.

Features:
- Colored 3D cube visualization in terminal
- Interactive move execution with real-time updates
- Scrambling with configurable number of moves
- Automated solving with step-by-step visualization
- Multiple solver algorithm selection
- Move history and undo functionality
"""

# pylint: disable=broad-exception-caught,no-else-return,too-many-return-statements
# pylint: disable=too-many-branches,too-many-statements,wrong-import-position
# pylint: disable=unused-import,too-few-public-methods

import os
import re
import sys
from typing import List

# Enable readline for better input editing (backspace, arrows, etc.)
try:
    import readline  # noqa: F401
except ImportError:
    # readline not available on Windows by default
    pass

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from solver.core.cube import Color, Cube
from solver.core.solver import CubeSolver, get_solver_info
from solver.core.solvers import list_available_solvers


class TerminalColors:
    """ANSI color codes for terminal output."""

    # Cube face colors (bright versions for better visibility)
    WHITE = "\033[97m"  # Bright white
    YELLOW = "\033[93m"  # Bright yellow
    RED = "\033[91m"  # Bright red
    ORANGE = "\033[38;5;208m"  # Orange (256-color)
    GREEN = "\033[92m"  # Bright green
    BLUE = "\033[94m"  # Bright blue

    # UI colors
    CYAN = "\033[96m"  # Bright cyan
    MAGENTA = "\033[95m"  # Bright magenta
    GRAY = "\033[90m"  # Gray
    BOLD = "\033[1m"  # Bold
    UNDERLINE = "\033[4m"  # Underline

    # Reset
    RESET = "\033[0m"  # Reset to default

    # Background colors for better contrast
    BG_BLACK = "\033[40m"
    BG_WHITE = "\033[47m"


class CubeVisualizer:
    """Handles colored terminal visualization of the Rubik's cube."""

    COLOR_MAP = {
        Color.WHITE: TerminalColors.WHITE + TerminalColors.BG_BLACK,
        Color.YELLOW: TerminalColors.YELLOW + TerminalColors.BG_BLACK,
        Color.RED: TerminalColors.RED + TerminalColors.BG_BLACK,
        Color.ORANGE: TerminalColors.ORANGE + TerminalColors.BG_BLACK,
        Color.GREEN: TerminalColors.GREEN + TerminalColors.BG_BLACK,
        Color.BLUE: TerminalColors.BLUE + TerminalColors.BG_BLACK,
    }

    @staticmethod
    def get_colored_sticker(color: Color) -> str:
        """Get a colored square character representing a cube sticker."""
        color_code = CubeVisualizer.COLOR_MAP.get(color, TerminalColors.GRAY)
        return f"{color_code}██{TerminalColors.RESET}"

    @staticmethod
    def display_cube(cube: Cube) -> None:
        """Display the cube in a clear 3D unfolded layout with colors."""
        print()
        print(
            f"{TerminalColors.BOLD}{TerminalColors.CYAN}Current Cube State:{TerminalColors.RESET}"
        )
        print()

        # Get cube display and colorize it
        lines = cube.display().split("\n")

        for line in lines:
            # Skip empty lines
            if not line.strip():
                print()
                continue

            # Check if this is a face label line (contains "Face:")
            if "Face:" in line:
                # For face label lines, don't colorize any characters
                print(line)
            else:
                # For cube sticker lines, colorize the letters
                colored_line = ""
                for char in line:
                    if char in "WYROGB":
                        # Map character to color
                        color_map = {
                            "W": Color.WHITE,
                            "Y": Color.YELLOW,
                            "R": Color.RED,
                            "O": Color.ORANGE,
                            "G": Color.GREEN,
                            "B": Color.BLUE,
                        }

                        if char in color_map:
                            colored_line += CubeVisualizer.get_colored_sticker(
                                color_map[char]
                            )
                        else:
                            colored_line += char
                    else:
                        # Regular character (spacing, borders, etc.)
                        colored_line += char

                print(colored_line)

        print()


class CLIApp:
    """Main CLI application for Rubik's Cube interaction."""

    def __init__(self):
        """Initialize the CLI application."""
        self.cube = Cube()
        self.solver = CubeSolver()  # Auto-selecting solver
        self.move_history: List[str] = []
        self.visualizer = CubeVisualizer()
        self.running = True

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system("cls" if os.name == "nt" else "clear")

    def print_header(self):
        """Print the application header."""
        print(f"{TerminalColors.BOLD}{TerminalColors.CYAN}")
        print("🎲 RUBIK'S CUBE SOLVER - Interactive CLI")
        print("=" * 45)
        print(f"{TerminalColors.RESET}")

    def print_status(self):
        """Print current cube status information."""
        status = "SOLVED" if self.cube.is_solved() else "SCRAMBLED"
        status_color = (
            TerminalColors.GREEN if self.cube.is_solved() else TerminalColors.YELLOW
        )

        print(
            f"Status: {status_color}{TerminalColors.BOLD}{status}{TerminalColors.RESET}"
        )
        print(
            f"Moves made: {TerminalColors.CYAN}{len(self.move_history)}{TerminalColors.RESET}"
        )

        if self.move_history:
            recent_moves = " → ".join(self.move_history[-5:])  # Show last 5 moves
            if len(self.move_history) > 5:
                recent_moves = f"... → {recent_moves}"
            print(
                f"Recent moves: {TerminalColors.GRAY}{recent_moves}{TerminalColors.RESET}"
            )

        print()

    def show_help(self, topic: str = None):
        """Display help information."""
        if topic == "moves":
            self.show_moves_help()
            return
        elif topic == "commands":
            self.show_commands_help()
            return

        # General help
        print(
            f"{TerminalColors.BOLD}{TerminalColors.MAGENTA}🎲 Rubik's Cube Solver - Help{TerminalColors.RESET}"
        )
        print()
        print(f"{TerminalColors.CYAN}Quick Start:{TerminalColors.RESET}")
        print("  • Type moves like 'R', 'U', 'F' to rotate cube faces")
        print("  • Type 'scramble' to mix up the cube")
        print("  • Type 'solve' to automatically solve the cube")
        print("  • Type 'help moves' for detailed move notation")
        print("  • Type 'help commands' for all available commands")
        print()
        print(f"{TerminalColors.CYAN}Essential Commands:{TerminalColors.RESET}")
        print("  scramble   - Mix up the cube")
        print("  solve      - Solve the cube automatically")
        print("  reset      - Return to solved state")
        print("  undo       - Undo last move")
        print("  help moves - Learn move notation")
        print("  quit       - Exit the application")
        print()
        print(
            f"{TerminalColors.GRAY}💡 Tip: Start with 'scramble' then try 'solve step' to see the solution step-by-step!{TerminalColors.RESET}"
        )
        print()

    def show_moves_help(self):
        """Display detailed move notation help."""
        print(
            f"{TerminalColors.BOLD}{TerminalColors.MAGENTA}🔄 Move Notation Guide{TerminalColors.RESET}"
        )
        print()
        print(f"{TerminalColors.CYAN}Basic Face Rotations:{TerminalColors.RESET}")
        print("  R  - Right face clockwise 90°")
        print("  L  - Left face clockwise 90°")
        print("  U  - Up face clockwise 90°")
        print("  D  - Down face clockwise 90°")
        print("  F  - Front face clockwise 90°")
        print("  B  - Back face clockwise 90°")
        print()
        print(f"{TerminalColors.CYAN}Modifiers:{TerminalColors.RESET}")
        print("  '  - Counter-clockwise (e.g., R' = right counter-clockwise)")
        print("  2  - Double turn/180° (e.g., R2 = right face twice)")
        print("  w  - Wide turn/two layers (e.g., Rw = right + middle layer)")
        print()
        print(f"{TerminalColors.CYAN}Examples:{TerminalColors.RESET}")
        print("  R    - Turn right face clockwise")
        print("  R'   - Turn right face counter-clockwise")
        print("  R2   - Turn right face 180 degrees")
        print("  Rw   - Turn right face and middle layer clockwise")
        print("  2R   - Turn second layer from right")
        print("  2Rw' - Turn second layer + wide, counter-clockwise")
        print()
        print(f"{TerminalColors.CYAN}Try These Sequences:{TerminalColors.RESET}")
        print("  R U R' U'     - Classic beginner sequence")
        print("  R U2 R' U'    - Modified sequence")
        print("  F R U' R' F'  - Another common pattern")
        print()
        print(f"{TerminalColors.CYAN}Sequence Support:{TerminalColors.RESET}")
        print("  • You can enter multiple moves separated by spaces")
        print("  • Example: Type 'R U R' U'' to execute all four moves")
        print("  • Each move in the sequence will be executed in order")
        print()
        print(
            f"{TerminalColors.GRAY}💡 Tips: All moves are case-insensitive. Use backspace to edit your input.{TerminalColors.RESET}"
        )
        print()

    def show_commands_help(self):
        """Display detailed commands help."""
        print(
            f"{TerminalColors.BOLD}{TerminalColors.MAGENTA}⌨️  All Available Commands{TerminalColors.RESET}"
        )
        print()
        print(f"{TerminalColors.CYAN}Cube Manipulation:{TerminalColors.RESET}")
        print("  <move>        - Execute a move (see 'help moves' for notation)")
        print("  <sequence>    - Execute multiple moves (e.g., 'R U R' U'')")
        print("  reset         - Reset cube to solved state")
        print("  scramble      - Scramble cube (default: 5 moves)")
        print("  scramble N    - Scramble cube with N moves (e.g., 'scramble 10')")
        print()
        print(f"{TerminalColors.CYAN}Solving:{TerminalColors.RESET}")
        print("  solve      - Solve the cube automatically")
        print("  solve step - Solve with step-by-step visualization")
        print("  algorithms - List available solving algorithms")
        print()
        print(f"{TerminalColors.CYAN}History & Navigation:{TerminalColors.RESET}")
        print("  history    - Show complete move history")
        print("  undo       - Undo the last move")
        print("  clear      - Clear move history")
        print()
        print(f"{TerminalColors.CYAN}Display & Interface:{TerminalColors.RESET}")
        print("  show       - Display current cube state")
        print("  cls        - Clear screen")
        print("  help       - Show general help")
        print("  help moves - Show move notation guide")
        print("  help commands - Show this command reference")
        print()
        print(f"{TerminalColors.CYAN}System:{TerminalColors.RESET}")
        print("  quit/exit  - Exit the application")
        print()
        print(
            f"{TerminalColors.GRAY}💡 All commands are case-insensitive. You can use shortcuts like 'q' for quit.{TerminalColors.RESET}"
        )
        print()

    def execute_move(self, move_str: str) -> bool:
        """Execute a move on the cube."""
        try:
            self.cube.execute_move(move_str)
            self.move_history.append(move_str)
            print(
                f"{TerminalColors.GREEN}✓ Executed move: {move_str}{TerminalColors.RESET}"
            )
            return True
        except Exception as e:
            print(
                f"{TerminalColors.RED}✗ Invalid move '{move_str}': {e}{TerminalColors.RESET}"
            )
            return False

    def scramble_cube(self, num_moves: int = 5):
        """Scramble the cube with random moves."""
        print(
            f"{TerminalColors.YELLOW}🎲 Scrambling cube with {num_moves} moves...{TerminalColors.RESET}"
        )

        # Generate scramble moves
        scramble_moves = self.cube.scramble(num_moves)
        self.move_history.extend(scramble_moves)

        print(
            f"{TerminalColors.GREEN}✓ Scrambled! Moves used: {' '.join(scramble_moves)}{TerminalColors.RESET}"
        )
        print()

    def solve_cube(self, step_by_step: bool = False):
        """Solve the cube using the current algorithm."""
        if self.cube.is_solved():
            print(
                f"{TerminalColors.GREEN}✓ Cube is already solved!{TerminalColors.RESET}"
            )
            return

        print(f"{TerminalColors.YELLOW}🔍 Solving cube...{TerminalColors.RESET}")

        try:
            # Get algorithm info
            algo_info = self.solver.get_algorithm_info()
            print(
                f"Using algorithm: {TerminalColors.CYAN}{algo_info.get('name', 'Auto-select')}{TerminalColors.RESET}"
            )

            # Solve the cube
            solution = self.solver.solve(self.cube)

            if solution is None:
                print(
                    f"{TerminalColors.RED}✗ No solution found within search limits{TerminalColors.RESET}"
                )
                return

            print(
                f"{TerminalColors.GREEN}✓ Solution found! {len(solution)} moves: {' '.join(solution)}{TerminalColors.RESET}"
            )
            print()

            if step_by_step:
                print(
                    f"{TerminalColors.MAGENTA}Applying solution step by step:{TerminalColors.RESET}"
                )
                input("Press Enter to start...")

                for i, move in enumerate(solution):
                    print(
                        f"{TerminalColors.BOLD}Step {i+1}/{len(solution)}: {move}{TerminalColors.RESET}"
                    )
                    self.cube.execute_move(move)
                    self.move_history.append(move)

                    # Display cube state
                    self.visualizer.display_cube(self.cube)
                    self.print_status()

                    if i < len(solution) - 1:  # Don't wait after the last move
                        input("Press Enter for next move...")
                    print()
            else:
                # Apply all moves at once
                for move in solution:
                    self.cube.execute_move(move)
                    self.move_history.append(move)

            print(
                f"{TerminalColors.GREEN}🎉 Cube solved successfully!{TerminalColors.RESET}"
            )

        except Exception as e:
            print(
                f"{TerminalColors.RED}✗ Error during solving: {e}{TerminalColors.RESET}"
            )

    def show_algorithms(self):
        """Display available solving algorithms."""
        print(
            f"{TerminalColors.BOLD}{TerminalColors.MAGENTA}Available Solving Algorithms:{TerminalColors.RESET}"
        )
        print()

        algorithms = list_available_solvers()
        for algo in algorithms:
            print(f"{TerminalColors.CYAN}• {algo['name']}{TerminalColors.RESET}")
            print(f"  {algo['description']}")
            print(f"  Max depth: {algo['max_recommended_depth']} moves")
            print()

        # Show current solver info
        solver_info = get_solver_info()
        current_algo = solver_info.get("default_algorithm", "Unknown")
        print(
            f"Current default: {TerminalColors.GREEN}{current_algo}{TerminalColors.RESET}"
        )
        print()

    def show_history(self):
        """Display move history."""
        if not self.move_history:
            print(f"{TerminalColors.GRAY}No moves made yet.{TerminalColors.RESET}")
            return

        print(
            f"{TerminalColors.BOLD}{TerminalColors.MAGENTA}Move History ({len(self.move_history)} moves):{TerminalColors.RESET}"
        )
        print()

        # Display moves in groups of 10
        for i in range(0, len(self.move_history), 10):
            group = self.move_history[i : i + 10]
            move_numbers = [
                f"{j+1:3d}" for j in range(i, min(i + 10, len(self.move_history)))
            ]

            print(
                f"{TerminalColors.GRAY}"
                + "  ".join(move_numbers)
                + f"{TerminalColors.RESET}"
            )
            print(
                f"{TerminalColors.CYAN}"
                + "  ".join(f"{move:>3}" for move in group)
                + f"{TerminalColors.RESET}"
            )
            print()

    def undo_last_move(self):
        """Undo the last move made."""
        if not self.move_history:
            print(f"{TerminalColors.GRAY}No moves to undo.{TerminalColors.RESET}")
            return

        # Get the last move and compute its inverse
        last_move = self.move_history.pop()

        try:
            # Simple inverse logic for standard moves
            if last_move.endswith("'"):
                inverse_move = last_move[:-1]  # Remove prime
            elif last_move.endswith("2"):
                inverse_move = last_move  # Double moves are self-inverse
            else:
                inverse_move = last_move + "'"  # Add prime

            self.cube.execute_move(inverse_move)
            print(
                f"{TerminalColors.GREEN}✓ Undid move: {last_move} (applied {inverse_move}){TerminalColors.RESET}"
            )

        except Exception as e:
            # If inverse fails, restore the move to history
            self.move_history.append(last_move)
            print(
                f"{TerminalColors.RED}✗ Failed to undo move: {e}{TerminalColors.RESET}"
            )

    def clear_history(self):
        """Clear the move history."""
        self.move_history.clear()
        print(f"{TerminalColors.GREEN}✓ Move history cleared.{TerminalColors.RESET}")

    def reset_cube(self):
        """Reset cube to solved state."""
        self.cube = Cube()  # Create new solved cube
        self.move_history.clear()
        print(
            f"{TerminalColors.GREEN}✓ Cube reset to solved state.{TerminalColors.RESET}"
        )

    def process_command(self, command: str):
        """Process a user command."""
        command = command.strip().lower()

        if not command:
            return

        # Handle quit/exit
        if command in ["quit", "exit", "q"]:
            self.running = False
            return

        # Handle help
        if command in ["help", "h", "?"]:
            self.show_help()
            return
        elif command.startswith("help "):
            topic = command.split(" ", 1)[1]
            self.show_help(topic)
            return

        # Handle clear screen
        if command in ["cls", "clear"]:
            self.clear_screen()
            self.print_header()
            return

        # Handle show cube
        if command == "show":
            self.visualizer.display_cube(self.cube)
            self.print_status()
            return

        # Handle reset
        if command == "reset":
            self.reset_cube()
            return

        # Handle scramble
        if command.startswith("scramble"):
            parts = command.split()
            if len(parts) == 1:
                num_moves = 5
            else:
                try:
                    num_moves = int(parts[1])
                    if num_moves < 1:
                        print(
                            f"{TerminalColors.RED}✗ Number of moves must be positive{TerminalColors.RESET}"
                        )
                        return
                except ValueError:
                    print(
                        f"{TerminalColors.RED}✗ Invalid number of moves: {parts[1]}{TerminalColors.RESET}"
                    )
                    return

            self.scramble_cube(num_moves)
            return

        # Handle solve
        if command.startswith("solve"):
            parts = command.split()
            step_by_step = len(parts) > 1 and parts[1] == "step"
            self.solve_cube(step_by_step)
            return

        # Handle algorithms
        if command == "algorithms":
            self.show_algorithms()
            return

        # Handle history
        if command == "history":
            self.show_history()
            return

        # Handle undo
        if command == "undo":
            self.undo_last_move()
            return

        # Handle clear history
        if command == "clear":
            self.clear_history()
            return

        # Try to parse as a move or sequence of moves
        move_pattern = r"^[RUFDLBxyz][w]?[2\']?$|^[2-9][RUFDLBxyz][w]?[2\']?$"

        # Check if it's a single move
        if re.match(move_pattern, command, re.IGNORECASE):
            self.execute_move(command.upper())
        else:
            # Try to parse as a sequence of moves separated by spaces
            moves = command.split()
            if moves and all(
                re.match(move_pattern, move, re.IGNORECASE) for move in moves
            ):
                print(
                    f"{TerminalColors.YELLOW}🎯 Executing sequence: {' '.join(moves).upper()}{TerminalColors.RESET}"
                )
                for move in moves:
                    success = self.execute_move(move.upper())
                    if not success:
                        print(
                            f"{TerminalColors.RED}✗ Sequence stopped at move: {move}{TerminalColors.RESET}"
                        )
                        break
                print(
                    f"{TerminalColors.GREEN}✓ Sequence completed!{TerminalColors.RESET}"
                )
            else:
                print(
                    f"{TerminalColors.RED}✗ Unknown command: {command}{TerminalColors.RESET}"
                )
                print(
                    f"Type '{TerminalColors.CYAN}help{TerminalColors.RESET}' for available commands."
                )

    def run(self):
        """Main application loop."""
        self.clear_screen()
        self.print_header()

        print(
            f"{TerminalColors.GREEN}Welcome to the Interactive Rubik's Cube Solver!{TerminalColors.RESET}"
        )
        print()
        print(f"{TerminalColors.YELLOW}🚀 Quick Start Guide:{TerminalColors.RESET}")
        print(
            f"  • Try '{TerminalColors.CYAN}scramble{TerminalColors.RESET}' to mix up the cube"
        )
        print(
            f"  • Try '{TerminalColors.CYAN}solve{TerminalColors.RESET}' to solve it automatically"
        )
        print(
            f"  • Try '{TerminalColors.CYAN}help moves{TerminalColors.RESET}' "
            "to learn move notation"
        )
        print(
            f"  • Type '{TerminalColors.CYAN}help{TerminalColors.RESET}' for all available commands"
        )
        print()

        # Display initial cube state
        self.visualizer.display_cube(self.cube)
        self.print_status()

        # Main command loop
        while self.running:
            try:
                command = input(f"{TerminalColors.BOLD}cube> {TerminalColors.RESET}")
                self.process_command(command)

                # Show cube state after each command (except help, clear, etc.)
                if command.strip().lower() not in [
                    "help",
                    "h",
                    "?",
                    "cls",
                    "clear",
                    "algorithms",
                    "history",
                ]:
                    self.visualizer.display_cube(self.cube)
                    self.print_status()

            except KeyboardInterrupt:
                print(
                    f"\n{TerminalColors.YELLOW}Use 'quit' to exit properly.{TerminalColors.RESET}"
                )
            except EOFError:
                break

        print(
            f"\n{TerminalColors.GREEN}Thanks for using Rubik's Cube Solver! 🎲{TerminalColors.RESET}"
        )


def main():
    """Main entry point for the CLI application."""
    app = CLIApp()
    app.run()


if __name__ == "__main__":
    main()
