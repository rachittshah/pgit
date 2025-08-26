"""
Registry for red team attack strategies.
"""

from typing import Any, Callable, Dict, Optional


class RedTeamStrategyRegistry:
    """Registry for red team attack strategies."""

    def __init__(self):
        """Initialize the strategy registry."""
        self._strategies: Dict[str, Callable] = {}
        self._register_default_strategies()

    def _register_default_strategies(self):
        """Register default red team strategies."""
        from .basic import (
            jailbreak_strategy,
            prompt_injection_strategy,
            user_mischief_strategy,
        )

        self.register("jailbreak", jailbreak_strategy)
        self.register("prompt-injection", prompt_injection_strategy)
        self.register("user-mischief", user_mischief_strategy)

    def register(self, strategy_name: str, strategy_func: Callable):
        """Register a red team strategy.

        Args:
            strategy_name: Name of the strategy
            strategy_func: Strategy function that modifies attack scenarios
        """
        self._strategies[strategy_name] = strategy_func

    def get_strategy(self, strategy_name: str) -> Optional[Callable]:
        """Get strategy function by name.

        Args:
            strategy_name: Name of the strategy

        Returns:
            Strategy function or None if not found
        """
        return self._strategies.get(strategy_name)

    def list_strategies(self) -> Dict[str, Callable]:
        """List all registered strategies.

        Returns:
            Dictionary of strategy name to function mappings
        """
        return self._strategies.copy()


# Global strategy registry instance
strategy_registry = RedTeamStrategyRegistry()


# Convenience functions
def register_strategy(strategy_name: str, strategy_func: Callable):
    """Register a red team strategy globally.

    Args:
        strategy_name: Name of the strategy
        strategy_func: Strategy function
    """
    strategy_registry.register(strategy_name, strategy_func)


def get_strategy(strategy_name: str) -> Optional[Callable]:
    """Get strategy function by name globally.

    Args:
        strategy_name: Name of the strategy

    Returns:
        Strategy function or None if not found
    """
    return strategy_registry.get_strategy(strategy_name)