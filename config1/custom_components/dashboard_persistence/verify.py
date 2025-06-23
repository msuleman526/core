#!/usr/bin/env python3
"""
Helper script to verify dashboard_persistence component.
Run this script from your Home Assistant config directory.
"""

import os
import json
import sys
import socket
import time
import requests
import argparse

def check_file_exists(filename):
    """Check if a file exists."""
    return os.path.isfile(filename)

def check_ha_running():
    """Check if Home Assistant is running."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 8123))
        if result == 0:
            return True
        return False
    except:
        return False
    finally:
        sock.close()

def check_entity_exists(entity_id, token):
    """Check if an entity exists in Home Assistant."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(
            f"http://localhost:8123/api/states/{entity_id}",
            headers=headers
        )
        return response.status_code == 200
    except:
        return False

def check_service_exists(domain, service, token):
    """Check if a service exists in Home Assistant."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(
            f"http://localhost:8123/api/services/{domain}/{service}",
            headers=headers
        )
        return response.status_code == 200
    except:
        return False

def call_service(domain, service, data, token):
    """Call a Home Assistant service."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(
            f"http://localhost:8123/api/services/{domain}/{service}",
            headers=headers,
            json=data
        )
        return response.status_code == 200
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description='Verify dashboard_persistence component')
    parser.add_argument('--token', dest='token', required=True,
                    help='Home Assistant Long-Lived Access Token')
    parser.add_argument('--test', dest='test', action='store_true',
                    help='Run test operations (backup/restore)')

    args = parser.parse_args()
    token = args.token

    print("Checking dashboard_persistence component...")
    
    print("\nChecking files...")
    required_files = [
        "custom_components/dashboard_persistence/__init__.py",
        "custom_components/dashboard_persistence/manifest.json",
        ".storage/dashboard_persistence.storage"
    ]
    
    for filename in required_files:
        exists = check_file_exists(filename)
        print(f"  {filename}: {'✓' if exists else '✗'}")
    
    print("\nChecking Home Assistant status...")
    ha_running = check_ha_running()
    print(f"  Home Assistant running: {'✓' if ha_running else '✗'}")
    
    if not ha_running:
        print("\nERROR: Home Assistant is not running. Start Home Assistant and try again.")
        sys.exit(1)
    
    print("\nChecking entities...")
    entities = [
        "input_text.dashboard_3d_plan",
        "input_text.dashboard_2d_panel",
        "input_text.dashboard_thermostat",
        "input_text.dashboard_lights",
        "input_text.dashboard_covers"
    ]
    
    for entity_id in entities:
        exists = check_entity_exists(entity_id, token)
        print(f"  {entity_id}: {'✓' if exists else '✗'}")
    
    print("\nChecking services...")
    services = [
        ("dashboard_persistence", "backup_settings"),
        ("dashboard_persistence", "restore_settings")
    ]
    
    for domain, service in services:
        exists = check_service_exists(domain, service, token)
        print(f"  {domain}.{service}: {'✓' if exists else '✗'}")
    
    if args.test:
        print("\nTesting backup service...")
        success = call_service("dashboard_persistence", "backup_settings", {}, token)
        print(f"  Backup service call: {'✓' if success else '✗'}")
        
        print("\nTesting restore service...")
        success = call_service("dashboard_persistence", "restore_settings", {}, token)
        print(f"  Restore service call: {'✓' if success else '✗'}")
    
    print("\nVerification complete!")

if __name__ == "__main__":
    main()
