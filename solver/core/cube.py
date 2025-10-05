"""
Transformation-based Rubik's Cube implementation.

Based on the MagicCube approach by David W. Hogg, using numpy array
transformations to handle face rotations and edge cycling correctly.
"""

import random
from enum import IntEnum
from typing import List, Tuple

import numpy as np


class Color(IntEnum):
    """Rubik's cube face colors following Western/WCA color scheme."""

    WHITE = 0  # Up (Y+)
    YELLOW = 1  # Down (Y-)
    RED = 2  # Right (X+)
    ORANGE = 3  # Left (X-)
    GREEN = 4  # Front (Z+)
    BLUE = 5  # Back (Z-)


class Face(IntEnum):
    """Cube faces with their orientations."""

    U = 0  # Up (White)
    D = 1  # Down (Yellow)
    R = 2  # Right (Red)
    L = 3  # Left (Orange)
    F = 4  # Front (Green)
    B = 5  # Back (Blue)


class Cube:
    """
    Rubik's Cube using numpy array transformations for correct move implementation.

    This approach uses a 3D numpy array where:
    - First dimension: 6 faces
    - Second dimension: 3 rows per face
    - Third dimension: 3 columns per face

    Moves are implemented by:
    1. Rotating the face itself using np.rot90
    2. Cycling edge pieces between adjacent faces using array slicing
    """

    def __init__(self):
        """Initialize a solved cube."""
        self.N = 3  # pylint: disable=invalid-name  # Standard notation for cube size
        self.move_history = []
        self.reset()

    def reset(self):
        """Reset cube to solved state."""
        # Create 6 faces, each filled with its corresponding color
        # pylint: disable=attribute-defined-outside-init  # reset() is called in __init__
        self.stickers = np.array([np.full((self.N, self.N), color) for color in Color])
        self.move_history = []

    def _cycle_edges(self, edges: List[Tuple]):
        """
        Cycle edge pieces between faces.

        Args:
            edges: List of (face_index, row_selector, col_selector) tuples
                   representing the edges to cycle
        """
        # Save the first edge
        first_edge = edges[0]
        temp = self.stickers[first_edge].copy()

        # Shift each edge to the previous position
        current = first_edge
        for next_edge in edges[1:]:
            self.stickers[current] = self.stickers[next_edge]
            current = next_edge

        # Place the first edge in the last position
        self.stickers[current] = temp

    def R(self):  # pylint: disable=invalid-name  # Standard Rubik's cube notation
        """Right face clockwise rotation."""
        # Rotate the R face itself
        self.stickers[Face.R] = np.rot90(self.stickers[Face.R], -1)

        # Cycle edges: F right -> U right -> B left -> D right -> F right
        # This is the correct clockwise cycle when looking at R face

        # Save edges before cycling
        f_right = self.stickers[Face.F, :, 2].copy()
        u_right = self.stickers[Face.U, :, 2].copy()
        b_left = self.stickers[Face.B, :, 0].copy()
        d_right = self.stickers[Face.D, :, 2].copy()

        # Perform the cycling with proper reversals
        self.stickers[Face.U, :, 2] = f_right  # F goes up to U
        self.stickers[Face.B, :, 0] = u_right[::-1]  # U goes back to B (reversed)
        self.stickers[Face.D, :, 2] = b_left[::-1]  # B goes down to D (reversed)
        self.stickers[Face.F, :, 2] = d_right  # D goes forward to F

    def R_prime(self):  # pylint: disable=invalid-name  # Standard Rubik's cube notation
        """Right face counter-clockwise rotation."""
        # Three rights make a left
        self.R()
        self.R()
        self.R()

    def L(self):  # pylint: disable=invalid-name  # Standard Rubik's cube notation
        """Left face clockwise rotation."""
        # Rotate the L face itself
        self.stickers[Face.L] = np.rot90(self.stickers[Face.L], -1)

        # Cycle edges: U left -> F left -> D left -> B right -> U left
        # B face is on opposite side

        # Save edges before cycling
        u_left = self.stickers[Face.U, :, 0].copy()
        f_left = self.stickers[Face.F, :, 0].copy()
        d_left = self.stickers[Face.D, :, 0].copy()
        b_right = self.stickers[Face.B, :, 2].copy()

        # Perform the cycling with proper reversals
        self.stickers[Face.F, :, 0] = u_left
        self.stickers[Face.D, :, 0] = f_left
        self.stickers[Face.B, :, 2] = d_left[::-1]  # Reverse when going to B
        self.stickers[Face.U, :, 0] = b_right[::-1]  # Reverse when coming from B

    def L_prime(self):  # pylint: disable=invalid-name  # Standard Rubik's cube notation
        """Left face counter-clockwise rotation."""
        self.L()
        self.L()
        self.L()

    def U(self):  # pylint: disable=invalid-name  # Standard Rubik's cube notation
        """Up face clockwise rotation."""
        # Rotate the U face itself
        self.stickers[Face.U] = np.rot90(self.stickers[Face.U], -1)

        # Cycle edges: F -> L -> B -> R -> F (clockwise when looking down at U)
        # All are top rows (row 0)
        f_top = self.stickers[Face.F, 0, :].copy()
        r_top = self.stickers[Face.R, 0, :].copy()
        b_top = self.stickers[Face.B, 0, :].copy()
        l_top = self.stickers[Face.L, 0, :].copy()

        # Perform the cycle
        self.stickers[Face.L, 0, :] = f_top  # F -> L
        self.stickers[Face.B, 0, :] = l_top  # L -> B
        self.stickers[Face.R, 0, :] = b_top  # B -> R
        self.stickers[Face.F, 0, :] = r_top  # R -> F

    def U_prime(self):  # pylint: disable=invalid-name  # Standard Rubik's cube notation
        """Up face counter-clockwise rotation."""
        self.U()
        self.U()
        self.U()

    def D(self):  # pylint: disable=invalid-name  # Standard Rubik's cube notation
        """Down face clockwise rotation."""
        # Rotate the D face itself
        self.stickers[Face.D] = np.rot90(self.stickers[Face.D], -1)

        # Cycle edges: F -> R -> B -> L -> F (clockwise when looking down at D)
        # All are bottom rows (row 2)
        f_bot = self.stickers[Face.F, 2, :].copy()
        r_bot = self.stickers[Face.R, 2, :].copy()
        b_bot = self.stickers[Face.B, 2, :].copy()
        l_bot = self.stickers[Face.L, 2, :].copy()

        # Perform the cycle
        self.stickers[Face.R, 2, :] = f_bot  # F -> R
        self.stickers[Face.B, 2, :] = r_bot  # R -> B
        self.stickers[Face.L, 2, :] = b_bot  # B -> L
        self.stickers[Face.F, 2, :] = l_bot  # L -> F

    def D_prime(self):  # pylint: disable=invalid-name  # Standard Rubik's cube notation
        """Down face counter-clockwise rotation."""
        self.D()
        self.D()
        self.D()

    def F(self):  # pylint: disable=invalid-name  # Standard Rubik's cube notation
        """Front face clockwise rotation."""
        # Rotate the F face itself
        self.stickers[Face.F] = np.rot90(self.stickers[Face.F], -1)

        # Cycle edges: U bottom -> R left -> D top -> L right -> U bottom
        # (clockwise when looking at F). Need to handle row/column conversions

        # Save edges before cycling
        u_bottom = self.stickers[Face.U, 2, :].copy()
        r_left = self.stickers[Face.R, :, 0].copy()
        d_top = self.stickers[Face.D, 0, :].copy()
        l_right = self.stickers[Face.L, :, 2].copy()

        # Perform the cycle with proper transformations
        self.stickers[Face.R, :, 0] = u_bottom  # U bottom row -> R left col
        self.stickers[Face.D, 0, :] = r_left[::-1]  # R left col -> D top row (reversed)
        self.stickers[Face.L, :, 2] = d_top  # D top row -> L right col
        self.stickers[Face.U, 2, :] = l_right[
            ::-1
        ]  # L right col -> U bottom row (reversed)

    def F_prime(self):  # pylint: disable=invalid-name  # Standard Rubik's cube notation
        """Front face counter-clockwise rotation."""
        self.F()
        self.F()
        self.F()

    def B(self):  # pylint: disable=invalid-name  # Standard Rubik's cube notation
        """Back face clockwise rotation."""
        # Rotate the B face itself
        self.stickers[Face.B] = np.rot90(self.stickers[Face.B], -1)

        # Cycle edges: U top -> L left -> D bottom -> R right -> U top (clockwise when looking at B)
        # Need to handle row/column conversions

        # Save edges before cycling
        u_top = self.stickers[Face.U, 0, :].copy()
        l_left = self.stickers[Face.L, :, 0].copy()
        d_bottom = self.stickers[Face.D, 2, :].copy()
        r_right = self.stickers[Face.R, :, 2].copy()

        # Perform the cycle with proper transformations
        self.stickers[Face.L, :, 0] = u_top[::-1]  # U top row -> L left col (reversed)
        self.stickers[Face.D, 2, :] = l_left  # L left col -> D bottom row
        self.stickers[Face.R, :, 2] = d_bottom[
            ::-1
        ]  # D bottom row -> R right col (reversed)
        self.stickers[Face.U, 0, :] = r_right  # R right col -> U top row

    def B_prime(self):  # pylint: disable=invalid-name  # Standard Rubik's cube notation
        """Back face counter-clockwise rotation."""
        self.B()
        self.B()
        self.B()

    def execute_move(self, move: str, track_history: bool = True):
        """Execute a move given in standard notation.

        Supports standard Western notation:
        - Base moves: R, L, U, D, F, B (clockwise 90°)
        - Prime moves: R', L', U', D', F', B' (counter-clockwise 90°)
        - Double moves: R2, L2, U2, D2, F2, B2 (180°)

        Args:
            move: Move in standard notation (e.g., 'R', "R'", 'R2')
            track_history: Whether to add this move to move_history (default: True)

        Raises:
            ValueError: If move notation is not recognized
        """
        moves = {
            "R": self.R,
            "R'": self.R_prime,
            "R2": lambda: (self.R(), self.R()),
            "L": self.L,
            "L'": self.L_prime,
            "L2": lambda: (self.L(), self.L()),
            "U": self.U,
            "U'": self.U_prime,
            "U2": lambda: (self.U(), self.U()),
            "D": self.D,
            "D'": self.D_prime,
            "D2": lambda: (self.D(), self.D()),
            "F": self.F,
            "F'": self.F_prime,
            "F2": lambda: (self.F(), self.F()),
            "B": self.B,
            "B'": self.B_prime,
            "B2": lambda: (self.B(), self.B()),
        }

        if move in moves:
            moves[move]()
            if track_history:
                self.move_history.append(move)
        else:
            raise ValueError(f"Unknown move: {move}")

    def is_solved(self) -> bool:
        """Check if cube is in solved state.

        A cube is solved when each face has all stickers of the same color.

        Returns:
            bool: True if cube is solved, False otherwise
        """
        for face_stickers in self.stickers:
            if not np.all(face_stickers == face_stickers[0, 0]):
                return False
        return True

    def _get_face_display_grid(self, face: Face):
        """Convert a face's array to 3x3 grid format for testing."""
        # Already in grid format, just return it
        return self.stickers[face]

    def display(self) -> str:
        """Return a string representation of the cube.

        Creates an unfolded view showing all six faces with single-letter color codes:
        W (White), Y (Yellow), R (Red), O (Orange), G (Green), B (Blue)

        Returns:
            str: Multi-line string showing all cube faces
        """
        color_map = {
            Color.WHITE: "W",
            Color.YELLOW: "Y",
            Color.RED: "R",
            Color.ORANGE: "O",
            Color.GREEN: "G",
            Color.BLUE: "B",
        }

        result = "Cube Display (Unfolded):\n\n"

        face_names = ["U", "D", "R", "L", "F", "B"]
        for i, face_name in enumerate(face_names):
            result += f"{face_name} Face:\n"
            for row in self.stickers[i]:
                result += "  " + " ".join(color_map[int(c)] for c in row) + "\n"
            result += "\n"

        return result

    def scramble(self, num_moves: int = 20) -> List[str]:
        """Scramble the cube with random moves.

        Applies a random sequence of face turns to scramble the cube.
        Each move is randomly selected from all 12 basic moves (6 faces × 2 directions).

        Args:
            num_moves: Number of random moves to apply (default: 20)

        Returns:
            List[str]: The sequence of moves that were applied
        """
        possible_moves = [
            "R",
            "R'",
            "L",
            "L'",
            "U",
            "U'",
            "D",
            "D'",
            "F",
            "F'",
            "B",
            "B'",
        ]
        moves = []

        for _ in range(num_moves):
            move = random.choice(possible_moves)
            self.execute_move(move)
            moves.append(move)

        return moves

    def copy(self):
        """Create a deep copy of the cube.

        Creates an independent copy with the same state and move history.
        Useful for testing moves without modifying the original cube.

        Returns:
            Cube: A new Cube instance with copied state
        """
        new_cube = Cube()
        new_cube.stickers = self.stickers.copy()
        new_cube.move_history = self.move_history.copy()
        return new_cube

    def save_state(self):
        """Save the current cube state for later restoration.

        Captures a snapshot of the cube's current sticker positions and move history.

        Returns:
            dict: State dictionary with 'stickers' and 'move_history' keys
        """
        return {
            "stickers": self.stickers.copy(),
            "move_history": self.move_history.copy(),
        }

    def restore_state(self, state: dict):
        """
        Restore a previously saved cube state.

        Args:
            state: Dictionary containing 'stickers' and 'move_history' arrays
        """
        # pylint: disable=attribute-defined-outside-init  # Valid use for deserialization
        self.stickers = state["stickers"].copy()
        self.move_history = state["move_history"].copy()
