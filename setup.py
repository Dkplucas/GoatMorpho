#!/usr/bin/env python
"""
Setup script for GoatMorpho project
Run this after installing requirements.txt
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.contrib.auth.models import User

def setup_project():
    """Setup the GoatMorpho project"""
    
    print("🐐 GoatMorpho Setup Script")
    print("=" * 40)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goat_morpho.settings')
    
    # Setup Django
    django.setup()
    
    print("1. Creating database migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    
    print("2. Running migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    print("3. Creating media directories...")
    media_dirs = [
        'media',
        'media/goat_images',
        'media/goat_images/original',
        'media/goat_images/processed'
    ]
    
    for dir_path in media_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"   Created: {dir_path}")
    
    print("4. Collecting static files...")
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    
    print("\n5. Creating superuser...")
    print("   Please provide admin credentials:")
    
    try:
        username = input("   Username: ")
        email = input("   Email: ")
        password = input("   Password: ")
        
        if User.objects.filter(username=username).exists():
            print(f"   User '{username}' already exists!")
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            print(f"   Superuser '{username}' created successfully!")
    
    except KeyboardInterrupt:
        print("\n   Skipping superuser creation...")
    
    print("\n✅ Setup Complete!")
    print("\nNext steps:")
    print("1. Run: python manage.py runserver")
    print("2. Open: http://127.0.0.1:8000/")
    print("3. Admin: http://127.0.0.1:8000/admin/")
    print("\nUpload a goat image to start measuring! 📏")

if __name__ == '__main__':
    setup_project()
