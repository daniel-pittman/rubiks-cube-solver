"""
OpenGL Widget for 3D Rubik's Cube Visualization
Uses PySide6 QOpenGLWidget and PyOpenGL for rendering
"""

# pylint: disable=invalid-name,too-many-branches,attribute-defined-outside-init
# pylint: disable=protected-access,reimported,import-outside-toplevel,pointless-statement

# pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin
from OpenGL.GL import *
from OpenGL.GLU import *

# pylint: enable=wildcard-import,unused-wildcard-import,redefined-builtin
# pylint: disable=no-name-in-module
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget

# pylint: enable=no-name-in-module
from solver.core.cube import Color, Face


# pylint: disable=too-many-instance-attributes,broad-exception-caught
class CubeGLWidget(QOpenGLWidget):
    """
    OpenGL widget for rendering 3D Rubik's Cube

    Features:
    - 3D cube rendering with proper colors
    - Mouse rotation controls
    - Smooth animations
    - Western color scheme (White, Yellow, Red, Orange, Green, Blue)
    """

    # Western/WCA Color scheme
    COLORS = {
        "WHITE": (1.0, 1.0, 1.0),
        "YELLOW": (1.0, 0.84, 0.0),
        "RED": (1.0, 0.0, 0.0),
        "ORANGE": (1.0, 0.27, 0.0),  # OrangeRed for distinction from yellow
        "GREEN": (0.0, 1.0, 0.0),
        "BLUE": (0.0, 0.0, 1.0),
        "BLACK": (0.1, 0.1, 0.1),  # Dark gray for cube structure
    }

    def __init__(self, cube, parent=None):
        super().__init__(parent)
        self.cube = cube

        # Rotation angles for view
        self.rotation_x = 30.0
        self.rotation_y = -30.0

        # Mouse interaction
        self.last_mouse_pos = QPoint()
        self.mouse_press_pos = QPoint()
        self.is_dragging = False
        self.drag_threshold = 5  # pixels
        self.pending_click_check = None  # Store click position for face detection
        self.pending_click_button = None  # Store which button was clicked

        # Animation state
        self.animating = False
        self.animation_progress = 0.0
        self.animation_speed = (
            500  # Animation duration in ms (can be changed externally)
        )
        self.animation_start_time = 0
        self.current_move = None
        self.animation_queue = []  # Queue of (move_notation, saved_state) tuples

        # Track previous cube state for animation
        self.animation_cube_state = None  # Cube state during animation
        self.animating_face = None
        self.animation_angle = 0.0
        self.animation_axis = None
        self.animation_clockwise = True

        # Configure OpenGL format
        format = QSurfaceFormat()
        format.setDepthBufferSize(24)
        format.setStencilBufferSize(8)
        format.setVersion(2, 1)
        format.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
        self.setFormat(format)

        # Enable right-click events (disable context menu)
        self.setContextMenuPolicy(Qt.PreventContextMenu)

    def initializeGL(self):
        """Initialize OpenGL context"""
        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        # Enable lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Set up light
        glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 5.0, 5.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])

        # Enable smooth shading
        glShadeModel(GL_SMOOTH)

        # Set background color
        glClearColor(0.94, 0.96, 0.97, 1.0)  # Light gray background

        # Enable antialiasing
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_POLYGON_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)

    def resizeGL(self, width, height):
        """Handle window resize"""
        if height == 0:
            height = 1

        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        aspect = width / height
        gluPerspective(45.0, aspect, 0.1, 50.0)

        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        """Render the scene"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Position camera
        glTranslatef(0.0, 0.0, -8.0)

        # Apply rotations
        glRotatef(self.rotation_x, 1.0, 0.0, 0.0)
        glRotatef(self.rotation_y, 0.0, 1.0, 0.0)

        # Draw the cube
        self.draw_rubiks_cube()

        # Process pending face click detection (must be after rendering)
        if self.pending_click_check is not None:
            print("DEBUG: Processing pending click check")
            face = self.get_clicked_face(
                self.pending_click_check.x(), self.pending_click_check.y()
            )
            print(f"DEBUG: Detected face: {face}")

            if face:
                # Determine if it's a prime move (right-click)
                if self.pending_click_button == Qt.RightButton:
                    move = f"{face}'"
                else:
                    move = face

                print(f"DEBUG: Executing move: {move}")

                # Notify parent to execute the move
                if hasattr(self, "on_face_clicked"):
                    print("DEBUG: Calling on_face_clicked callback")
                    self.on_face_clicked(move)
                else:
                    print("DEBUG: No on_face_clicked callback found!")

            # Clear pending click
            self.pending_click_check = None
            self.pending_click_button = None

    def draw_rubiks_cube(self):
        """Draw the complete Rubik's cube"""
        cubie_size = 0.95  # Slightly smaller for gaps
        gap = 0.05

        # Draw each cubie
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    # Calculate position
                    pos_x = (x - 1) * (cubie_size + gap)
                    pos_y = (y - 1) * (cubie_size + gap)
                    pos_z = (z - 1) * (cubie_size + gap)

                    # Check if this cubie is part of the animating face
                    is_animating_cubie = False
                    if self.animating and self.animating_face:
                        if self.animating_face == "R" and x == 2:
                            is_animating_cubie = True
                        elif self.animating_face == "L" and x == 0:
                            is_animating_cubie = True
                        elif self.animating_face == "U" and y == 2:
                            is_animating_cubie = True
                        elif self.animating_face == "D" and y == 0:
                            is_animating_cubie = True
                        elif self.animating_face == "F" and z == 2:
                            is_animating_cubie = True
                        elif self.animating_face == "B" and z == 0:
                            is_animating_cubie = True

                    glPushMatrix()
                    glTranslatef(pos_x, pos_y, pos_z)

                    # Apply rotation if this cubie is animating
                    if is_animating_cubie:
                        # Move to origin, rotate, move back
                        glTranslatef(-pos_x, -pos_y, -pos_z)

                        if self.animation_axis == "x":
                            glRotatef(self.animation_angle, 1.0, 0.0, 0.0)
                        elif self.animation_axis == "y":
                            glRotatef(self.animation_angle, 0.0, 1.0, 0.0)
                        elif self.animation_axis == "z":
                            glRotatef(self.animation_angle, 0.0, 0.0, 1.0)

                        glTranslatef(pos_x, pos_y, pos_z)

                    self.draw_cubie(x, y, z, cubie_size)
                    glPopMatrix()

    # pylint: disable=too-many-locals
    def draw_cubie(self, x, y, z, size):
        """
        Draw a single cubie with appropriate face colors

        Args:
            x, y, z: Position in cube (0-2)
            size: Size of cubie
        """
        s = size / 2.0

        # Define faces with their positions and normals
        # Coordinate system mapping to Rubik's cube faces:
        # Looking at the cube from standard view (white on top, green in front):
        # +X (right) = Red face (R), -X (left) = Orange face (L)
        # +Y (top) = White face (U), -Y (bottom) = Yellow face (D)
        # +Z (front) = Green face (F), -Z (back) = Blue face (B)
        # Face mapping formulas copied from working web version (cube3d.js)
        # Each face uses the formula: faceIndex = row * 3 + col
        faces = [
            # Right face (+X) - Red (R)
            # Formula: (2-y) * 3 + (2-z)
            {
                "condition": x == 2,
                "vertices": [[s, -s, -s], [s, s, -s], [s, s, s], [s, -s, s]],
                "normal": [1, 0, 0],
                "face": Face.R,
                "row": lambda: 2 - y,
                "col": lambda: 2 - z,
            },
            # Left face (-X) - Orange (L)
            # Formula: (2-y) * 3 + z
            {
                "condition": x == 0,
                "vertices": [[-s, -s, s], [-s, s, s], [-s, s, -s], [-s, -s, -s]],
                "normal": [-1, 0, 0],
                "face": Face.L,
                "row": lambda: 2 - y,
                "col": lambda: z,
            },
            # Top face (+Y) - White (U)
            # Formula: z * 3 + x
            {
                "condition": y == 2,
                "vertices": [[-s, s, -s], [-s, s, s], [s, s, s], [s, s, -s]],
                "normal": [0, 1, 0],
                "face": Face.U,
                "row": lambda: z,
                "col": lambda: x,
            },
            # Bottom face (-Y) - Yellow (D)
            # Formula: (2-z) * 3 + x
            {
                "condition": y == 0,
                "vertices": [[-s, -s, -s], [s, -s, -s], [s, -s, s], [-s, -s, s]],
                "normal": [0, -1, 0],
                "face": Face.D,
                "row": lambda: 2 - z,
                "col": lambda: x,
            },
            # Front face (+Z) - Green (F)
            # Formula: (2-y) * 3 + x
            {
                "condition": z == 2,
                "vertices": [[-s, -s, s], [-s, s, s], [s, s, s], [s, -s, s]],
                "normal": [0, 0, 1],
                "face": Face.F,
                "row": lambda: 2 - y,
                "col": lambda: x,
            },
            # Back face (-Z) - Blue (B)
            # Formula: (2-y) * 3 + (2-x)
            {
                "condition": z == 0,
                "vertices": [[s, -s, -s], [s, s, -s], [-s, s, -s], [-s, -s, -s]],
                "normal": [0, 0, -1],
                "face": Face.B,
                "row": lambda: 2 - y,
                "col": lambda: 2 - x,
            },
        ]

        # Draw each visible face
        glBegin(GL_QUADS)
        for face_data in faces:
            if face_data["condition"]:
                # Get color from cube using display grid (proper orientation)
                face_enum = face_data["face"]
                row = face_data["row"]()
                col = face_data["col"]()

                # Use saved animation state during animation, current state otherwise
                if self.animating and self.animation_cube_state is not None:
                    # During animation: use the saved state (before move)
                    face_grid = self.animation_cube_state[face_enum]
                else:
                    # Not animating: use current state
                    face_grid = self.cube._get_face_display_grid(
                        face_enum
                    )  # pylint: disable=protected-access

                color_enum = face_grid[row, col]
                color_name = Color(color_enum).name
                color = self.COLORS.get(color_name, self.COLORS["BLACK"])

                # Set color and draw face
                glColor3fv(color)
                glNormal3fv(face_data["normal"])
                for vertex in face_data["vertices"]:
                    glVertex3fv(vertex)
        glEnd()

        # Draw black edges for cube structure
        glDisable(GL_LIGHTING)
        glColor3f(0.0, 0.0, 0.0)
        glLineWidth(2.0)

        # Draw outline
        edges = [
            [[-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s]],  # Back
            [[-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s]],  # Front
            [[-s, -s, -s], [-s, -s, s]],  # Bottom-left
            [[s, -s, -s], [s, -s, s]],  # Bottom-right
            [[s, s, -s], [s, s, s]],  # Top-right
            [[-s, s, -s], [-s, s, s]],  # Top-left
        ]

        for edge in edges:
            glBegin(GL_LINE_STRIP if len(edge) > 2 else GL_LINES)
            for vertex in edge:
                glVertex3fv(vertex)
            if len(edge) > 2:
                glVertex3fv(edge[0])  # Close the loop
            glEnd()

        glEnable(GL_LIGHTING)

    def save_cube_state_for_animation(self):
        """Save current cube state before move is executed"""
        from solver.core.cube import Face

        # Save the current state for each face
        self.animation_cube_state = {}
        for face_enum in Face:
            # Store a copy of the display grid
            self.animation_cube_state[face_enum] = self.cube._get_face_display_grid(
                face_enum
            ).copy()  # pylint: disable=protected-access

    def animate_move(self, move_notation, saved_state=None):
        """Animate a cube move with 3D rotation"""
        if self.animating:
            # Queue the move with current cube state saved
            # We need to save state NOW before any more moves execute
            from solver.core.cube import Face

            queued_state = {}
            for face_enum in Face:
                queued_state[face_enum] = self.cube._get_face_display_grid(
                    face_enum
                ).copy()  # pylint: disable=protected-access
            self.animation_queue.append((move_notation, queued_state))
            return

        # Use provided saved state or the one from animation_cube_state
        if saved_state is not None:
            self.animation_cube_state = saved_state
        # If animation_cube_state is already set (from save_cube_state_for_animation), use it

        # Parse move notation
        face = move_notation[0].upper()
        clockwise = "'" not in move_notation
        "2" in move_notation

        # Store animation parameters
        self.animating = True
        self.current_move = move_notation
        self.animating_face = face
        self.animation_clockwise = clockwise
        self.animation_angle = 0.0
        self.animation_start_time = (
            QTimer.currentTime() if hasattr(QTimer, "currentTime") else 0
        )

        # Get rotation axis
        if face in ["R", "L"]:
            self.animation_axis = "x"
        elif face in ["U", "D"]:
            self.animation_axis = "y"
        else:  # F, B
            self.animation_axis = "z"

        # Start animation loop
        self.animate_step()

    def animate_step(self):
        """Perform one step of the animation"""
        if not self.animating:
            return

        # Calculate progress (0 to 1)
        import time

        current_time = time.time() * 1000  # ms
        if not hasattr(self, "_anim_start"):
            self._anim_start = current_time

        elapsed = current_time - self._anim_start
        progress = min(elapsed / self.animation_speed, 1.0)

        # Easing function (ease-out cubic)
        eased_progress = 1 - pow(1 - progress, 3)

        # Calculate target angle (90 degrees or 180 for double moves)
        target_angle = 90.0
        if "2" in self.current_move:
            target_angle = 180.0
        if not self.animation_clockwise:
            target_angle = -target_angle

        # Apply direction corrections for OpenGL coordinate system
        if self.animating_face in ["R", "U", "F"]:
            target_angle = -target_angle

        self.animation_angle = target_angle * eased_progress

        self.update()  # Trigger repaint

        if progress < 1.0:
            # Continue animation
            QTimer.singleShot(16, self.animate_step)  # ~60 FPS
        else:
            # Animation complete
            self.animating = False
            self.animation_angle = 0.0
            self.animating_face = None
            self.animation_cube_state = None  # Clear saved state
            delattr(self, "_anim_start")

            # Process next queued move
            if self.animation_queue:
                next_item = self.animation_queue.pop(0)
                next_move, next_state = next_item
                QTimer.singleShot(50, lambda: self.animate_move(next_move, next_state))

    def update_cube_state(self, animate=True, move_notation=None):
        """Update the OpenGL display with current cube state"""
        if animate and move_notation:
            # Animate the move
            self.animate_move(move_notation)
        else:
            # Immediate update
            self.update()  # Trigger repaint

    def get_clicked_face(self, x, y):
        """Detect which cube face was clicked using ray casting.

        Uses OpenGL depth buffer and unprojection to convert 2D screen coordinates
        into 3D world coordinates, then determines which face was clicked based on
        the dominant axis.

        Args:
            x: Screen X coordinate (pixels)
            y: Screen Y coordinate (pixels)

        Returns:
            str: Face notation (R, L, U, D, F, B) or None if background clicked

        Note:
            Must be called during OpenGL rendering context (in paintGL method).
            The depth buffer must be populated before this method is called.
        """
        # Convert window coordinates to OpenGL coordinates
        # Get current OpenGL matrices and viewport for unprojection
        viewport = glGetIntegerv(GL_VIEWPORT)
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)

        # Flip y coordinate (OpenGL has origin at bottom-left, Qt at top-left)
        window_y = viewport[3] - y
        print(
            f"DEBUG: get_clicked_face: window coords ({x}, {y}) -> OpenGL ({x}, {window_y})"
        )

        # Read depth at click position
        try:
            depth = glReadPixels(x, int(window_y), 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)[
                0
            ][0]
            print(f"DEBUG: Depth at click: {depth}")

            if depth >= 1.0:  # Clicked on background
                print("DEBUG: Clicked on background (depth >= 1.0)")
                return None

            # Unproject to get 3D world coordinates
            from OpenGL.GLU import gluUnProject

            world_coords = gluUnProject(
                x, window_y, depth, modelview, projection, viewport
            )
            print(f"DEBUG: World coords: {world_coords}")

            # Determine which face based on world coordinates
            wx, wy, wz = world_coords

            # Find the dominant axis (which face is closest)
            abs_x, abs_y, abs_z = abs(wx), abs(wy), abs(wz)
            max_val = max(abs_x, abs_y, abs_z)
            print(
                f"DEBUG: Abs coords: x={abs_x:.2f}, y={abs_y:.2f}, z={abs_z:.2f}, max={max_val:.2f}"
            )

            # Map to face based on dominant axis
            if abs_x == max_val:
                face = "R" if wx > 0 else "L"
            elif abs_y == max_val:
                face = "U" if wy > 0 else "D"
            else:
                face = "F" if wz > 0 else "B"

            print(f"DEBUG: Determined face: {face}")
            return face
        except Exception as e:
            print(f"DEBUG: Exception in get_clicked_face: {e}")
            import traceback

            traceback.print_exc()
            return None

    def mousePressEvent(self, event):
        """Handle mouse press for rotation or face click"""
        print(
            f"DEBUG: Mouse press at {event.pos().x()}, {event.pos().y()}, button: {event.button()}"
        )
        self.mouse_press_pos = event.pos()
        self.last_mouse_pos = event.pos()
        self.is_dragging = False

    def mouseMoveEvent(self, event):
        """Handle mouse drag for view rotation"""
        if event.buttons() & Qt.LeftButton or event.buttons() & Qt.RightButton:
            # Calculate distance moved
            dx = event.pos().x() - self.mouse_press_pos.x()
            dy = event.pos().y() - self.mouse_press_pos.y()
            distance = (dx * dx + dy * dy) ** 0.5

            # If moved beyond threshold, it's a drag
            if distance > self.drag_threshold:
                if not self.is_dragging:
                    print(f"DEBUG: Drag detected, distance: {distance:.2f}")
                self.is_dragging = True

            # Update rotation if dragging
            if self.is_dragging:
                dx_delta = event.pos().x() - self.last_mouse_pos.x()
                dy_delta = event.pos().y() - self.last_mouse_pos.y()

                self.rotation_x += dy_delta * 0.5
                self.rotation_y += dx_delta * 0.5

                self.last_mouse_pos = event.pos()
                self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release - detect face click or finish drag"""
        print(
            f"DEBUG: Mouse release, is_dragging: {self.is_dragging}, is_animating: {self.animating}"
        )

        if not self.is_dragging and not self.animating:
            # It's a click, not a drag - schedule face detection for next render
            print(
                f"DEBUG: Scheduling face detection at {event.pos().x()}, {event.pos().y()}"
            )
            self.pending_click_check = event.pos()
            self.pending_click_button = event.button()
            # Trigger a repaint to process the click
            self.update()

        self.is_dragging = False

    def wheelEvent(self, event):
        """Handle mouse wheel for zoom (future feature)"""
        # Could add zoom functionality here
