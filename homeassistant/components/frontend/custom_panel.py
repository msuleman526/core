"""Register custom-dashboard panel in Home Assistant."""

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.core import HomeAssistant


def setup_custom_panel(hass: HomeAssistant) -> None:
    """Set up custom dashboard panel."""
    async_register_built_in_panel(
        hass,
        component_name="custom-dashboard",
        sidebar_title="Dashboard",
        sidebar_icon="mdi:view-dashboard",
        frontend_url_path="custom-dashboard",
        require_admin=False,
        config=None,
    )
