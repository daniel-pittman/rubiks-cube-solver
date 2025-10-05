"""
Desktop application package for Rubik's Cube Solver.

Provides a desktop GUI using PySide6 (Qt6) with OpenGL-based 3D visualization.

Features:
- Hardware-accelerated 3D cube rendering with OpenGL
- Smooth rotation animations with easing
- Interactive face clicking (left-click clockwise, right-click counter-clockwise)
- Camera orbit controls with mouse drag
- Background solver thread for responsive UI
- Solution playback with manual controls

Components:
    CubeGLWidget: OpenGL widget for 3D cube visualization
    RubiksCubeDesktopApp: Main application window (in desktop_app.py)
"""

__all__ = ["CubeGLWidget"]

from solver.desktop.cube_gl_widget import CubeGLWidget
