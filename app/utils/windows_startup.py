"""
Windows startup management utilities.
"""

import os
import sys
import winreg
from pathlib import Path
from typing import bool


def add_to_startup(app_name: str, app_path: str) -> bool:
    """
    Add application to Windows startup.
    
    Args:
        app_name: Name of the application
        app_path: Full path to the application executable
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Open the registry key for startup programs
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        
        # Set the value
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
        
        # Close the key
        winreg.CloseKey(key)
        
        return True
        
    except Exception as e:
        print(f"Error adding to startup: {e}")
        return False


def remove_from_startup(app_name: str) -> bool:
    """
    Remove application from Windows startup.
    
    Args:
        app_name: Name of the application
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Open the registry key for startup programs
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        
        # Delete the value
        winreg.DeleteValue(key, app_name)
        
        # Close the key
        winreg.CloseKey(key)
        
        return True
        
    except FileNotFoundError:
        # Key doesn't exist, which means it's not in startup
        return True
    except Exception as e:
        print(f"Error removing from startup: {e}")
        return False


def is_in_startup(app_name: str) -> bool:
    """
    Check if application is in Windows startup.
    
    Args:
        app_name: Name of the application
        
    Returns:
        True if in startup, False otherwise
    """
    try:
        # Open the registry key for startup programs
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )
        
        # Try to read the value
        try:
            winreg.QueryValueEx(key, app_name)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
            
    except Exception as e:
        print(f"Error checking startup status: {e}")
        return False


def get_app_path() -> str:
    """
    Get the full path to the current application.
    
    Returns:
        Full path to the application executable
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return sys.executable
    else:
        # Running as script
        return f'"{sys.executable}" "{os.path.abspath(__file__)}"'


def update_startup_setting(app_name: str, enabled: bool) -> bool:
    """
    Update Windows startup setting for the application.
    
    Args:
        app_name: Name of the application
        enabled: Whether to enable or disable startup
        
    Returns:
        True if successful, False otherwise
    """
    if enabled:
        app_path = get_app_path()
        return add_to_startup(app_name, app_path)
    else:
        return remove_from_startup(app_name)
