"""
Registry for red team plugins.
"""

from typing import Any, Callable, Dict, List, Optional


class RedTeamPluginRegistry:
    """Registry for red team attack plugins."""

    def __init__(self):
        """Initialize the plugin registry."""
        self._plugins: Dict[str, Callable] = {}
        self._register_default_plugins()

    def _register_default_plugins(self):
        """Register default red team plugins."""
        from .basic import (
            harmful_self_harm_plugin,
            harmful_hate_plugin,
            harmful_violence_plugin,
            politics_plugin,
            competitors_plugin,
            pii_plugin,
        )

        self.register("harmful:self-harm", harmful_self_harm_plugin)
        self.register("harmful:hate", harmful_hate_plugin)
        self.register("harmful:violence", harmful_violence_plugin)
        self.register("politics", politics_plugin)
        self.register("competitors", competitors_plugin)
        self.register("pii", pii_plugin)

    def register(self, plugin_name: str, plugin_func: Callable):
        """Register a red team plugin.

        Args:
            plugin_name: Name of the plugin
            plugin_func: Plugin function that returns attack scenarios
        """
        self._plugins[plugin_name] = plugin_func

    def get_plugin(self, plugin_name: str) -> Optional[Callable]:
        """Get plugin function by name.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin function or None if not found
        """
        return self._plugins.get(plugin_name)

    def list_plugins(self) -> Dict[str, Callable]:
        """List all registered plugins.

        Returns:
            Dictionary of plugin name to function mappings
        """
        return self._plugins.copy()


# Global plugin registry instance
red_team_registry = RedTeamPluginRegistry()


# Convenience functions
def register_plugin(plugin_name: str, plugin_func: Callable):
    """Register a red team plugin globally.

    Args:
        plugin_name: Name of the plugin
        plugin_func: Plugin function
    """
    red_team_registry.register(plugin_name, plugin_func)


def get_plugin(plugin_name: str) -> Optional[Callable]:
    """Get plugin function by name globally.

    Args:
        plugin_name: Name of the plugin

    Returns:
        Plugin function or None if not found
    """
    return red_team_registry.get_plugin(plugin_name)