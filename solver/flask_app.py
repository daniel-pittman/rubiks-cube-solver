#!/usr/bin/env python3
"""
Flask Web Interface for Rubik's Cube Solver.

Provides a professional, mobile-responsive web interface with 3D cube visualization,
real-time move animations, and integrated solving capabilities.

Features:
- Interactive 3D cube with Three.js
- Mobile-first responsive design
- Real-time WebSocket communication
- Step-by-step solving visualization
- Touch and mouse controls
- Professional UI/UX
"""
# pylint: disable=logging-fstring-interpolation,broad-exception-caught
# pylint: disable=import-outside-toplevel,protected-access,too-many-nested-blocks,unused-argument

import logging
from typing import Dict, Optional

import numpy as np
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit

# Use absolute imports when running directly
try:
    from .core.cube import Cube
    from .core.solver import CubeSolver
except ImportError:
    from core.cube import Cube
    from core.solver import CubeSolver

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app with SocketIO
app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
app.config["SECRET_KEY"] = "rubiks-cube-solver-secret-key-2024"
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state - in production, use Redis or database
cube_sessions: Dict[str, Cube] = {}
solver_sessions: Dict[str, CubeSolver] = {}
saved_states: Dict[str, Dict] = {}  # For storing scrambled states before solving
scramble_sequences: Dict[str, list] = {}  # For storing scramble move sequences


class CubeWebAPI:
    """Web API interface for cube operations."""

    @staticmethod
    def create_session(session_id: str) -> Dict:
        """Create a new cube session."""
        cube = Cube()
        solver = CubeSolver()

        cube_sessions[session_id] = cube
        solver_sessions[session_id] = solver

        logger.info(f"Created new session: {session_id}")

        return {
            "session_id": session_id,
            "cube_state": CubeWebAPI._serialize_cube(cube),
            "is_solved": cube.is_solved(),
            "move_history": [],
        }

    @staticmethod
    def get_session(session_id: str) -> Optional[Cube]:
        """Get cube from session."""
        return cube_sessions.get(session_id)

    @staticmethod
    def execute_move(session_id: str, move: str) -> Dict:
        """Execute a move on the cube."""
        cube = CubeWebAPI.get_session(session_id)
        if not cube:
            return {"error": "Session not found"}

        try:
            # Execute the move - it returns None on success, False on failure
            result = cube.execute_move(move)
            if result is False:
                return {"error": f"Invalid move: {move}"}

            return {
                "success": True,
                "move": move,
                "cube_state": CubeWebAPI._serialize_cube(cube),
                "is_solved": cube.is_solved(),
                "move_history": getattr(cube, "move_history", []),
            }
        except Exception as e:
            logger.error(f"Error executing move {move}: {e}")
            return {"error": str(e)}

    @staticmethod
    def scramble_cube(session_id: str, moves: int = 20) -> Dict:
        """Scramble the cube with random moves."""
        cube = CubeWebAPI.get_session(session_id)
        if not cube:
            return {"error": "Session not found"}

        try:
            scramble_moves = cube.scramble(moves)
            # Store scramble sequence for later retrieval
            scramble_sequences[session_id] = scramble_moves
            return {
                "success": True,
                "scramble_moves": scramble_moves,
                "cube_state": CubeWebAPI._serialize_cube(cube),
                "is_solved": cube.is_solved(),
            }
        except Exception as e:
            logger.error(f"Error scrambling cube: {e}")
            return {"error": str(e)}

    @staticmethod
    def solve_cube(
        session_id: str, algorithm: str = "auto", max_depth: int = 8
    ) -> Dict:
        """Solve the cube and return solution steps."""
        cube = CubeWebAPI.get_session(session_id)
        solver = solver_sessions.get(session_id)

        if not cube or not solver:
            return {"error": "Session not found"}

        if cube.is_solved():
            return {
                "success": True,
                "solution": [],
                "message": "Cube is already solved!",
            }

        try:
            # Save the current (scrambled) state before solving
            saved_states[session_id] = cube.save_state()

            # Handle 'auto' algorithm selection
            if algorithm == "auto":
                algorithm = None  # Let solver auto-select

            # Get solution from solver
            solution = solver.solve(cube, algorithm=algorithm, max_depth=max_depth)

            if solution is None:
                return {"error": "No solution found within depth limit"}

            return {
                "success": True,
                "solution": solution,
                "algorithm_used": algorithm or "auto",
                "solution_length": len(solution),
            }
        except Exception as e:
            logger.error(f"Error solving cube: {e}")
            return {"error": str(e)}

    @staticmethod
    def reset_cube(session_id: str) -> Dict:
        """Reset cube to solved state."""
        cube = CubeWebAPI.get_session(session_id)
        if not cube:
            return {"error": "Session not found"}

        # Recreate cube in solved state
        new_cube = Cube()
        cube_sessions[session_id] = new_cube
        # Clear saved state
        saved_states.pop(session_id, None)

        return {
            "success": True,
            "cube_state": CubeWebAPI._serialize_cube(new_cube),
            "is_solved": True,
        }

    @staticmethod
    def restore_scrambled_state(session_id: str) -> Dict:
        """Restore the cube to its last scrambled state (before solution was applied)."""
        cube = CubeWebAPI.get_session(session_id)
        if not cube:
            return {"error": "Session not found"}

        saved_state = saved_states.get(session_id)
        if not saved_state:
            return {"error": "No saved scrambled state found"}

        try:
            cube.restore_state(saved_state)
            return {
                "success": True,
                "cube_state": CubeWebAPI._serialize_cube(cube),
                "is_solved": cube.is_solved(),
                "move_history": cube.move_history,
            }
        except Exception as e:
            logger.error(f"Error restoring scrambled state: {e}")
            return {"error": str(e)}

    @staticmethod
    def _serialize_cube(cube: Cube) -> Dict:
        """Convert cube state to JSON-serializable format for frontend."""
        try:
            from .core.cube import Face
        except ImportError:
            from core.cube import Face

        # Create a simplified representation for Three.js
        faces = {}

        # Get the actual cube state using the display method
        try:
            for face_enum in Face:
                face_name = (
                    face_enum.name
                )  # Use name ('U', 'D', etc.) not value (0, 1, etc.)
                face_grid = cube._get_face_display_grid(face_enum)

                # Flatten the grid and extract color names
                face_colors = []
                for row in face_grid:
                    for color_value in row:
                        # Handle integer values from numpy array
                        if isinstance(color_value, (int, np.integer)):
                            # Map integer to Color enum name
                            try:
                                from .core.cube import Color
                            except ImportError:
                                from core.cube import Color
                            color_name = Color(color_value).name
                            face_colors.append(color_name)
                        elif hasattr(color_value, "name"):
                            face_colors.append(color_value.name)
                        elif isinstance(color_value, str):
                            # Map single character colors to full names
                            color_map = {
                                "W": "WHITE",
                                "Y": "YELLOW",
                                "R": "RED",
                                "O": "ORANGE",
                                "G": "GREEN",
                                "B": "BLUE",
                                "?": "WHITE",  # Default fallback
                            }
                            face_colors.append(color_map.get(color_value, "WHITE"))
                        else:
                            face_colors.append("WHITE")  # Fallback

                faces[face_name] = face_colors

        except Exception as e:
            # Fallback to solved state if extraction fails
            logger.warning(f"Failed to extract cube state: {e}, using solved state")
            solved_colors = {
                "U": "WHITE",
                "D": "YELLOW",
                "R": "RED",  # Right face is Red in Western scheme
                "L": "ORANGE",  # Left face is Orange in Western scheme
                "F": "GREEN",  # Front face is Green in Western scheme
                "B": "BLUE",  # Back face is Blue in Western scheme
            }
            for face_enum in Face:
                face_name = face_enum.name  # Use name not value
                faces[face_name] = [solved_colors[face_name]] * 9

        return {"faces": faces, "size": cube.N, "solved": cube.is_solved()}


# Flask Routes
@app.route("/")
def index():
    """Main web interface."""
    return render_template("index.html")


@app.route("/api/session", methods=["POST"])
def create_session():
    """Create a new cube session."""
    session_id = request.json.get("session_id", "default")
    result = CubeWebAPI.create_session(session_id)
    return jsonify(result)


@app.route("/api/move", methods=["POST"])
def execute_move():
    """Execute a move on the cube."""
    data = request.json
    session_id = data.get("session_id", "default")
    move = data.get("move")

    if not move:
        return jsonify({"error": "Move is required"}), 400

    result = CubeWebAPI.execute_move(session_id, move)
    return jsonify(result)


@app.route("/api/scramble", methods=["POST"])
def scramble():
    """Scramble the cube."""
    data = request.json or {}
    session_id = data.get("session_id", "default")
    moves = data.get("moves", 20)

    result = CubeWebAPI.scramble_cube(session_id, moves)
    return jsonify(result)


@app.route("/api/solve", methods=["POST"])
def solve():
    """Solve the cube."""
    data = request.json or {}
    session_id = data.get("session_id", "default")
    algorithm = data.get("algorithm", "auto")
    max_depth = data.get("max_depth", 8)

    result = CubeWebAPI.solve_cube(session_id, algorithm, max_depth)
    return jsonify(result)


@app.route("/api/reset", methods=["POST"])
def reset():
    """Reset cube to solved state."""
    data = request.json or {}
    session_id = data.get("session_id", "default")

    result = CubeWebAPI.reset_cube(session_id)
    return jsonify(result)


@app.route("/api/algorithms", methods=["GET"])
def get_algorithms():
    """Get available solving algorithms."""
    try:
        solver = CubeSolver()
        algorithms = solver.list_algorithms()

        return jsonify(
            {"algorithms": algorithms}  # algorithms is already a list of dicts
        )
    except Exception as e:
        logger.error(f"Error getting algorithms: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/scramble_sequence", methods=["POST"])
def get_scramble_sequence():
    """Get the scramble sequence for the current session."""
    data = request.json or {}
    session_id = data.get("session_id", "default")

    scramble_seq = scramble_sequences.get(session_id, [])
    if not scramble_seq:
        return jsonify({"scramble": [], "message": "No scramble recorded"}), 200

    return jsonify({"scramble": scramble_seq, "scramble_text": " ".join(scramble_seq)})


# WebSocket Events
@socketio.on("connect")
def handle_connect(auth=None):
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")

    # Create default session for this client
    result = CubeWebAPI.create_session(request.sid)
    emit("session_created", result)


@socketio.on("disconnect")
def handle_disconnect(auth=None):
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")

    # Clean up session
    cube_sessions.pop(request.sid, None)
    solver_sessions.pop(request.sid, None)
    saved_states.pop(request.sid, None)


@socketio.on("execute_move")
def handle_move(data):
    """Handle real-time move execution."""
    move = data.get("move")
    if not move:
        emit("error", {"message": "Move is required"})
        return

    result = CubeWebAPI.execute_move(request.sid, move)
    emit("move_executed", result)


@socketio.on("scramble")
def handle_scramble(data):
    """Handle real-time scrambling."""
    moves = data.get("moves", 20)
    result = CubeWebAPI.scramble_cube(request.sid, moves)
    emit("cube_scrambled", result)


@socketio.on("solve")
def handle_solve(data):
    """Handle real-time solving."""
    algorithm = data.get("algorithm", "auto")
    max_depth = data.get("max_depth", 8)
    step_by_step = data.get("step_by_step", False)

    result = CubeWebAPI.solve_cube(request.sid, algorithm, max_depth)

    if result.get("success") and step_by_step:
        # Send solution steps one by one
        solution = result.get("solution", [])
        emit(
            "solve_started",
            {"total_moves": len(solution), "algorithm": result.get("algorithm_used")},
        )

        # Execute moves step by step
        for i, move in enumerate(solution):
            move_result = CubeWebAPI.execute_move(request.sid, move)
            emit(
                "solve_step",
                {
                    "step": i + 1,
                    "total_steps": len(solution),
                    "move": move,
                    "cube_state": move_result.get("cube_state"),
                    "is_solved": move_result.get("is_solved"),
                },
            )

        emit("solve_completed", {"success": True})
    else:
        emit("solve_result", result)


@socketio.on("reset")
def handle_reset():
    """Handle real-time reset."""
    result = CubeWebAPI.reset_cube(request.sid)
    emit("cube_reset", result)


@socketio.on("restore_scrambled")
def handle_restore_scrambled():
    """Handle restoring scrambled state."""
    result = CubeWebAPI.restore_scrambled_state(request.sid)
    emit("scrambled_state_restored", result)


def main():
    """Run the Flask development server."""
    logger.info("Starting Rubik's Cube Web Interface...")

    # Suppress Werkzeug warnings for development
    import warnings

    warnings.filterwarnings("ignore", message=".*Werkzeug.*production.*")

    try:
        # Try the modern approach first
        socketio.run(
            app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True
        )
    except (TypeError, RuntimeError) as e:
        logger.warning(f"Primary startup method failed: {e}")
        try:
            # Alternative approach - use regular Flask run with SocketIO
            logger.info("Trying alternative startup method...")
            app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
        except Exception as e2:
            logger.error(f"Alternative startup failed: {e2}")
            # Final fallback - basic Flask without debug mode
            logger.info("Using basic Flask server...")
            socketio.run(app, host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
