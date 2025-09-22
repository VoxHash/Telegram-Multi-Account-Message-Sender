"""
Nuitka build script for creating cross-platform binaries.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def get_platform_info():
    """Get platform information."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "windows":
        if machine in ["amd64", "x86_64"]:
            return "windows", "x64"
        else:
            return "windows", "x86"
    elif system == "darwin":
        if machine == "arm64":
            return "macos", "arm64"
        else:
            return "macos", "x64"
    elif system == "linux":
        if machine == "aarch64":
            return "linux", "arm64"
        else:
            return "linux", "x64"
    else:
        return "unknown", "unknown"


def build_application():
    """Build application using Nuitka."""
    platform_name, arch = get_platform_info()
    
    if platform_name == "unknown":
        print("Unsupported platform")
        return False
    
    # Get project root
    project_root = Path(__file__).parent.parent
    main_file = project_root / "main.py"
    
    if not main_file.exists():
        print(f"Main file not found: {main_file}")
        return False
    
    # Build output directory
    build_dir = project_root / "build" / f"{platform_name}-{arch}"
    dist_dir = project_root / "dist" / f"{platform_name}-{arch}"
    
    # Create directories
    build_dir.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    # Nuitka command
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--output-dir", str(dist_dir),
        "--output-filename", f"telegram-sender-{platform_name}-{arch}",
        "--include-data-dir=app=app",
        "--include-data-dir=assets=assets",
        "--include-data-file=env.example=env.example",
        "--include-data-file=README.md=README.md",
        "--include-data-file=LICENSE=LICENSE",
        "--enable-plugin=pyqt5",
        "--enable-plugin=pandas",
        "--enable-plugin=telethon",
        "--assume-yes-for-downloads",
        "--remove-output",
        str(main_file)
    ]
    
    # Platform-specific options
    if platform_name == "windows":
        cmd.extend([
            "--windows-console-mode=disable",
            "--windows-icon-from-ico=assets/icons/app.ico"
        ])
    elif platform_name == "macos":
        cmd.extend([
            "--macos-create-bundle",
            "--macos-app-icon=assets/icons/app.icns"
        ])
    elif platform_name == "linux":
        cmd.extend([
            "--linux-icon=assets/icons/app.png"
        ])
    
    print(f"Building for {platform_name} {arch}...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(f"Output directory: {dist_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False


def main():
    """Main function."""
    print("Telegram Multi-Account Message Sender - Nuitka Build Script")
    print("=" * 60)
    
    # Check if Nuitka is installed
    try:
        import nuitka
        print(f"Nuitka version: {nuitka.__version__}")
    except ImportError:
        print("Nuitka not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "nuitka"], check=True)
    
    # Build application
    success = build_application()
    
    if success:
        print("\nBuild completed successfully!")
        print("You can find the executable in the dist/ directory.")
    else:
        print("\nBuild failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
