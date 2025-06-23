"""Component for persisting dashboard settings across Home Assistant restarts."""
import logging
import os
import json
import asyncio
import time
from datetime import timedelta
import voluptuous as vol

from homeassistant.core import HomeAssistant, callback
from homeassistant.const import (
    EVENT_HOMEASSISTANT_START,
    EVENT_STATE_CHANGED,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.reload import async_setup_reload_service

_LOGGER = logging.getLogger(__name__)

DOMAIN = "dashboard_persistence"
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.storage"

# How often to perform automatic backups (in seconds)
DEFAULT_BACKUP_INTERVAL = 300  # 5 minutes

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional("enable_backup", default=True): cv.boolean,
        vol.Optional("backup_interval", default=DEFAULT_BACKUP_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=60, max=86400)
        ),
    })
}, extra=vol.ALLOW_EXTRA)

# List of entities to track and persist
TRACKED_ENTITIES = [
    "input_text.dashboard_3d_plan",
    "input_text.dashboard_2d_panel",
    "input_text.dashboard_thermostat", 
    "input_text.dashboard_lights",
    "input_text.dashboard_covers"
]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Dashboard Persistence component."""
    _LOGGER.info("Setting up dashboard_persistence component")
    
    try:
        # Create component configuration
        component_config = config.get(DOMAIN, {})
        enable_backup = component_config.get("enable_backup", True)
        backup_interval = component_config.get("backup_interval", DEFAULT_BACKUP_INTERVAL)
        
        # Create storage directory if it doesn't exist
        storage_dir = hass.config.path(".storage")
        if not os.path.exists(storage_dir):
            try:
                os.makedirs(storage_dir)
                _LOGGER.debug(f"Created storage directory at {storage_dir}")
            except Exception as e:
                _LOGGER.error(f"Failed to create storage directory: {e}")
        
        # Initialize component data
        hass.data[DOMAIN] = {
            "storage_path": hass.config.path(".storage", STORAGE_KEY),
            "last_backup": None,
            "settings": {},
            "entity_listeners": {},
            "config": {
                "enable_backup": enable_backup,
                "backup_interval": backup_interval
            }
        }
        
        # Helper functions for data operations
        async def async_load_from_storage():
            """Load settings from storage file."""
            storage_path = hass.data[DOMAIN]["storage_path"]
            if not os.path.exists(storage_path):
                _LOGGER.debug("Storage file does not exist yet")
                return {}
            
            try:
                with open(storage_path, "r") as file:
                    data = json.load(file)
                    _LOGGER.debug(f"Loaded data from storage: {list(data.keys()) if data else 'empty'}")
                    return data
            except json.JSONDecodeError as e:
                _LOGGER.error(f"Failed to parse storage file - invalid JSON: {e}")
                # Backup corrupted file for debugging
                backup_path = f"{storage_path}.corrupted.{int(time.time())}"
                try:
                    import shutil
                    shutil.copy2(storage_path, backup_path)
                    _LOGGER.warning(f"Backed up corrupted storage file to {backup_path}")
                except Exception as backup_error:
                    _LOGGER.error(f"Failed to backup corrupted storage file: {backup_error}")
                return {}
            except Exception as e:
                _LOGGER.error(f"Failed to load settings from storage: {e}")
                return {}
        
        async def async_save_to_storage(data):
            """Save settings to storage file."""
            storage_path = hass.data[DOMAIN]["storage_path"]
            
            try:
                # First write to a temporary file 
                temp_path = f"{storage_path}.tmp"
                with open(temp_path, "w") as file:
                    json.dump(data, file, indent=2)
                
                # Then rename for atomic update
                os.replace(temp_path, storage_path)
                
                _LOGGER.debug(f"Saved settings to storage: {list(data.keys()) if data else 'empty'}")
                hass.data[DOMAIN]["last_backup"] = time.time()
                return True
            except Exception as e:
                _LOGGER.error(f"Failed to save settings to storage: {e}")
                return False
        
        async def async_backup_settings(call=None):
            """Back up all tracked entity states to storage."""
            settings = {}
            backup_count = 0
            
            # Get current state for all tracked entities
            for entity_id in TRACKED_ENTITIES:
                state = hass.states.get(entity_id)
                if state and state.state not in [STATE_UNKNOWN, STATE_UNAVAILABLE, ""]:
                    try:
                        # Store the entity state
                        settings[entity_id] = state.state
                        backup_count += 1
                        _LOGGER.debug(f"Backed up {entity_id}")
                    except Exception as e:
                        _LOGGER.error(f"Error backing up {entity_id}: {e}")
            
            # Save settings to storage if we have any valid states
            if settings:
                hass.data[DOMAIN]["settings"] = settings
                await async_save_to_storage(settings)
                _LOGGER.info(f"Backed up settings for {backup_count} entities")
                
                # Create a notification that the backup occurred
                try:
                    await hass.services.async_call(
                        "persistent_notification", 
                        "create", 
                        {
                            "title": "Dashboard Settings Backed Up",
                            "message": f"Settings for {backup_count} dashboard entities were backed up at {time.strftime('%H:%M:%S')}",
                            "notification_id": f"{DOMAIN}_backup_notification"
                        }
                    )
                except Exception as e:
                    _LOGGER.error(f"Failed to create backup notification: {e}")
            else:
                _LOGGER.warning("No settings to back up - all entities may be unavailable")
                
                # Create a warning notification
                try:
                    await hass.services.async_call(
                        "persistent_notification", 
                        "create", 
                        {
                            "title": "Dashboard Settings Backup Failed",
                            "message": "Could not back up any dashboard settings - all entities may be unavailable. Check your configuration.yaml for input_text entities.",
                            "notification_id": f"{DOMAIN}_backup_failed_notification"
                        }
                    )
                except Exception as e:
                    _LOGGER.error(f"Failed to create backup failure notification: {e}")
        
        async def async_restore_settings(call=None):
            """Restore settings from storage to entities."""
            _LOGGER.info("Starting settings restoration process")
            
            # Load settings from storage
            settings = await async_load_from_storage()
            
            if not settings:
                _LOGGER.warning("No settings found in storage to restore")
                return
            
            # Restore each entity
            restore_count = 0
            for entity_id, value in settings.items():
                if entity_id in TRACKED_ENTITIES:
                    try:
                        # Check if entity exists
                        if hass.states.get(entity_id) is None:
                            _LOGGER.warning(f"Entity {entity_id} does not exist, cannot restore")
                            continue
                        
                        # Validate that the value is valid JSON to avoid errors
                        try:
                            json.loads(value)
                        except json.JSONDecodeError:
                            _LOGGER.warning(f"Value for {entity_id} is not valid JSON: {value[:50]}...")
                            continue
                        
                        # Set the entity value
                        await hass.services.async_call(
                            "input_text", 
                            "set_value", 
                            {"entity_id": entity_id, "value": value},
                            blocking=True
                        )
                        restore_count += 1
                        _LOGGER.info(f"Restored {entity_id}")
                        
                        # Force entity state update
                        await asyncio.sleep(0.2)  # Small delay to prevent rate limiting
                        await hass.services.async_call(
                            "homeassistant", 
                            "update_entity", 
                            {"entity_id": entity_id},
                            blocking=True
                        )
                    except Exception as e:
                        _LOGGER.error(f"Error restoring {entity_id}: {e}")
            
            if restore_count > 0:
                _LOGGER.info(f"Restored settings for {restore_count} entities")
                
                # Create a notification that the restoration succeeded
                try:
                    await hass.services.async_call(
                        "persistent_notification", 
                        "create", 
                        {
                            "title": "Dashboard Settings Restored",
                            "message": f"Settings for {restore_count} dashboard entities were restored successfully. You may need to refresh your browser.",
                            "notification_id": f"{DOMAIN}_restore_notification"
                        }
                    )
                except Exception as e:
                    _LOGGER.error(f"Failed to create restore notification: {e}")
            else:
                _LOGGER.warning("No entities were restored")
                
                # Create a warning notification
                try:
                    await hass.services.async_call(
                        "persistent_notification", 
                        "create", 
                        {
                            "title": "Dashboard Settings Restoration Failed",
                            "message": "Failed to restore any dashboard settings. Check that your input_text entities exist in configuration.yaml.",
                            "notification_id": f"{DOMAIN}_restore_failed_notification"
                        }
                    )
                except Exception as e:
                    _LOGGER.error(f"Failed to create restore failure notification: {e}")
        
        # Set up state change tracking
        @callback
        def async_state_change_listener(event):
            """Handle tracked entity state changes."""
            entity_id = event.data.get("entity_id")
            new_state = event.data.get("new_state")
            old_state = event.data.get("old_state")
            
            if entity_id in TRACKED_ENTITIES and new_state and new_state.state not in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
                # Skip if the state is not actually changing
                if old_state and old_state.state == new_state.state:
                    _LOGGER.debug(f"Skipping backup for {entity_id} - state unchanged")
                    return
                
                _LOGGER.debug(f"Tracked entity {entity_id} changed to {new_state.state[:30]}..., scheduling backup")
                hass.async_create_task(async_backup_settings())
        
        # Register the event listener for state changes
        @callback
        def async_subscribe_to_state_changes():
            """Subscribe to state changes for tracked entities."""
            if enable_backup:
                _LOGGER.debug("Setting up entity state change listeners")
                hass.bus.async_listen(EVENT_STATE_CHANGED, async_state_change_listener)
        
        # Setup periodic backup
        async def async_periodic_backup(now=None):
            """Run periodic backup."""
            _LOGGER.debug("Running periodic backup")
            await async_backup_settings()
        
        # Register services
        async def async_service_handler(call):
            """Handle service calls."""
            service = call.service
            
            if service == "backup_settings":
                await async_backup_settings()
            elif service == "restore_settings":
                await async_restore_settings()
        
        # Register the services
        hass.services.async_register(
            DOMAIN, "backup_settings", async_service_handler,
            schema=vol.Schema({})
        )
        
        hass.services.async_register(
            DOMAIN, "restore_settings", async_service_handler,
            schema=vol.Schema({})
        )
        
        # Log service registration
        _LOGGER.info(f"Registered services: {DOMAIN}.backup_settings and {DOMAIN}.restore_settings")
        
        # Setup startup restore
        @callback
        def async_startup_restore(event):
            """Restore settings when Home Assistant starts."""
            _LOGGER.info("Home Assistant started, preparing to restore dashboard settings")
            
            # Set a small delay to ensure all entities are loaded
            async def delayed_restore():
                await asyncio.sleep(5)
                _LOGGER.info("Restoring dashboard settings now")
                await async_restore_settings()
                
                # Set up the subscription after restoration (to avoid triggering immediate backup)
                async_subscribe_to_state_changes()
                
                # Start periodic backup after a delay
                if enable_backup:
                    _LOGGER.debug(f"Setting up periodic backup every {backup_interval} seconds")
                    async_track_time_interval(
                        hass, async_periodic_backup, timedelta(seconds=backup_interval)
                    )
            
            hass.async_create_task(delayed_restore())
            
        # Register startup listener
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, async_startup_restore)
        
        # Verify that all required entities exist, log warnings if they don't
        async def async_verify_entities():
            """Verify that all tracked entities exist."""
            missing_entities = []
            
            for entity_id in TRACKED_ENTITIES:
                if hass.states.get(entity_id) is None:
                    missing_entities.append(entity_id)
            
            if missing_entities:
                _LOGGER.warning(f"The following tracked entities are missing: {', '.join(missing_entities)}")
                _LOGGER.warning("Make sure these input_text entities are defined in your configuration.yaml:")
                for entity_id in missing_entities:
                    _LOGGER.warning(f"  {entity_id}: # Add to your configuration.yaml")
                    _LOGGER.warning(f"    name: {entity_id.split('.')[1].replace('_', ' ').title()}")
                    _LOGGER.warning(f"    initial: '{{}}'")
                    _LOGGER.warning(f"    max: 255")
            
            return len(missing_entities) == 0
        
        # Schedule entity verification
        hass.async_create_task(async_verify_entities())
        
        _LOGGER.info(f"Dashboard Persistence component initialized with backup_interval={backup_interval}s")
        return True
        
    except Exception as setup_exception:
        _LOGGER.error(f"Failed to set up dashboard_persistence component: {setup_exception}")
        
        # Create error notification for the user
        try:
            hass.async_create_task(
                hass.services.async_call(
                    "persistent_notification", 
                    "create", 
                    {
                        "title": "Dashboard Persistence Error",
                        "message": f"Failed to set up the dashboard_persistence component: {setup_exception}. Check the logs for more details.",
                        "notification_id": f"{DOMAIN}_setup_error"
                    }
                )
            )
        except Exception as notification_error:
            _LOGGER.error(f"Failed to create error notification: {notification_error}")
        
        return False