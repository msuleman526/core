# Home Assistant Dashboard Persistence Guide

This guide explains how to use the improved settings persistence system for your Home Assistant custom dashboard. The solution ensures your dashboard settings are properly preserved across Home Assistant restarts and consistent across all clients/browsers.

## Components of the Solution

1. **Configuration.yaml Settings**: Properly declares the entities used for settings storage
2. **Custom Component**: A dashboard_persistence component that handles backup and restoration
3. **Automations and Scripts**: For automatic restoration on restart
4. **Enhanced Frontend Code**: For better loading and saving

## How It Works

The solution uses a multi-layered approach:

1. **Primary Storage**: Settings are stored in input_text entities in Home Assistant
2. **Backup Storage**: Settings are also backed up to a file by the dashboard_persistence component
3. **Browser Storage**: As a final fallback, settings are kept in localStorage
4. **Auto-Restoration**: Automations run on Home Assistant startup to restore settings

## Installation Verification

The solution has already been installed in your system. Here's how to verify everything is working properly:

1. **Check Configuration.yaml**:
   - Verify the input_text entities are properly declared
   - Ensure the dashboard_persistence component is enabled

2. **Check Custom Component**:
   - Confirm the dashboard_persistence folder exists in your custom_components directory
   - Verify it contains `__init__.py`, `manifest.json`, and `README.md`

3. **Check Automations and Scripts**:
   - Verify the "Restore Dashboard Settings on Start" automation exists
   - Confirm the restore_dashboard_settings script is present

## Usage

### Setting Up Your Dashboard

Setup your dashboard as normal:
1. Configure your 3D Plan image
2. Select your thermostat entity
3. Choose light entities
4. Configure covers

Your settings will automatically be:
- Saved to the input_text entities
- Backed up by the dashboard_persistence component
- Preserved across Home Assistant restarts

### Manually Backing Up Settings

If you want to manually backup all dashboard settings:

1. Go to Developer Tools → Services
2. Call the `script.backup_dashboard_settings` service
3. This will backup all settings to storage

### Manually Restoring Settings

If your settings are lost for some reason:

1. Go to Developer Tools → Services
2. Call the `script.restore_dashboard_settings` service
3. This will restore settings from history or storage

## Troubleshooting

### Settings Not Persisting

If settings are not being saved across restarts:

1. Check Entity States:
   - Go to Developer Tools → States
   - Search for input_text.dashboard_*
   - Verify they have proper JSON values

2. Check Component Logs:
   - Enable debug logging for the component
   - Look for errors in the logs

3. Manual Reset:
   - Call `script.reset_dashboard_settings` to clear settings
   - Reconfigure your dashboard settings
   - Call `script.backup_dashboard_settings` to force a backup

### Checking Storage Files

The storage files are kept in the Home Assistant .storage directory:

- Dashboard Persistence: `.storage/dashboard_persistence.storage`
- Lovelace Config: `.storage/lovelace*`

## Advanced: Adding New Settings

If you need to add new settings to be persisted:

1. Add a new input_text entity in configuration.yaml:
   ```yaml
   input_text:
     dashboard_new_setting:
       name: New Dashboard Setting
       initial: '{}'
       max: 255
   ```

2. Add the entity to the DASHBOARD_ENTITIES list in the custom component:
   ```python
   DASHBOARD_ENTITIES = [
       # Existing entities...
       "input_text.dashboard_new_setting"
   ]
   ```

3. Update the restore_dashboard_settings script to include the new entity

## Conclusion

This solution provides robust settings persistence for your Home Assistant dashboard. It uses a multi-layered approach to ensure settings are properly preserved across restarts and consistent across all clients/browsers.

If you encounter any issues or have questions, refer to the custom component's README.md file.