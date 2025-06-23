"""Custom Dashboard integration for Home Assistant."""
import os
import logging
import json
import voluptuous as vol
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, CONFIG_PATH
from .service import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Custom Dashboard component."""
    hass.http.register_view(CustomDashboardConfigView(hass))
    
    # Ensure the custom_dashboard directory exists
    dashboard_dir = os.path.join(hass.config.config_dir, "www/custom-dashboard")
    os.makedirs(dashboard_dir, exist_ok=True)
    
    # Ensure config file exists
    config_file = os.path.join(hass.config.config_dir, CONFIG_PATH)
    if not os.path.exists(config_file):
        with open(config_file, "w") as f:
            json.dump({"image_path": None, "last_updated": None}, f, indent=2)
    
    # Set up services
    await async_setup_services(hass)
    
    _LOGGER.info("Custom Dashboard integration is set up")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Custom Dashboard from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if hass.data[DOMAIN].get(entry.entry_id):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    # Unload services
    await async_unload_services(hass)
    
    return True

class CustomDashboardConfigView(HomeAssistantView):
    """View to handle Custom Dashboard config requests."""

    url = "/api/custom_dashboard/config"
    name = "api:custom_dashboard:config"
    
    def __init__(self, hass):
        """Initialize the Custom Dashboard config view."""
        self.hass = hass
    
    async def get(self, request):
        """Handle GET requests."""
        config_file = os.path.join(self.hass.config.config_dir, CONFIG_PATH)
        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)
            return self.json(config_data)
        except Exception as err:
            _LOGGER.error("Error reading config file: %s", err)
            return self.json({"error": str(err)}, status_code=500)
    
    async def post(self, request):
        """Handle POST requests to update config."""
        try:
            data = await request.json()
            config_file = os.path.join(self.hass.config.config_dir, CONFIG_PATH)
            
            # Validate the data
            if "image_path" not in data:
                return self.json({"error": "Missing required field: image_path"}, status_code=400)
            
            # Update the file
            import datetime
            data["last_updated"] = datetime.datetime.now().isoformat()
            
            with open(config_file, "w") as f:
                json.dump(data, f, indent=2)
            
            _LOGGER.info("Updated 3D Plan configuration")
            return self.json({"success": True})
        except Exception as err:
            _LOGGER.error("Error updating config file: %s", err)
            return self.json({"error": str(err)}, status_code=500)
