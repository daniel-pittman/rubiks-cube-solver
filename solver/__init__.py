"""
Rubik's Cube Solver - A comprehensive 3D cube solving application.

This package provides a complete implementation of a 3x3x3 Rubik's Cube with:
- Core cube representation and move mechanics (solver.core.cube)
- Plugin-based solver system with IDDFS algorithm (solver.core.solver)
- Command-line interface (solver.cli)
- Web interface with 3D visualization (solver.flask_app)
- Desktop application with OpenGL rendering (solver.desktop_app)

The implementation follows standard Western-style cube notation where:
- R (Right), L (Left), U (Up), D (Down), F (Front), B (Back)
- Prime (') denotes counter-clockwise rotation
- 2 denotes 180-degree rotation

Example usage:
    # Using the core cube
    from solver.core.cube import Cube
    cube = Cube()
    cube.execute_move("R U R' U'")

    # Using the solver
    from solver.core.solver import CubeSolver
    solver = CubeSolver()
    solution = solver.solve(cube)
"""

__all__ = []
