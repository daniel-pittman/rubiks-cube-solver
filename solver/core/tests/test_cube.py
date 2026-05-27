#!/usr/bin/env python3
"""
Corrected comprehensive movement tests for Rubik's Cube implementation.

These tests verify that each move cycles edges according to standard
Western-style Rubik's cube notation.
"""

# pylint: disable=protected-access,redefined-outer-name  # Tests need internal access

import numpy as np
import pytest

from solver.core.cube import Cube, Face


class TestCorrectMoveBehavior:
    """Test that moves actually do what they should according to cube notation."""

    @pytest.fixture
    def cube(self):
        """Provide a fresh solved cube for each test."""
        return Cube()

    def test_r_move_correct_edge_cycling(self, cube):
        """Test that R move correctly cycles edges between U, F, D, B faces."""
        # Apply some moves to create different edge colors
        cube.execute_move("U")
        cube.execute_move("F")

        # Get face grids before R move
        u_grid = cube._get_face_display_grid(Face.U)
        f_grid = cube._get_face_display_grid(Face.F)
        d_grid = cube._get_face_display_grid(Face.D)
        b_grid = cube._get_face_display_grid(Face.B)

        # Store edges that should cycle during R move
        u_right = u_grid[:, 2].copy()  # U right column
        f_right = f_grid[:, 2].copy()  # F right column
        d_right = d_grid[:, 2].copy()  # D right column
        b_left = b_grid[:, 0].copy()  # B left column (opposite side)

        # Execute R move
        cube.execute_move("R")

        # Get face grids after R move
        u_grid_after = cube._get_face_display_grid(Face.U)
        f_grid_after = cube._get_face_display_grid(Face.F)
        d_grid_after = cube._get_face_display_grid(Face.D)
        b_grid_after = cube._get_face_display_grid(Face.B)

        # R move cycles: F→U→B(reversed)→D→F
        assert np.array_equal(
            u_grid_after[:, 2], f_right
        ), "U right should be old F right"
        assert np.array_equal(
            b_grid_after[:, 0], u_right[::-1]
        ), "B left should be old U right reversed"
        assert np.array_equal(
            d_grid_after[:, 2], b_left[::-1]
        ), "D right should be old B left reversed"
        assert np.array_equal(
            f_grid_after[:, 2], d_right
        ), "F right should be old D right"

    def test_l_move_correct_edge_cycling(self, cube):
        """Test that L move correctly cycles edges between U, B, D, F faces."""
        # Apply some moves to create different edge colors
        cube.execute_move("U")
        cube.execute_move("F")

        # Get face grids before L move
        u_grid = cube._get_face_display_grid(Face.U)
        b_grid = cube._get_face_display_grid(Face.B)
        d_grid = cube._get_face_display_grid(Face.D)
        f_grid = cube._get_face_display_grid(Face.F)

        # Store edges that should cycle during L move
        u_left = u_grid[:, 0].copy()  # U left column
        f_left = f_grid[:, 0].copy()  # F left column
        d_left = d_grid[:, 0].copy()  # D left column
        b_right = b_grid[:, 2].copy()  # B right column (opposite side)

        # Execute L move
        cube.execute_move("L")

        # Get face grids after L move
        u_grid_after = cube._get_face_display_grid(Face.U)
        b_grid_after = cube._get_face_display_grid(Face.B)
        d_grid_after = cube._get_face_display_grid(Face.D)
        f_grid_after = cube._get_face_display_grid(Face.F)

        # L move cycles: U→F, F→D, D→B(reversed), B(reversed)→U
        assert np.array_equal(f_grid_after[:, 0], u_left), "F left should be old U left"
        assert np.array_equal(d_grid_after[:, 0], f_left), "D left should be old F left"
        assert np.array_equal(
            b_grid_after[:, 2], d_left[::-1]
        ), "B right should be old D left reversed"
        assert np.array_equal(
            u_grid_after[:, 0], b_right[::-1]
        ), "U left should be old B right reversed"

    def test_u_move_correct_edge_cycling(self, cube):
        """Test that U move correctly cycles edges between F, R, B, L faces."""
        # Apply some moves to create different edge colors
        cube.execute_move("R")
        cube.execute_move("F")

        # Get face grids before U move
        f_grid = cube._get_face_display_grid(Face.F)
        r_grid = cube._get_face_display_grid(Face.R)
        b_grid = cube._get_face_display_grid(Face.B)
        l_grid = cube._get_face_display_grid(Face.L)

        # Store edges that should cycle during U move
        f_top = f_grid[0, :].copy()  # F top row
        r_top = r_grid[0, :].copy()  # R top row
        b_top = b_grid[0, :].copy()  # B top row
        l_top = l_grid[0, :].copy()  # L top row

        # Execute U move
        cube.execute_move("U")

        # Get face grids after U move
        f_grid_after = cube._get_face_display_grid(Face.F)
        r_grid_after = cube._get_face_display_grid(Face.R)
        b_grid_after = cube._get_face_display_grid(Face.B)
        l_grid_after = cube._get_face_display_grid(Face.L)

        # U move cycles: F→L→B→R→F (all top rows, no reversals)
        assert np.array_equal(l_grid_after[0, :], f_top), "L top should be old F top"
        assert np.array_equal(b_grid_after[0, :], l_top), "B top should be old L top"
        assert np.array_equal(r_grid_after[0, :], b_top), "R top should be old B top"
        assert np.array_equal(f_grid_after[0, :], r_top), "F top should be old R top"

    def test_d_move_correct_edge_cycling(self, cube):
        """Test that D move correctly cycles edges between F, L, B, R faces."""
        # Apply some moves to create different edge colors
        cube.execute_move("R")
        cube.execute_move("F")

        # Get face grids before D move
        f_grid = cube._get_face_display_grid(Face.F)
        l_grid = cube._get_face_display_grid(Face.L)
        b_grid = cube._get_face_display_grid(Face.B)
        r_grid = cube._get_face_display_grid(Face.R)

        # Store edges that should cycle during D move
        f_bottom = f_grid[2, :].copy()  # F bottom row
        l_bottom = l_grid[2, :].copy()  # L bottom row
        b_bottom = b_grid[2, :].copy()  # B bottom row
        r_bottom = r_grid[2, :].copy()  # R bottom row

        # Execute D move
        cube.execute_move("D")

        # Get face grids after D move
        f_grid_after = cube._get_face_display_grid(Face.F)
        l_grid_after = cube._get_face_display_grid(Face.L)
        b_grid_after = cube._get_face_display_grid(Face.B)
        r_grid_after = cube._get_face_display_grid(Face.R)

        # D move cycles: F→R→B→L→F (all bottom rows, no reversals)
        assert np.array_equal(
            r_grid_after[2, :], f_bottom
        ), "R bottom should be old F bottom"
        assert np.array_equal(
            b_grid_after[2, :], r_bottom
        ), "B bottom should be old R bottom"
        assert np.array_equal(
            l_grid_after[2, :], b_bottom
        ), "L bottom should be old B bottom"
        assert np.array_equal(
            f_grid_after[2, :], l_bottom
        ), "F bottom should be old L bottom"

    def test_f_move_correct_edge_cycling(self, cube):
        """Test that F move correctly cycles edges between U, R, D, L faces."""
        # Apply some moves to create different edge colors
        cube.execute_move("R")
        cube.execute_move("U")

        # Get face grids before F move
        u_grid = cube._get_face_display_grid(Face.U)
        r_grid = cube._get_face_display_grid(Face.R)
        d_grid = cube._get_face_display_grid(Face.D)
        l_grid = cube._get_face_display_grid(Face.L)

        # Store edges that should cycle during F move
        u_bottom = u_grid[2, :].copy()  # U bottom row
        r_left = r_grid[:, 0].copy()  # R left column
        d_top = d_grid[0, :].copy()  # D top row
        l_right = l_grid[:, 2].copy()  # L right column

        # Execute F move
        cube.execute_move("F")

        # Get face grids after F move
        u_grid_after = cube._get_face_display_grid(Face.U)
        r_grid_after = cube._get_face_display_grid(Face.R)
        d_grid_after = cube._get_face_display_grid(Face.D)
        l_grid_after = cube._get_face_display_grid(Face.L)

        # F move: U bottom→R left, R left→D top (reversed),
        # D top→L right, L right→U bottom (reversed)
        assert np.array_equal(
            r_grid_after[:, 0], u_bottom
        ), "R left should be old U bottom"
        assert np.array_equal(
            d_grid_after[0, :], r_left[::-1]
        ), "D top should be old R left reversed"
        assert np.array_equal(l_grid_after[:, 2], d_top), "L right should be old D top"
        assert np.array_equal(
            u_grid_after[2, :], l_right[::-1]
        ), "U bottom should be old L right reversed"

    def test_b_move_correct_edge_cycling(self, cube):
        """Test that B move correctly cycles edges between U, R, D, L faces."""
        # Apply some moves to create different edge colors
        cube.execute_move("R")
        cube.execute_move("U")

        # Get face grids before B move
        u_grid = cube._get_face_display_grid(Face.U)
        r_grid = cube._get_face_display_grid(Face.R)
        d_grid = cube._get_face_display_grid(Face.D)
        l_grid = cube._get_face_display_grid(Face.L)

        # Store edges that should cycle during B move
        u_top = u_grid[0, :].copy()  # U top row
        r_right = r_grid[:, 2].copy()  # R right column
        d_bottom = d_grid[2, :].copy()  # D bottom row
        l_left = l_grid[:, 0].copy()  # L left column

        # Execute B move
        cube.execute_move("B")

        # Get face grids after B move
        u_grid_after = cube._get_face_display_grid(Face.U)
        r_grid_after = cube._get_face_display_grid(Face.R)
        d_grid_after = cube._get_face_display_grid(Face.D)
        l_grid_after = cube._get_face_display_grid(Face.L)

        # B move cycles: U top→L left(reversed)→D bottom→R right(reversed)→U top
        assert np.array_equal(
            l_grid_after[:, 0], u_top[::-1]
        ), "L left should be old U top reversed"
        assert np.array_equal(
            d_grid_after[2, :], l_left
        ), "D bottom should be old L left"
        assert np.array_equal(
            r_grid_after[:, 2], d_bottom[::-1]
        ), "R right should be old D bottom reversed"
        assert np.array_equal(
            u_grid_after[0, :], r_right
        ), "U top should be old R right"


class TestMathematicalProperties:
    """Test mathematical group properties of the cube."""

    def test_order_four_property(self):
        """Test that all moves have order 4 (M^4 = I)."""
        cube = Cube()
        moves = ["R", "L", "U", "D", "F", "B"]

        for move in moves:
            cube.reset()
            # Execute move 4 times
            for _ in range(4):
                cube.execute_move(move)
            assert cube.is_solved(), f"{move}^4 should return to solved state"

    def test_inverse_property(self):
        """Test that M followed by M' returns to solved state."""
        cube = Cube()
        moves = ["R", "L", "U", "D", "F", "B"]

        for move in moves:
            cube.reset()
            cube.execute_move(move)
            cube.execute_move(move + "'")
            assert (
                cube.is_solved()
            ), f"{move} followed by {move}' should return to solved state"

    def test_double_move_property(self):
        """Test that M2 followed by M2 returns to solved state."""
        cube = Cube()
        moves = ["R", "L", "U", "D", "F", "B"]

        for move in moves:
            cube.reset()
            cube.execute_move(move + "2")
            cube.execute_move(move + "2")
            assert (
                cube.is_solved()
            ), f"{move}2 followed by {move}2 should return to solved state"


if __name__ == "__main__":
    # Run basic tests
    print("Running corrected cube movement tests...")

    test = TestCorrectMoveBehavior()
    cube = Cube()

    # Test each move
    moves_to_test = [
        ("R", test.test_r_move_correct_edge_cycling),
        ("L", test.test_l_move_correct_edge_cycling),
        ("U", test.test_u_move_correct_edge_cycling),
        ("D", test.test_d_move_correct_edge_cycling),
        ("F", test.test_f_move_correct_edge_cycling),
        ("B", test.test_b_move_correct_edge_cycling),
    ]

    passed = 0
    failed = 0

    for move_name, test_func in moves_to_test:
        cube = Cube()  # Fresh cube for each test
        try:
            test_func(cube)
            print(f"✓ {move_name} move test PASSED")
            passed += 1
        except AssertionError as e:
            print(f"✗ {move_name} move test FAILED: {e}")
            failed += 1

    print(f"\nRESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")

    # Test mathematical properties
    print("\nTesting mathematical properties...")
    math_test = TestMathematicalProperties()

    try:
        math_test.test_order_four_property()
        print("✓ Order-4 property test PASSED")
    except AssertionError as e:
        print(f"✗ Order-4 property test FAILED: {e}")

    try:
        math_test.test_inverse_property()
        print("✓ Inverse property test PASSED")
    except AssertionError as e:
        print(f"✗ Inverse property test FAILED: {e}")

    try:
        math_test.test_double_move_property()
        print("✓ Double move property test PASSED")
    except AssertionError as e:
        print(f"✗ Double move property test FAILED: {e}")
