#!/usr/bin/env python3
"""
Comprehensive build script for Telegram Multi-Account Message Sender
Creates executables and installers for Windows, Linux, and macOS
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path
import json

class BuildManager:
    def __init__(self):
        self.project_name = "telegram-multi-account-sender"
        self.version = "1.2.0"
        self.build_dir = Path("build")
        self.dist_dir = Path("dist")
        self.current_platform = platform.system().lower()
        
    def clean_build_dirs(self):
        """Clean build and dist directories"""
        print("🧹 Cleaning build directories...")
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"   Removed {dir_path}")
        
        # Create fresh directories
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
        print("✅ Build directories cleaned")
    
    def install_dependencies(self):
        """Install build dependencies"""
        print("📦 Installing build dependencies...")
        
        dependencies = [
            "pyinstaller>=5.0",
            "cx-freeze>=6.0",
            "py2app>=0.28",
            "fbs>=0.9",
            "auto-py-to-exe>=2.0",
            "nuitka>=1.0",
            "setuptools>=61.0",
            "wheel>=0.37",
            "twine>=4.0"
        ]
        
        for dep in dependencies:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
                print(f"   ✅ Installed {dep}")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed to install {dep}: {e}")
    
    def build_windows(self):
        """Build Windows executable and installer"""
        print("🪟 Building Windows executable...")
        
        # PyInstaller spec for Windows
        spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/translations', 'app/translations'),
        ('assets', 'assets'),
        ('example_files', 'example_files'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'telethon',
        'sqlmodel',
        'pydantic',
        'rich',
        'cryptography',
        'qrcode',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{self.project_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/favicon.ico'
)
'''
        
        with open("telegram_sender.spec", "w") as f:
            f.write(spec_content)
        
        # Build with PyInstaller
        try:
            subprocess.run([
                sys.executable, "-m", "PyInstaller", 
                "--clean", 
                "--noconfirm",
                "telegram_sender.spec"
            ], check=True)
            print("   ✅ Windows executable built successfully")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to build Windows executable: {e}")
            return False
        
        # Create Windows installer with Inno Setup
        self.create_windows_installer()
        return True
    
    def create_windows_installer(self):
        """Create Windows installer using Inno Setup"""
        print("📦 Creating Windows installer...")
        
        inno_script = f'''
[Setup]
AppName=Telegram Multi-Account Message Sender
AppVersion={self.version}
AppPublisher=VoxHash
AppPublisherURL=https://voxhash.dev
AppSupportURL=https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues
AppUpdatesURL=https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/releases
DefaultDirName={{autopf}}\\TelegramMultiAccountSender
DefaultGroupName=Telegram Multi-Account Message Sender
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=dist
OutputBaseFilename=TelegramMultiAccountSender-{self.version}-Windows
SetupIconFile=assets\\icons\\favicon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{{cm:CreateQuickLaunchIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "dist\\{self.project_name}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "LICENSE"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "CHANGELOG.md"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\Telegram Multi-Account Message Sender"; Filename: "{{app}}\\{self.project_name}.exe"
Name: "{{group}}\\{{cm:UninstallProgram,Telegram Multi-Account Message Sender}}"; Filename: "{{uninstallexe}}"
Name: "{{commondesktop}}\\Telegram Multi-Account Message Sender"; Filename: "{{app}}\\{self.project_name}.exe"; Tasks: desktopicon
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\Telegram Multi-Account Message Sender"; Filename: "{{app}}\\{self.project_name}.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{{app}}\\{self.project_name}.exe"; Description: "{{cm:LaunchProgram,Telegram Multi-Account Message Sender}}"; Flags: nowait postinstall skipifsilent
'''
        
        with open("installer.iss", "w") as f:
            f.write(inno_script)
        
        print("   📝 Inno Setup script created")
        print("   ⚠️  Please install Inno Setup and run installer.iss to create the installer")
    
    def build_linux(self):
        """Build Linux packages"""
        print("🐧 Building Linux packages...")
        
        # Create .deb package for Debian/Ubuntu
        self.create_deb_package()
        
        # Create .rpm package for Fedora/CentOS/RHEL
        self.create_rpm_package()
        
        # Create .tar.gz for source distribution
        self.create_tar_gz()
        
        # Create Arch Linux PKGBUILD
        self.create_arch_pkgbuild()
    
    def create_deb_package(self):
        """Create .deb package for Debian/Ubuntu"""
        print("   📦 Creating .deb package...")
        
        debian_dir = Path("debian")
        debian_dir.mkdir(exist_ok=True)
        
        # Create control file
        control_content = f'''Package: {self.project_name}
Version: {self.version}
Section: net
Priority: optional
Architecture: all
Depends: python3 (>= 3.10), python3-pyqt5, python3-pip
Maintainer: VoxHash <contact@voxhash.dev>
Description: Professional-grade desktop application for managing and sending messages across multiple Telegram accounts
 A comprehensive desktop application for managing multiple Telegram accounts with advanced features like scheduling, spintax, media support, and compliance controls.
 .
 Features:
  - Multi-account management
  - Campaign management with scheduling
  - Template system with spintax support
  - Recipient management
  - Message testing
  - Comprehensive logging
  - Multi-language support (13 languages)
  - Dark/Light themes
  - Account warmup
  - Rate limiting
  - Media support
 .
 This application is for educational and legitimate business purposes only.
 Users are responsible for complying with Telegram's Terms of Service and applicable laws.
'''
        
        with open(debian_dir / "control", "w") as f:
            f.write(control_content)
        
        # Create postinst script
        postinst_content = '''#!/bin/bash
set -e

# Install Python dependencies
pip3 install --user telethon sqlmodel pydantic rich cryptography qrcode

# Create desktop entry
cat > /usr/share/applications/telegram-multi-account-sender.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Telegram Multi-Account Message Sender
Comment=Professional-grade desktop application for managing and sending messages across multiple Telegram accounts
Exec=/usr/bin/telegram-multi-account-sender
Icon=telegram-multi-account-sender
Terminal=false
Categories=Network;InstantMessaging;
EOF

# Make executable
chmod +x /usr/bin/telegram-multi-account-sender

echo "Telegram Multi-Account Message Sender installed successfully!"
'''
        
        with open(debian_dir / "postinst", "w") as f:
            f.write(postinst_content)
        
        os.chmod(debian_dir / "postinst", 0o755)
        
        print("   ✅ .deb package files created")
    
    def create_rpm_package(self):
        """Create .rpm package for Fedora/CentOS/RHEL"""
        print("   📦 Creating .rpm package...")
        
        spec_content = f'''Name: {self.project_name}
Version: {self.version}
Release: 1%{{?dist}}
Summary: Professional-grade desktop application for managing and sending messages across multiple Telegram accounts
License: BSD-3-Clause
URL: https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender
Source0: https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/archive/v{self.version}.tar.gz

BuildArch: noarch
Requires: python3 >= 3.10, python3-PyQt5, python3-pip

%description
A comprehensive desktop application for managing multiple Telegram accounts with advanced features like scheduling, spintax, media support, and compliance controls.

Features:
- Multi-account management
- Campaign management with scheduling  
- Template system with spintax support
- Recipient management
- Message testing
- Comprehensive logging
- Multi-language support (13 languages)
- Dark/Light themes
- Account warmup
- Rate limiting
- Media support

This application is for educational and legitimate business purposes only.
Users are responsible for complying with Telegram's Terms of Service and applicable laws.

%prep
%setup -q

%build
# Nothing to build for Python application

%install
mkdir -p %{{buildroot}}/usr/bin
mkdir -p %{{buildroot}}/usr/share/applications
mkdir -p %{{buildroot}}/usr/share/pixmaps

# Install application files
cp -r * %{{buildroot}}/usr/share/{self.project_name}/

# Create executable script
cat > %{{buildroot}}/usr/bin/{self.project_name} << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/usr/share/{self.project_name}')
os.chdir('/usr/share/{self.project_name}')
exec(open('main.py').read())
EOF

chmod +x %{{buildroot}}/usr/bin/{self.project_name}

# Create desktop entry
cat > %{{buildroot}}/usr/share/applications/{self.project_name}.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Telegram Multi-Account Message Sender
Comment=Professional-grade desktop application for managing and sending messages across multiple Telegram accounts
Exec={self.project_name}
Icon={self.project_name}
Terminal=false
Categories=Network;InstantMessaging;
EOF

%files
/usr/bin/{self.project_name}
/usr/share/{self.project_name}/
/usr/share/applications/{self.project_name}.desktop

%post
# Install Python dependencies
pip3 install --user telethon sqlmodel pydantic rich cryptography qrcode

%changelog
* {self.version}-1 VoxHash <contact@voxhash.dev> - {self.version}-1
- Initial package
'''
        
        with open(f"{self.project_name}.spec", "w") as f:
            f.write(spec_content)
        
        print("   ✅ .rpm package files created")
    
    def create_tar_gz(self):
        """Create .tar.gz source distribution"""
        print("   📦 Creating .tar.gz source distribution...")
        
        try:
            subprocess.run([
                sys.executable, "setup.py", "sdist"
            ], check=True)
            print("   ✅ .tar.gz created successfully")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to create .tar.gz: {e}")
    
    def create_arch_pkgbuild(self):
        """Create Arch Linux PKGBUILD"""
        print("   📦 Creating Arch Linux PKGBUILD...")
        
        pkgbuild_content = f'''# Maintainer: VoxHash <contact@voxhash.dev>
pkgname={self.project_name}
pkgver={self.version}
pkgrel=1
pkgdesc="Professional-grade desktop application for managing and sending messages across multiple Telegram accounts"
arch=('any')
url="https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender"
license=('BSD-3-Clause')
depends=('python' 'python-pyqt5' 'python-pip')
makedepends=('python-setuptools')
source=("https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')

package() {{
    cd "$srcdir/Telegram-Multi-Account-Message-Sender-$pkgver"
    
    # Install application
    python setup.py install --root="$pkgdir" --optimize=1
    
    # Create desktop entry
    install -Dm644 assets/icons/favicon.ico "$pkgdir/usr/share/pixmaps/$pkgname.ico"
    
    cat > "$pkgdir/usr/share/applications/$pkgname.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Telegram Multi-Account Message Sender
Comment=Professional-grade desktop application for managing and sending messages across multiple Telegram accounts
Exec=$pkgname
Icon=$pkgname
Terminal=false
Categories=Network;InstantMessaging;
EOF
}}
'''
        
        with open("PKGBUILD", "w") as f:
            f.write(pkgbuild_content)
        
        print("   ✅ PKGBUILD created successfully")
    
    def build_macos(self):
        """Build macOS application bundle"""
        print("🍎 Building macOS application...")
        
        # Create py2app setup
        setup_py2app = f'''
from setuptools import setup
import py2app

APP = ['main.py']
DATA_FILES = [
    ('app/translations', ['app/translations']),
    ('assets', ['assets']),
    ('example_files', ['example_files']),
]

OPTIONS = {{
    'argv_emulation': True,
    'iconfile': 'assets/icons/favicon.ico',
    'plist': {{
        'CFBundleName': 'Telegram Multi-Account Message Sender',
        'CFBundleDisplayName': 'Telegram Multi-Account Message Sender',
        'CFBundleGetInfoString': 'Professional-grade desktop application for managing and sending messages across multiple Telegram accounts',
        'CFBundleIdentifier': 'dev.voxhash.telegram-multi-account-sender',
        'CFBundleVersion': '{self.version}',
        'CFBundleShortVersionString': '{self.version}',
        'NSHighResolutionCapable': True,
    }},
    'packages': ['PyQt5', 'telethon', 'sqlmodel', 'pydantic', 'rich', 'cryptography', 'qrcode'],
}}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={{'py2app': OPTIONS}},
    setup_requires=['py2app'],
)
'''
        
        with open("setup_macos.py", "w") as f:
            f.write(setup_py2app)
        
        try:
            subprocess.run([
                sys.executable, "setup_macos.py", "py2app"
            ], check=True)
            print("   ✅ macOS application built successfully")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to build macOS application: {e}")
            return False
        
        # Create .dmg installer
        self.create_macos_dmg()
        return True
    
    def create_macos_dmg(self):
        """Create macOS .dmg installer"""
        print("   📦 Creating macOS .dmg installer...")
        
        dmg_script = f'''#!/bin/bash
# Create DMG for macOS

APP_NAME="Telegram Multi-Account Message Sender"
APP_VERSION="{self.version}"
DMG_NAME="TelegramMultiAccountSender-{self.version}-macOS"
VOLUME_NAME="Telegram Multi-Account Message Sender"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
APP_DIR="$TEMP_DIR/$APP_NAME.app"

# Copy application
cp -R "dist/$APP_NAME.app" "$APP_DIR"

# Create DMG
hdiutil create -srcfolder "$TEMP_DIR" -volname "$VOLUME_NAME" -fs HFS+ -fsargs "-c c=64,a=16,e=16" -format UDRW -size 200m "$DMG_NAME.temp.dmg"

# Mount DMG
hdiutil attach "$DMG_NAME.temp.dmg" -readwrite -noverify -noautoopen

# Create final DMG
hdiutil convert "$DMG_NAME.temp.dmg" -format UDZO -imagekey zlib-level=9 -o "$DMG_NAME.dmg"

# Cleanup
hdiutil detach /Volumes/"$VOLUME_NAME"
rm -rf "$TEMP_DIR"
rm "$DMG_NAME.temp.dmg"

echo "DMG created: $DMG_NAME.dmg"
'''
        
        with open("create_dmg.sh", "w") as f:
            f.write(dmg_script)
        
        os.chmod("create_dmg.sh", 0o755)
        print("   📝 DMG creation script created")
        print("   ⚠️  Run ./create_dmg.sh to create the DMG installer")
    
    def build_pypi_package(self):
        """Build and prepare PyPI package"""
        print("🐍 Building PyPI package...")
        
        try:
            # Clean previous builds
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "build", "twine"], check=True)
            
            # Build package
            subprocess.run([sys.executable, "-m", "build"], check=True)
            print("   ✅ PyPI package built successfully")
            
            # Check package
            subprocess.run([sys.executable, "-m", "twine", "check", "dist/*"], check=True)
            print("   ✅ Package check passed")
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to build PyPI package: {e}")
            return False
        
        return True
    
    def upload_to_pypi(self):
        """Upload package to PyPI"""
        print("🚀 Uploading to PyPI...")
        
        try:
            subprocess.run([
                sys.executable, "-m", "twine", "upload", "dist/*"
            ], check=True)
            print("   ✅ Package uploaded to PyPI successfully")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to upload to PyPI: {e}")
            return False
        
        return True
    
    def run_all_builds(self):
        """Run all build processes"""
        print(f"🚀 Starting comprehensive build for {self.project_name} v{self.version}")
        print(f"   Platform: {self.current_platform}")
        
        # Clean and prepare
        self.clean_build_dirs()
        self.install_dependencies()
        
        # Build based on platform
        if self.current_platform == "windows":
            self.build_windows()
        elif self.current_platform == "linux":
            self.build_linux()
        elif self.current_platform == "darwin":
            self.build_macos()
        else:
            print(f"   ⚠️  Unsupported platform: {self.current_platform}")
            print("   Building PyPI package only...")
        
        # Always build PyPI package
        if self.build_pypi_package():
            print("   ✅ PyPI package ready for upload")
            upload = input("   Upload to PyPI? (y/N): ").lower().strip()
            if upload == 'y':
                self.upload_to_pypi()
        
        print("🎉 Build process completed!")
        print(f"   Check the 'dist' directory for built packages")
        print(f"   Check the 'build' directory for build artifacts")

if __name__ == "__main__":
    builder = BuildManager()
    builder.run_all_builds()
