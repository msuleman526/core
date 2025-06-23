# Dashboard Persistence Component

The `dashboard_persistence` component provides functionality to persist dashboard settings across Home Assistant restarts and synchronize them across multiple clients.

## Overview

This component manages the persistence and restoration of dashboard settings stored in input_text entities. It ensures that these settings are preserved when Home Assistant restarts and provides a centralized way to manage them.

## Features

- **Automatic backup of dashboard settings** to a storage file
- **Automatic restoration of settings** when Home Assistant starts
- **Periodic backups** to ensure settings are always saved
- **Services** to manually backup and restore settings
- **State change tracking** to automatically backup settings when they change

## Installation

1. Copy the `dashboard_persistence` directory to your Home Assistant config directory under `custom_components/`
2. Add the following to your `configuration.yaml`:

```yaml
# Enable dashboard_persistence component
dashboard_persistence:
  enable_backup: true  # Optional, defaults to true
  backup_interval: 300  # Optional, in seconds, defaults to 300 (5 minutes)

# Required input_text entities for storing dashboard settings
input_text:
  dashboard_lights:
    name: Dashboard Lights Configuration
    initial: "{}"
    max: 255
  
  dashboard_3d_plan:
    name: 3D Plan Configuration
    initial: "{}"
    max: 255
  
  dashboard_2d_panel:
    name: 2D Panel Configuration
    initial: "{}"
    max: 255
  
  dashboard_thermostat:
    name: Thermostat Configuration
    initial: "{}"
    max: 255
  
  dashboard_covers:
    name: Covers Configuration
    initial: "{}"
    max: 255
```

3. Restart Home Assistant using one of these methods:
   - Restart from the UI: Configuration > System > Restart
   - Restart from the command line if running as a service: `sudo systemctl restart home-assistant`
   - If running directly: stop and restart the `hass` command

## Services

The component provides the following services:

- `dashboard_persistence.backup_settings`: Manually backup current settings to storage
- `dashboard_persistence.restore_settings`: Manually restore settings from storage

## Tracked Entities

The component automatically tracks and persists the following entities:

- `input_text.dashboard_3d_plan`
- `input_text.dashboard_2d_panel`
- `input_text.dashboard_thermostat`
- `input_text.dashboard_lights`
- `input_text.dashboard_covers`

## Automations

The component works best with the following automations:

```yaml
- id: 'ensure_input_text_entities_are_loaded'
  alias: 'Ensure input_text entities are loaded after restart'
  description: 'Makes sure input_text entities are properly loaded after Home Assistant restarts'
  trigger:
    platform: homeassistant
    event: start
  action:
    - delay:
        seconds: 10
    - service: input_text.reload
    - delay: 
        seconds: 5
    - service: homeassistant.update_entity
      target:
        entity_id: 
          - input_text.dashboard_3d_plan
          - input_text.dashboard_2d_panel
          - input_text.dashboard_thermostat
          - input_text.dashboard_lights
          - input_text.dashboard_covers

- id: 'restore_dashboard_settings_on_start'
  alias: 'Restore Dashboard Settings on Startup'
  description: 'Restores dashboard settings from storage when Home Assistant starts'
  trigger:
    platform: homeassistant
    event: start
  action:
    - delay:
        seconds: 15
    - service: dashboard_persistence.restore_settings
      data: {}
    - delay:
        seconds: 2
    - service: persistent_notification.create
      data:
        title: "Dashboard Settings Restored"
        message: "Dashboard settings have been restored from storage. Refresh your browser if needed."
```

## Troubleshooting

If you encounter issues with the component:

1. Check that all required input_text entities are defined in your configuration.yaml
2. Verify that the automations for entity loading and settings restoration are present
3. Check the Home Assistant logs for any error messages related to dashboard_persistence
4. Try manually calling the restore_settings service

## Storage Location

Settings are stored in the Home Assistant .storage directory in a file named:
```
.storage/dashboard_persistence.storage
```

## Frontend Integration

The component is designed to work with frontend components that store their settings in the tracked input_text entities. It eliminates the need for browser localStorage and ensures settings are synchronized across all clients.
