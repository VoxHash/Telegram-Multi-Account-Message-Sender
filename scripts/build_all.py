"""
Build script for all platforms.
"""

import subprocess
import sys
from pathlib import Path


def build_all_platforms():
    """Build for all supported platforms."""
    project_root = Path(__file__).parent.parent
    build_script = project_root / "scripts" / "build_nuitka.py"
    
    platforms = [
        ("windows", "x64"),
        ("macos", "x64"),
        ("macos", "arm64"),
        ("linux", "x64"),
        ("linux", "arm64")
    ]
    
    results = {}
    
    for platform_name, arch in platforms:
        print(f"\n{'='*60}")
        print(f"Building for {platform_name} {arch}")
        print(f"{'='*60}")
        
        try:
            # Set environment variables for cross-compilation
            env = os.environ.copy()
            env["NUITKA_PLATFORM"] = platform_name
            env["NUITKA_ARCH"] = arch
            
            result = subprocess.run(
                [sys.executable, str(build_script)],
                cwd=project_root,
                env=env,
                check=True,
                capture_output=True,
                text=True
            )
            
            results[f"{platform_name}-{arch}"] = True
            print(f"✅ {platform_name} {arch} - SUCCESS")
            
        except subprocess.CalledProcessError as e:
            results[f"{platform_name}-{arch}"] = False
            print(f"❌ {platform_name} {arch} - FAILED")
            print(f"Error: {e.stderr}")
    
    # Summary
    print(f"\n{'='*60}")
    print("BUILD SUMMARY")
    print(f"{'='*60}")
    
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    for platform_arch, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{platform_arch:20} {status}")
    
    print(f"\nTotal: {successful}/{total} successful")
    
    if successful == total:
        print("🎉 All builds completed successfully!")
        return True
    else:
        print("⚠️  Some builds failed. Check the logs above.")
        return False


def main():
    """Main function."""
    print("Telegram Multi-Account Message Sender - Multi-Platform Build")
    print("=" * 60)
    
    success = build_all_platforms()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    import os
    main()
