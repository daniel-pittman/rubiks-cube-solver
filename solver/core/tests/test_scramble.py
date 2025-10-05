"""
Unit tests for cube scramble functionality.

Tests ensure that scramble:
1. Produces valid cube states
2. Maintains correct color counts
3. Keeps centers fixed
4. Is fully reversible
5. Generates random sequences
"""

from typing import Dict

import numpy as np

from solver.core.cube import Color, Cube, Face


class TestScrambleValidity:
    """Test that scramble produces valid cube states."""

    def test_scramble_maintains_color_count(self):
        """Test that scrambled cube has exactly 9 stickers of each color."""
        cube = Cube()

        # Test with different scramble lengths
        for num_moves in [10, 20, 50]:
            cube = Cube()  # Reset to solved
            cube.scramble(num_moves)

            # Count colors across all faces
            color_counts = self._count_colors(cube)

            # Each color should appear exactly 9 times
            for color in Color:
                assert color_counts[color] == 9, (
                    f"After {num_moves} moves, {color.name} appears "
                    f"{color_counts[color]} times instead of 9"
                )

    def test_scramble_keeps_centers_fixed(self):
        """Test that center pieces remain in their original positions."""
        cube = Cube()

        # Expected center colors for each face
        expected_centers = {
            Face.U: Color.WHITE,
            Face.D: Color.YELLOW,
            Face.R: Color.RED,
            Face.L: Color.ORANGE,
            Face.F: Color.GREEN,
            Face.B: Color.BLUE,
        }

        # Scramble the cube
        cube.scramble(30)

        # Check that each center is still the correct color
        for face, expected_color in expected_centers.items():
            center_color = cube.stickers[face, 1, 1]
            assert center_color == expected_color, (
                f"Center of {face.name} is {Color(center_color).name} "
                f"instead of {expected_color.name}"
            )

    def test_scramble_is_reversible(self):
        """Test that applying inverse moves returns cube to solved state."""
        cube = Cube()

        # Scramble and save the moves
        moves = cube.scramble(25)

        # Apply inverse moves in reverse order
        for move in reversed(moves):
            if "'" in move:
                inverse = move[0]  # Remove the prime
            else:
                inverse = move + "'"  # Add prime
            cube.execute_move(inverse)

        assert cube.is_solved(), "Cube should be solved after reversing scramble moves"

    def test_scramble_creates_unsolved_state(self):
        """Test that scramble actually scrambles the cube."""
        cube = Cube()

        # A scramble of reasonable length should create an unsolved state
        cube.scramble(20)

        assert not cube.is_solved(), "Cube should not be solved after scrambling"

    def test_empty_scramble_leaves_cube_solved(self):
        """Test that scramble with 0 moves leaves cube solved."""
        cube = Cube()
        moves = cube.scramble(0)

        assert len(moves) == 0, "Should return empty move list"
        assert cube.is_solved(), "Cube should remain solved with 0 scramble moves"

    def test_scramble_returns_move_list(self):
        """Test that scramble returns the list of moves applied."""
        cube = Cube()
        num_moves = 15
        moves = cube.scramble(num_moves)

        assert len(moves) == num_moves, f"Should return {num_moves} moves"

        # All moves should be valid
        valid_moves = {"R", "R'", "L", "L'", "U", "U'", "D", "D'", "F", "F'", "B", "B'"}
        for move in moves:
            assert move in valid_moves, f"Invalid move in scramble: {move}"

    def _count_colors(self, cube: Cube) -> Dict[Color, int]:
        """Count occurrences of each color in the cube."""
        color_counts = {color: 0 for color in Color}

        for face in range(6):
            for row in range(3):
                for col in range(3):
                    color = cube.stickers[face, row, col]
                    color_counts[color] += 1

        return color_counts


class TestScrambleRandomness:
    """Test that scramble generates random sequences."""

    def test_scrambles_are_different(self):
        """Test that multiple scrambles produce different sequences."""
        sequences = []

        # Generate several scrambles
        for _ in range(10):
            cube = Cube()
            moves = cube.scramble(20)
            sequences.append(tuple(moves))  # Convert to tuple for set comparison

        # At least 8 out of 10 should be unique (allowing for rare duplicates)
        unique_sequences = set(sequences)
        assert (
            len(unique_sequences) >= 8
        ), f"Only {len(unique_sequences)} unique scrambles out of 10"

    def test_scramble_uses_all_move_types(self):
        """Test that scramble uses a variety of moves over multiple scrambles."""
        all_moves_used = set()

        # Generate multiple scrambles to collect move types
        for _ in range(20):
            cube = Cube()
            moves = cube.scramble(20)
            all_moves_used.update(moves)

        # Should use most move types (at least 10 out of 12)
        assert (
            len(all_moves_used) >= 10
        ), f"Only using {len(all_moves_used)} different move types"


class TestScrambleEdgeCases:
    """Test edge cases and error conditions."""

    def test_large_scramble(self):
        """Test that large scrambles work correctly."""
        cube = Cube()
        moves = cube.scramble(100)

        assert len(moves) == 100, "Should handle large scramble counts"

        # Should still maintain valid state
        color_counts = self._count_colors(cube)
        for color in Color:
            assert color_counts[color] == 9

    def test_multiple_scrambles_on_same_cube(self):
        """Test applying scramble multiple times to the same cube."""
        cube = Cube()

        # First scramble
        moves1 = cube.scramble(10)
        assert len(moves1) == 10

        # Second scramble (should add to the existing scrambled state)
        moves2 = cube.scramble(10)
        assert len(moves2) == 10

        # Cube should still be valid
        color_counts = self._count_colors(cube)
        for color in Color:
            assert color_counts[color] == 9

    def test_scramble_with_negative_moves(self):
        """Test that negative move count is handled properly."""
        cube = Cube()

        # Should either raise an error or treat as 0
        # Current implementation doesn't validate, so it treats negative as 0
        moves = cube.scramble(-5)
        assert len(moves) == 0, "Negative moves should result in no scramble"

    def _count_colors(self, cube: Cube) -> Dict[Color, int]:
        """Count occurrences of each color in the cube."""
        color_counts = {color: 0 for color in Color}

        for face in range(6):
            for row in range(3):
                for col in range(3):
                    color = cube.stickers[face, row, col]
                    color_counts[color] += 1

        return color_counts


class TestScramblePerformance:
    """Test performance-related aspects of scramble."""

    def test_scramble_move_sequence_validity(self):
        """Test that the scramble sequence can be executed without errors."""
        cube = Cube()

        # Get scramble moves
        moves = cube.scramble(30)

        # Create a fresh cube and apply the same moves
        cube2 = Cube()
        for move in moves:
            # This should not raise any exceptions
            cube2.execute_move(move)

        # Both cubes should be in the same state
        assert np.array_equal(
            cube.stickers, cube2.stickers
        ), "Applying scramble moves individually should produce same result"

    def test_scramble_preserves_cube_structure(self):
        """Test that scramble doesn't break the cube's internal structure."""
        cube = Cube()
        cube.scramble(50)

        # Check that the stickers array has the correct shape
        assert cube.stickers.shape == (6, 3, 3), "Stickers array shape corrupted"

        # Check that all values are valid colors
        for face in range(6):
            for row in range(3):
                for col in range(3):
                    color_value = cube.stickers[face, row, col]
                    assert color_value in [c.value for c in Color], (
                        f"Invalid color value {color_value} at position "
                        f"[{face},{row},{col}]"
                    )
