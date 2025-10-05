#!/usr/bin/env python3
"""
Main Rubik's Cube Solver Interface.

This module provides the main CubeSolver class that acts as a facade for
the various solving algorithms available in the solver plugin system.
It maintains backward compatibility with existing code while providing
access to the new multi-algorithm architecture.
"""

from typing import List, Optional

from .cube import Cube
from .solvers import (
    get_best_solver,
    get_default_solver,
    get_solver,
    list_available_solvers,
)


class CubeSolver:
    """
    Main interface for solving Rubik's cubes.

    This class acts as a facade for the solver plugin system, providing easy access
    to different solving algorithms while maintaining backward compatibility.

    The solver automatically selects the best algorithm based on the scramble
    complexity, or you can specify a particular algorithm to use.
    """

    def __init__(self, algorithm: str = None):
        """
        Initialize the cube solver.

        Args:
            algorithm: Specific algorithm to use (e.g., "IDDFS"). If None,
                      will automatically select the best algorithm for each solve.
        """
        self._algorithm_name = algorithm
        self._solver_instance = None

        if algorithm:
            self._solver_instance = get_solver(algorithm)

    def solve(
        self, cube: Cube, max_depth: int = 7, algorithm: str = None, **kwargs
    ) -> Optional[List[str]]:
        """
        Solve the cube using the specified or best available algorithm.

        Args:
            cube: The cube to solve
            max_depth: Maximum search depth (algorithm-dependent)
            algorithm: Override the default algorithm for this solve
            **kwargs: Additional parameters passed to the solving algorithm

        Returns:
            List of move strings that solve the cube, or None if no solution found

        Example:
            solver = CubeSolver()
            solution = solver.solve(cube)  # Use best algorithm

            solver = CubeSolver("IDDFS")
            solution = solver.solve(cube, max_depth=8)  # Use specific algorithm

            solution = solver.solve(cube, algorithm="IDDFS", verbose=True)  # Override for one solve
        """
        if cube.is_solved():
            return []

        # Determine which algorithm to use
        if algorithm:
            # Use specified algorithm for this solve
            solver_instance = get_solver(algorithm)
        elif self._solver_instance:
            # Use instance-specific algorithm
            solver_instance = self._solver_instance
        else:
            # Auto-select best algorithm based on estimated scramble depth
            estimated_depth = min(max_depth, 8)  # Estimate based on max_depth requested
            solver_instance = get_best_solver(estimated_depth)

        # Solve using the selected algorithm
        return solver_instance.solve(cube, max_depth=max_depth, **kwargs)

    def get_algorithm_info(self) -> dict:
        """
        Get information about the currently selected algorithm.

        Returns:
            Dictionary containing algorithm information, or info about auto-selection
        """
        if self._solver_instance:
            return self._solver_instance.get_algorithm_info()

        return {
            "mode": "auto-select",
            "description": "Automatically selects the best algorithm for each solve",
            "available_algorithms": list_available_solvers(),
        }

    @staticmethod
    def list_algorithms() -> List[dict]:
        """
        List all available solving algorithms.

        Returns:
            List of dictionaries containing information about each available algorithm
        """
        return list_available_solvers()

    @staticmethod
    def get_algorithm_recommendations(scramble_depth: int) -> List[str]:
        """
        Get recommended algorithms for a given scramble depth.

        Args:
            scramble_depth: The depth/complexity of the scramble

        Returns:
            List of algorithm names, ordered by suitability (best first)
        """
        algorithms = list_available_solvers()

        # Filter and sort algorithms by their ability to handle the scramble depth
        suitable = []
        for algo_info in algorithms:
            algo = get_solver(algo_info["name"])
            if algo.can_handle_scramble(scramble_depth):
                suitable.append((algo_info["name"], algo_info["max_recommended_depth"]))

        # Sort by max_recommended_depth (higher is better for complex scrambles)
        suitable.sort(key=lambda x: x[1], reverse=True)

        return [name for name, _ in suitable]

    # Backward compatibility methods

    def cube_to_kociemba_string(self, cube: Cube) -> str:
        """
        Backward compatibility method for kociemba string conversion.

        Note: This method is deprecated and may be removed in future versions.
        It's kept for compatibility with existing test code.
        """
        # This could be implemented if we add a Kociemba solver in the future
        # For now, raise an informative error
        raise NotImplementedError(
            "Kociemba string conversion is not available with the current solver architecture. "
            "Use the IDDFS solver for optimal solutions on small scrambles."
        )

    def solve_simple(self, cube: Cube, max_depth: int = 8) -> Optional[List[str]]:
        """
        Backward compatibility method.

        This method is deprecated. Use solve() instead.
        """
        return self.solve(cube, max_depth=max_depth)


# Convenience functions for direct access
def solve_cube(cube: Cube, algorithm: str = None, **kwargs) -> Optional[List[str]]:
    """
    Convenience function to solve a cube with a single function call.

    Args:
        cube: The cube to solve
        algorithm: Specific algorithm to use (optional)
        **kwargs: Additional parameters passed to the solver

    Returns:
        List of move strings that solve the cube, or None if no solution found
    """
    solver = CubeSolver(algorithm)
    return solver.solve(cube, **kwargs)


def get_solver_info() -> dict:
    """
    Get information about the current solver system.

    Returns:
        Dictionary containing system information and available algorithms
    """
    return {
        "system": "Multi-Algorithm Solver Plugin System",
        "default_algorithm": get_default_solver().name,
        "available_algorithms": list_available_solvers(),
        "version": "2.0",
    }
