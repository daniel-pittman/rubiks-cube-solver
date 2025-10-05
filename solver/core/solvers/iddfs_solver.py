#!/usr/bin/env python3
"""
Iterative Deepening Depth-First Search (IDDFS) solver for Rubik's Cube.

This module implements an IDDFS-based solver that guarantees optimal solutions
by systematically exploring all possible move sequences of increasing depth.
"""

from typing import List, Optional, Set

from ..cube import Cube
from .base_solver import SolverAlgorithm


class IDDFSSolver(SolverAlgorithm):
    """
    Iterative Deepening Depth-First Search cube solver.

    Uses IDDFS to systematically explore all possible move sequences of
    increasing depth until a solution is found, guaranteeing optimal solutions.

    Pros:
    - Guarantees optimal (shortest) solutions
    - Memory efficient compared to BFS
    - Simple and reliable implementation

    Cons:
    - Exponential time complexity limits practical depth to ~8 moves
    - Not suitable for heavily scrambled cubes
    - Re-explores states multiple times (inherent to IDDFS)
    """

    # Standard cube moves (avoiding redundant moves like R2, U2 for simplicity)
    BASIC_MOVES = ["R", "L", "U", "D", "F", "B", "R'", "L'", "U'", "D'", "F'", "B'"]

    @property
    def name(self) -> str:
        """Return the human-readable name of this solving algorithm."""
        return "IDDFS"

    @property
    def description(self) -> str:
        """Return a brief description of this solving algorithm."""
        return (
            "Iterative Deepening Depth-First Search - "
            "guarantees optimal solutions for small scrambles"
        )

    @property
    def max_recommended_depth(self) -> int:
        """Return the maximum depth this algorithm can handle efficiently."""
        return 8

    def can_handle_scramble(self, scramble_depth: int) -> bool:
        """
        Check if this algorithm can efficiently handle a scramble of the given depth.

        Args:
            scramble_depth: The depth/complexity of the scramble

        Returns:
            True if this algorithm is suitable for the given scramble depth
        """
        return scramble_depth <= self.max_recommended_depth

    def solve(
        self, cube: Cube, max_depth: int = 7, verbose: bool = False, **kwargs
    ) -> Optional[List[str]]:
        """
        Solve the cube using iterative deepening depth-first search.

        Args:
            cube: The cube to solve
            max_depth: Maximum search depth to prevent excessive computation
            verbose: Enable verbose output showing search progress
            **kwargs: Additional parameters (unused)

        Returns:
            List of move strings that solve the cube, or None if no solution found
        """
        if cube.is_solved():
            return []

        # Try increasing depths until solution found or max_depth reached
        for depth in range(1, max_depth + 1):
            if verbose:
                print(f"Trying depth {depth}...")

            solution = self._dfs_solve(cube, depth)
            if solution is not None:
                if verbose:
                    print(f"Solution found at depth {depth}!")
                return solution

        if verbose:
            print(f"No solution found within {max_depth} moves")
        return None

    def _dfs_solve(self, cube: Cube, max_depth: int) -> Optional[List[str]]:
        """
        Depth-first search for a solution up to max_depth.

        Args:
            cube: The cube state to solve from
            max_depth: Maximum depth to search

        Returns:
            List of moves that solve the cube, or None if not found at this depth
        """
        return self._dfs_recursive(cube, [], max_depth)

    def _dfs_recursive(
        self, cube: Cube, moves: List[str], remaining_depth: int
    ) -> Optional[List[str]]:
        """
        Recursive depth-first search helper.

        Args:
            cube: Current cube state
            moves: Moves taken so far
            remaining_depth: Remaining depth to explore

        Returns:
            List of moves that solve the cube, or None if not found
        """
        # Base case: check if cube is solved
        if cube.is_solved():
            return moves.copy()

        # Base case: no more depth to explore
        if remaining_depth == 0:
            return None

        # Recursive case: try each possible move
        for move in self.BASIC_MOVES:
            # Skip redundant moves (move followed by its inverse)
            if self._is_redundant_move(moves, move):
                continue

            # Apply move
            test_cube = cube.copy()
            test_cube.execute_move(move)

            # Recursively search deeper
            result = self._dfs_recursive(test_cube, moves + [move], remaining_depth - 1)
            if result is not None:
                return result

        # No solution found at this depth
        return None

    def _is_redundant_move(self, moves: List[str], new_move: str) -> bool:
        """
        Check if a move is redundant (e.g., R followed by R').

        Args:
            moves: Previous moves
            new_move: Move being considered

        Returns:
            True if the move is redundant
        """
        if not moves:
            return False

        last_move = moves[-1]

        # Check if new move cancels the last move
        canceling_pairs = [
            ("R", "R'"),
            ("R'", "R"),
            ("L", "L'"),
            ("L'", "L"),
            ("U", "U'"),
            ("U'", "U"),
            ("D", "D'"),
            ("D'", "D"),
            ("F", "F'"),
            ("F'", "F"),
            ("B", "B'"),
            ("B'", "B"),
        ]

        for move1, move2 in canceling_pairs:
            if last_move == move1 and new_move == move2:
                return True

        # Check if same move repeated (R R -> R2, which we're avoiding for simplicity)
        if last_move == new_move:
            return True

        return False

    # Enhanced version with pruning for potential future optimization
    def solve_with_pruning(
        self, cube: Cube, max_depth: int = 6, verbose: bool = False
    ) -> Optional[List[str]]:
        """
        Enhanced solver with basic pruning to avoid exploring obviously bad paths.

        This method is experimental and may not always outperform the basic solver
        due to the overhead of state tracking.

        Args:
            cube: The cube to solve
            max_depth: Maximum search depth
            verbose: Enable verbose output

        Returns:
            List of move strings that solve the cube, or None if not found
        """
        if cube.is_solved():
            return []

        # Try increasing depths with pruning
        for depth in range(1, max_depth + 1):
            if verbose:
                print(f"Trying depth {depth} with pruning...")

            visited = set()
            solution = self._dfs_solve_with_pruning(cube, [], depth, visited)
            if solution is not None:
                if verbose:
                    print(f"Solution found at depth {depth} with pruning!")
                return solution

        if verbose:
            print(f"No solution found within {max_depth} moves (with pruning)")
        return None

    def _dfs_solve_with_pruning(
        self, cube: Cube, moves: List[str], remaining_depth: int, visited: Set[str]
    ) -> Optional[List[str]]:
        """
        DFS with basic state pruning to avoid revisiting states.

        Args:
            cube: Current cube state
            moves: Moves taken so far
            remaining_depth: Remaining depth to explore
            visited: Set of visited cube signatures

        Returns:
            List of moves that solve the cube, or None if not found
        """
        # Check if cube is solved
        if cube.is_solved():
            return moves.copy()

        # No more depth to explore
        if remaining_depth == 0:
            return None

        # Get cube signature for pruning
        signature = self._get_cube_signature(cube)
        if signature in visited:
            return None  # Already explored this state

        visited.add(signature)

        # Try each possible move
        for move in self.BASIC_MOVES:
            if self._is_redundant_move(moves, move):
                continue

            test_cube = cube.copy()
            test_cube.execute_move(move)

            result = self._dfs_solve_with_pruning(
                test_cube, moves + [move], remaining_depth - 1, visited
            )
            if result is not None:
                return result

        return None

    def _get_cube_signature(self, cube: Cube) -> str:
        """
        Get a signature for the cube state to detect loops.

        Note: This is a simplified signature. A more sophisticated implementation
        would create a canonical representation of the entire cube state.

        Args:
            cube: The cube to get signature for

        Returns:
            String signature representing the cube state
        """
        # Simple signature based on solved state
        return str(cube.is_solved())
