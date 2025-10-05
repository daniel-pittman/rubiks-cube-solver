#!/usr/bin/env python3
"""
Base classes and interfaces for Rubik's Cube solvers.

This module defines the abstract base class that all solver algorithms must implement,
along with common utilities and interfaces for the solver plugin system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..cube import Cube


class SolverAlgorithm(ABC):
    """
    Abstract base class for all Rubik's Cube solving algorithms.

    This defines the interface that all solver implementations must follow,
    enabling easy swapping of different solving strategies.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the human-readable name of this solving algorithm."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a brief description of this solving algorithm."""

    @property
    @abstractmethod
    def max_recommended_depth(self) -> int:
        """Return the maximum depth this algorithm can handle efficiently."""

    @abstractmethod
    def solve(self, cube: Cube, **kwargs) -> Optional[List[str]]:
        """
        Solve the given cube using this algorithm.

        Args:
            cube: The cube to solve
            **kwargs: Algorithm-specific parameters

        Returns:
            List of move strings that solve the cube, or None if no solution found
        """

    @abstractmethod
    def can_handle_scramble(self, scramble_depth: int) -> bool:
        """
        Check if this algorithm can efficiently handle a scramble of the given depth.

        Args:
            scramble_depth: The depth/complexity of the scramble

        Returns:
            True if this algorithm is suitable for the given scramble depth
        """

    def get_algorithm_info(self) -> Dict[str, Any]:
        """
        Get information about this algorithm for display/logging purposes.

        Returns:
            Dictionary containing algorithm metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "max_recommended_depth": self.max_recommended_depth,
            "class": self.__class__.__name__,
        }


class SolverRegistry:
    """
    Registry for managing available solving algorithms.

    This class maintains a list of available solver algorithms and provides
    methods to select the best algorithm for a given task.
    """

    def __init__(self):
        """Initialize the solver registry."""
        self._algorithms: Dict[str, SolverAlgorithm] = {}
        self._default_algorithm: Optional[str] = None

    def register_algorithm(
        self, algorithm: SolverAlgorithm, set_as_default: bool = False
    ) -> None:
        """
        Register a new solving algorithm.

        Args:
            algorithm: The algorithm instance to register
            set_as_default: Whether to set this as the default algorithm
        """
        self._algorithms[algorithm.name] = algorithm

        if set_as_default or self._default_algorithm is None:
            self._default_algorithm = algorithm.name

    def get_algorithm(self, name: str) -> Optional[SolverAlgorithm]:
        """
        Get a specific algorithm by name.

        Args:
            name: Name of the algorithm to retrieve

        Returns:
            The algorithm instance, or None if not found
        """
        return self._algorithms.get(name)

    def get_default_algorithm(self) -> Optional[SolverAlgorithm]:
        """
        Get the default algorithm.

        Returns:
            The default algorithm instance, or None if none set
        """
        if self._default_algorithm:
            return self._algorithms.get(self._default_algorithm)
        return None

    def list_algorithms(self) -> List[Dict[str, Any]]:
        """
        List all registered algorithms with their information.

        Returns:
            List of algorithm information dictionaries
        """
        return [algo.get_algorithm_info() for algo in self._algorithms.values()]

    def get_best_algorithm(self, scramble_depth: int = 5) -> Optional[SolverAlgorithm]:
        """
        Get the best algorithm for a given scramble depth.

        Args:
            scramble_depth: The depth/complexity of the scramble

        Returns:
            The most suitable algorithm, or the default if none are optimal
        """
        # Find algorithms that can handle this scramble depth
        suitable_algorithms = [
            algo
            for algo in self._algorithms.values()
            if algo.can_handle_scramble(scramble_depth)
        ]

        if not suitable_algorithms:
            return self.get_default_algorithm()

        # Return the algorithm with the highest max_recommended_depth
        # (assuming more sophisticated algorithms have higher limits)
        return max(suitable_algorithms, key=lambda a: a.max_recommended_depth)

    def clear(self) -> None:
        """Clear all registered algorithms."""
        self._algorithms.clear()
        self._default_algorithm = None


# Global registry instance
_global_registry = SolverRegistry()


def get_solver_registry() -> SolverRegistry:
    """
    Get the global solver registry instance.

    Returns:
        The global SolverRegistry instance
    """
    return _global_registry


def register_solver_algorithm(
    algorithm: SolverAlgorithm, set_as_default: bool = False
) -> None:
    """
    Convenience function to register an algorithm with the global registry.

    Args:
        algorithm: The algorithm to register
        set_as_default: Whether to set this as the default algorithm
    """
    _global_registry.register_algorithm(algorithm, set_as_default)


def get_solver_algorithm(name: str) -> Optional[SolverAlgorithm]:
    """
    Convenience function to get an algorithm from the global registry.

    Args:
        name: Name of the algorithm to retrieve

    Returns:
        The algorithm instance, or None if not found
    """
    return _global_registry.get_algorithm(name)
