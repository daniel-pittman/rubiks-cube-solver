"""
Core Rubik's Cube implementation module.

This module provides the fundamental building blocks for working with a 3x3x3 Rubik's Cube:

Classes:
    Face: Enum representing the six faces of the cube (R, L, U, D, F, B)
    Color: Enum representing the six colors (Red, Orange, White, Yellow, Green, Blue)
    Cube: Main cube class with move execution and state management
    CubeSolver: High-level solver interface with plugin system

The cube representation uses a sticker-based model where each face is represented
as a 3x3 grid of color values. All moves follow standard Western notation.

Example:
    from solver.core import Cube, CubeSolver

    # Create and manipulate cube
    cube = Cube()
    cube.execute_move("R U R' U'")

    # Solve the cube
    solver = CubeSolver()
    solution = solver.solve(cube, max_depth=5)
"""

from .cube import Color, Cube, Face
from .solver import CubeSolver

__all__ = ["Cube", "Face", "Color", "CubeSolver"]
