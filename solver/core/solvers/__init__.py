#!/usr/bin/env python3
"""
Rubik's Cube Solver Algorithms Package.

This package contains various solving algorithms for Rubik's cubes, each implementing
the SolverAlgorithm interface defined in base_solver.py.

Available Solvers:
- IDDFS: Iterative Deepening Depth-First Search (optimal for small scrambles)
- [Future]: CFOP, Roux, Layer-by-Layer, Kociemba integration, etc.

Usage:
    from solver.core.solvers import get_default_solver, get_solver

    # Get the default solver
    solver = get_default_solver()

    # Get a specific solver by name
    iddfs_solver = get_solver("IDDFS")

    # Solve a cube
    solution = solver.solve(cube)
"""

from .base_solver import (
    SolverAlgorithm,
    SolverRegistry,
    get_solver_registry,
    register_solver_algorithm,
)
from .iddfs_solver import IDDFSSolver


# Initialize and register all available solvers
def _initialize_solvers():
    """Initialize and register all available solver algorithms."""
    registry = get_solver_registry()

    # Register IDDFS solver as default
    iddfs = IDDFSSolver()
    registry.register_algorithm(iddfs, set_as_default=True)

    # Future solvers would be registered here:
    # registry.register_algorithm(CFOPSolver())
    # registry.register_algorithm(RouxSolver())
    # registry.register_algorithm(LayerByLayerSolver())


# Initialize solvers on module import
_initialize_solvers()


# Convenience functions for easy access
def get_default_solver() -> SolverAlgorithm:
    """
    Get the default solver algorithm.

    Returns:
        The default solver instance

    Raises:
        RuntimeError: If no default solver is available
    """
    solver = get_solver_registry().get_default_algorithm()
    if solver is None:
        raise RuntimeError("No default solver algorithm is available")
    return solver


def get_solver(name: str) -> SolverAlgorithm:
    """
    Get a specific solver algorithm by name.

    Args:
        name: Name of the solver algorithm

    Returns:
        The solver instance

    Raises:
        ValueError: If the specified solver is not found
    """
    solver = get_solver_registry().get_algorithm(name)
    if solver is None:
        available = [algo["name"] for algo in get_solver_registry().list_algorithms()]
        raise ValueError(f"Solver '{name}' not found. Available solvers: {available}")
    return solver


def get_best_solver(scramble_depth: int = 5) -> SolverAlgorithm:
    """
    Get the best solver for a given scramble complexity.

    Args:
        scramble_depth: Estimated depth/complexity of the scramble

    Returns:
        The most suitable solver instance

    Raises:
        RuntimeError: If no suitable solver is available
    """
    solver = get_solver_registry().get_best_algorithm(scramble_depth)
    if solver is None:
        raise RuntimeError(f"No solver can handle scramble depth {scramble_depth}")
    return solver


def list_available_solvers():
    """
    List all available solver algorithms with their information.

    Returns:
        List of dictionaries containing solver information
    """
    return get_solver_registry().list_algorithms()


# Export the main classes and functions
__all__ = [
    "SolverAlgorithm",
    "SolverRegistry",
    "IDDFSSolver",
    "get_default_solver",
    "get_solver",
    "get_best_solver",
    "list_available_solvers",
    "get_solver_registry",
    "register_solver_algorithm",
]
