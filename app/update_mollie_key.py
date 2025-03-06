#!/usr/bin/env python3
"""
Script to update the Mollie API key using SystemSettingDude
"""
import os
import sys
import django

# Set up Django environment
sys.path.append('/opt/backend/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings.development')
django.setup()

from costasiella.dudes.system_setting_dude import SystemSettingDude

def main():
    # Create an instance of SystemSettingDude
    system_setting_dude = SystemSettingDude()
    
    # Set a test API key for Mollie
    # In a real environment, you would get a real test key from Mollie
    test_api_key = "test_stMBnq9xJQhVCJhNUGCJN24zxW2TkD"
    
    # Update the setting
    try:
        current_value = system_setting_dude.get("integration_mollie_api_key")
        print(f"Current Mollie API key: {current_value}")
        
        from costasiella.models import SystemSetting
        
        if SystemSetting.objects.filter(setting="integration_mollie_api_key").exists():
            setting = SystemSetting.objects.get(setting="integration_mollie_api_key")
            setting.value = test_api_key
            setting.save()
            print("Updated existing Mollie API key setting")
        else:
            setting = SystemSetting(
                setting="integration_mollie_api_key",
                value=test_api_key
            )
            setting.save()
            print("Created new Mollie API key setting")
        

        updated_value = system_setting_dude.get("integration_mollie_api_key")
        print(f"Mollie API key updated to: {updated_value}")
        
    except Exception as e:
        print(f"Error updating Mollie API key: {str(e)}")

if __name__ == "__main__":
    main()
