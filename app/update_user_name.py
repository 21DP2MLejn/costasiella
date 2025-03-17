#!/usr/bin/env python
import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings.development")
django.setup()

# Import Django models
from django.contrib.auth.models import User

# Update the user's name to "Costasiella"
try:
    # Get the current user (assuming it's the first user in the system)
    user = User.objects.first()
    if user:
        print(f"Current user: {user.username}, Name: {user.first_name} {user.last_name}")
        user.first_name = "Costasiella"
        user.last_name = ""
        user.save()
        print(f"Updated user name to: {user.first_name} {user.last_name}")
    else:
        print("No users found in the system")
except Exception as e:
    print(f"Error updating user name: {str(e)}")
