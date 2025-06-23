"""Services for the Custom Dashboard integration."""
import logging
import os
import json
from datetime import datetime

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, CONFIG_PATH

_LOGGER = logging.getLogger(__name__)

async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Custom Dashboard integration."""
    
    @callback
    async def reload_service(call: ServiceCall) -> None:
        """Handle reload service call."""
        _LOGGER.info("Reloading Custom Dashboard configuration")
        
        # Ensure the configuration directory exists
        config_dir = os.path.join(hass.config.config_dir, "www/custom-dashboard")
        os.makedirs(config_dir, exist_ok=True)
        
        # Ensure config file exists with default values if it doesn't
        config_file = os.path.join(hass.config.config_dir, CONFIG_PATH)
        if not os.path.exists(config_file):
            _LOGGER.info("Creating default configuration file")
            with open(config_file, "w") as f:
                json.dump({
                    "image_path": None,
                    "last_updated": None
                }, f, indent=2)
    
    hass.services.async_register(
        DOMAIN, "reload", reload_service
    )

async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Custom Dashboard services."""
    if hass.services.has_service(DOMAIN, "reload"):
        hass.services.async_remove(DOMAIN, "reload")
