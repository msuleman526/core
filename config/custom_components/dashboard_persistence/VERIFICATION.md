# Dashboard Persistence Verification

This document provides steps to verify that the Dashboard Persistence component is working correctly.

## Verifying Installation

1. After installing the component and restarting Home Assistant, check the logs for:
   ```
   Setting up dashboard_persistence component
   Dashboard Persistence component initialized with backup_interval=300s
   ```

2. Verify that the component is loaded in Home Assistant:
   - Go to Developer Tools > Services
   - Search for `dashboard_persistence`
   - You should see `backup_settings` and `restore_settings` services

## Verifying Functionality

### Testing Manual Backup

1. Make some changes to dashboard settings in the UI
2. Go to Developer Tools > Services
3. Call the `dashboard_persistence.backup_settings` service
4. Check the logs for:
   ```
   Backed up settings for X entities
   ```
5. Verify that a notification appears confirming the backup

### Testing Manual Restore

1. Make some additional changes to dashboard settings
2. Go to Developer Tools > Services
3. Call the `dashboard_persistence.restore_settings` service
4. Check the logs for:
   ```
   Restored settings for X entities
   ```
5. Verify that a notification appears confirming the restoration
6. Refresh your browser and confirm that the dashboard shows the settings from before your changes

### Testing Automatic Backup

1. Make changes to one of the tracked settings (e.g., change the 3D plan image)
2. Check the logs for:
   ```
   Tracked entity input_text.dashboard_3d_plan changed, scheduling backup
   Backed up settings for X entities
   ```

### Testing Automatic Restore on Restart

1. Make some changes to dashboard settings
2. Trigger the backup service to save them
3. Restart Home Assistant
4. After restart, check the logs for:
   ```
   Home Assistant started, preparing to restore dashboard settings
   Restoring dashboard settings now
   Restored settings for X entities
   ```
5. Verify that a notification appears confirming the restoration
6. Verify that your dashboard settings are preserved

## Checking Storage File

1. Look for the storage file at:
   ```
   .storage/dashboard_persistence.storage
   ```
2. The file should contain JSON data with entity IDs as keys and their values

## Troubleshooting Common Issues

### Component Not Loading

If you see an error like "Failed to load integration: dashboard_persistence":

1. Check that the `manifest.json` file includes the correct dependencies:
   ```json
   "dependencies": ["input_text"]
   ```
2. Verify that the required input_text entities are defined in your configuration.yaml
3. Check for any import errors in the logs
4. Make sure there are no syntax errors in the __init__.py file
5. Try restarting Home Assistant after making any changes

### Unauthorized Error When Calling Services

If you see an error like "Failed to perform the action dashboard_persistence/backup_settings. Unauthorized":

1. Make sure the component is properly loaded - check the logs for the initialization message
2. Ensure that there are no permission or authorization issues in the component code
3. Verify that the service is properly registered without domain verification restrictions
4. Restart Home Assistant to reload the component completely

### Entities Not Saving or Restoring

If settings are not being saved or restored:

1. Check that the input_text entities exist with max length of 255:
   ```yaml
   input_text:
     dashboard_3d_plan:
       name: 3D Plan Configuration
       initial: "{}"
       max: 255
   ```
2. Verify that the entities have proper values by checking them in the States UI
3. Look for any error messages in the logs related to JSON parsing
4. Verify that the automation for restoring settings on start is correctly defined

### Settings Not Persisting Across Restarts

If settings are lost after a restart:

1. Check that the `restore_dashboard_settings_on_start` automation is defined and working
2. Verify that the delay is long enough (15-20 seconds) to allow Home Assistant to fully initialize
3. Check logs for any errors during the restoration process
4. Manually trigger the `dashboard_persistence.restore_settings` service to see if it works

### Settings Not Syncing Between Clients

If settings are not consistent across different browsers or devices:

1. Verify that none of the frontend components are using localStorage
2. Check that the input_text entities have valid states and are being updated
3. Ensure that clients are loading the latest dashboard settings from the entities
4. Try forcing a refresh in the browser

## Log Level Configuration

To get more detailed debugging information, add this to your configuration.yaml:

```yaml
logger:
  default: info
  logs:
    custom_components.dashboard_persistence: debug
```
