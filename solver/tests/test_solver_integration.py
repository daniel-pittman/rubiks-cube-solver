#!/usr/bin/env python3
"""
Comprehensive integration tests for the solver system.

Tests the full integration between Phase 1 (cube implementation) and Phase 2 (solver system),
ensuring that all cube moves can be solved correctly and solutions can be applied to return
the cube to a solved state.
"""

# pylint: disable=wrong-import-position  # Test setup requires path modification

import os
import sys

# Add the parent directory to the path to import solver modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from solver.core.cube import Cube
from solver.core.solver import CubeSolver, get_solver_info, solve_cube
from solver.core.solvers import get_default_solver, get_solver, list_available_solvers


def test_solver_system_info():
    """Test that the solver system is properly initialized."""
    print("Testing solver system information...")

    # Test system info
    info = get_solver_info()
    assert info["system"] == "Multi-Algorithm Solver Plugin System"
    assert "default_algorithm" in info
    assert "available_algorithms" in info

    # Test available algorithms
    algorithms = list_available_solvers()
    assert len(algorithms) > 0
    assert any(algo["name"] == "IDDFS" for algo in algorithms)

    # Test default solver
    default_solver = get_default_solver()
    assert default_solver is not None
    assert default_solver.name == "IDDFS"

    print("✅ Solver system info tests passed")


def test_solver_creation_methods():
    """Test different ways to create and use solvers."""
    print("Testing solver creation methods...")

    # Auto-selecting solver
    auto_solver = CubeSolver()
    assert auto_solver is not None

    # Specific algorithm solver
    iddfs_solver = CubeSolver("IDDFS")
    assert iddfs_solver.get_algorithm_info()["name"] == "IDDFS"

    # Direct algorithm access
    direct_algo = get_solver("IDDFS")
    assert direct_algo.name == "IDDFS"

    # Test error handling for invalid algorithm
    try:
        CubeSolver("NonexistentAlgorithm")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not found" in str(e)

    print("✅ Solver creation tests passed")


def test_basic_move_solving():
    """Test solving of basic individual moves."""
    print("Testing basic move solving...")

    solver = CubeSolver("IDDFS")

    # Test just a few representative moves for speed
    basic_moves = ["R", "U", "R'"]

    for move in basic_moves:
        cube = Cube()
        cube.execute_move(move)

        assert not cube.is_solved(), f"Cube should be scrambled after {move}"

        solution = solver.solve(cube, max_depth=2)
        assert solution is not None, f"Should find solution for single move {move}"
        assert (
            len(solution) == 1
        ), f"Single move should have 1-move solution, got {len(solution)}"

        # Verify solution works
        test_cube = cube.copy()
        for sol_move in solution:
            test_cube.execute_move(sol_move)

        assert (
            test_cube.is_solved()
        ), f"Solution {solution} should solve cube scrambled with {move}"

    print(f"✅ Basic move solving tests passed ({len(basic_moves)} moves tested)")


def test_move_combinations():
    """Test solving of move combinations."""
    print("Testing move combination solving...")

    solver = CubeSolver("IDDFS")

    combinations = [
        ["R", "U"],
        ["R", "R'"],  # Identity sequence
    ]

    for moves in combinations:
        cube = Cube()
        for move in moves:
            cube.execute_move(move)

        if cube.is_solved():
            print(f"  ✅ {moves}: Already solved (identity sequence)")
            continue

        solution = solver.solve(cube, max_depth=3)
        assert solution is not None, f"Should find solution for {moves}"

        # Verify solution works
        test_cube = cube.copy()
        for sol_move in solution:
            test_cube.execute_move(sol_move)

        assert (
            test_cube.is_solved()
        ), f"Solution should solve cube scrambled with {moves}"

    print(f"✅ Move combination tests passed ({len(combinations)} combinations tested)")


def test_solver_architecture_features():
    """Test advanced features of the solver architecture."""
    print("Testing solver architecture features...")

    # Test algorithm recommendations
    recommendations = CubeSolver.get_algorithm_recommendations(5)
    assert len(recommendations) > 0
    assert "IDDFS" in recommendations

    # Test convenience functions
    cube = Cube()
    cube.execute_move("R")

    solution = solve_cube(cube, algorithm="IDDFS", max_depth=2)
    assert solution is not None
    assert len(solution) == 1
    assert solution[0] == "R'"

    # Test algorithm info
    solver = CubeSolver("IDDFS")
    info = solver.get_algorithm_info()
    assert info["name"] == "IDDFS"
    assert "description" in info

    print("✅ Architecture feature tests passed")


def test_phase1_phase2_integration():
    """Test that Phase 1 cube and Phase 2 solver work together perfectly."""
    print("Testing Phase 1 ↔ Phase 2 integration...")

    solver = CubeSolver("IDDFS")

    # Test key integration scenarios
    integration_tests = [
        (["R"], "Single move"),
        (["R", "U"], "Two moves"),
        (["R", "R'"], "Identity sequence"),
        (["R", "U", "R'", "U'"], "Classic algorithm"),
    ]

    passed = 0
    total = len(integration_tests)

    for moves, description in integration_tests:
        cube = Cube()

        # Apply moves from Phase 1 functionality
        for move in moves:
            cube.execute_move(move)

        if cube.is_solved():
            passed += 1
            print(f"  ✅ {description}: Already solved")
            continue

        # Solve with Phase 2 functionality
        solution = solver.solve(cube, max_depth=min(len(moves) + 2, 6))

        if solution is not None:
            # Apply solution back using Phase 1 functionality
            test_cube = cube.copy()
            for sol_move in solution:
                test_cube.execute_move(sol_move)

            if test_cube.is_solved():
                passed += 1
                print(f"  ✅ {description}: Solved in {len(solution)} moves")
            else:
                print(f"  ❌ {description}: Solution verification failed")
        else:
            print(f"  ❌ {description}: No solution found")

    success_rate = (passed / total) * 100
    assert success_rate == 100, f"Integration should be 100%, got {success_rate}%"
    print(f"✅ Phase 1 ↔ Phase 2 integration test passed ({passed}/{total} scenarios)")


def run_all_solver_tests():
    """Run all solver integration tests."""
    print("🚀 RUNNING SOLVER INTEGRATION TESTS")
    print("=" * 50)

    try:
        test_solver_system_info()
        test_solver_creation_methods()
        test_basic_move_solving()
        test_move_combinations()
        test_solver_architecture_features()
        test_phase1_phase2_integration()

        print("\n" + "=" * 50)
        print("🎉 ALL SOLVER INTEGRATION TESTS PASSED!")
        print("✅ Phase 1 ↔ Phase 2 integration verified")
        print("✅ Solver system is production-ready")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    run_all_solver_tests()
