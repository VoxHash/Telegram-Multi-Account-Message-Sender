# macOS Build Guide

This guide will walk you through building the Telegram Multi-Account Message Sender for macOS on your Mac.

## 📋 Prerequisites

### Required Software
- **macOS 10.15+** (Catalina or later)
- **Xcode Command Line Tools**
- **Python 3.10+**
- **Homebrew** (recommended package manager)

### Install Prerequisites

1. **Install Xcode Command Line Tools:**
   ```bash
   xcode-select --install
   ```

2. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. **Install Python 3.10+**:
   ```bash
   brew install python@3.10
   ```

4. **Verify Python installation:**
   ```bash
   python3 --version
   # Should show Python 3.10.x or later
   ```

## 🚀 Quick Build

### Option 1: Automated Build Script
```bash
# Clone the repository
git clone https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git
cd Telegram-Multi-Account-Message-Sender

# Run the automated build script
python3 build_all_platforms.py
```

### Option 2: Manual Build Process

#### Step 1: Set Up Environment
```bash
# Clone the repository
git clone https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git
cd Telegram-Multi-Account-Message-Sender

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller py2app
```

#### Step 2: Build Executable
```bash
# Build standalone executable
pyinstaller --onefile --name telegram-multi-account-sender main.py

# Build directory distribution
pyinstaller --onedir --name telegram-multi-account-sender-dir main.py
```

#### Step 3: Create Application Bundle
```bash
# Create .app bundle using py2app
python3 setup_macos.py py2app
```

#### Step 4: Create DMG Installer
```bash
# Run the DMG creation script
./create_dmg.sh
```

## 🔧 Detailed Build Process

### Method 1: PyInstaller (Recommended)

#### 1. Install PyInstaller
```bash
pip install pyinstaller
```

#### 2. Create Spec File
Create `telegram_sender.spec`:
```python
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
    hooksconfig={},
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
    name='telegram-multi-account-sender',
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
```

#### 3. Build Executable
```bash
pyinstaller telegram_sender.spec
```

### Method 2: py2app (Native macOS Bundle)

#### 1. Install py2app
```bash
pip install py2app
```

#### 2. Create Setup Script
Create `setup_macos.py`:
```python
from setuptools import setup
import py2app

APP = ['main.py']
DATA_FILES = [
    ('app/translations', ['app/translations']),
    ('assets', ['assets']),
    ('example_files', ['example_files']),
]

OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'assets/icons/favicon.ico',
    'plist': {
        'CFBundleName': 'Telegram Multi-Account Message Sender',
        'CFBundleDisplayName': 'Telegram Multi-Account Message Sender',
        'CFBundleGetInfoString': 'Professional-grade desktop application for managing and sending messages across multiple Telegram accounts',
        'CFBundleIdentifier': 'dev.voxhash.telegram-multi-account-sender',
        'CFBundleVersion': '1.2.0',
        'CFBundleShortVersionString': '1.2.0',
        'NSHighResolutionCapable': True,
    },
    'packages': ['PyQt5', 'telethon', 'sqlmodel', 'pydantic', 'rich', 'cryptography', 'qrcode'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

#### 3. Build Application Bundle
```bash
python3 setup_macos.py py2app
```

## 📦 Creating DMG Installer

### Method 1: Using hdiutil (Command Line)

```bash
#!/bin/bash
# Create DMG for macOS

APP_NAME="Telegram Multi-Account Message Sender"
APP_VERSION="1.2.0"
DMG_NAME="TelegramMultiAccountSender-${APP_VERSION}-macOS"
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
```

### Method 2: Using create-dmg (Third-party Tool)

#### 1. Install create-dmg
```bash
brew install create-dmg
```

#### 2. Create DMG
```bash
create-dmg \
  --volname "Telegram Multi-Account Message Sender" \
  --volicon "assets/icons/favicon.ico" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "Telegram Multi-Account Message Sender.app" 175 120 \
  --hide-extension "Telegram Multi-Account Message Sender.app" \
  --app-drop-link 425 120 \
  "TelegramMultiAccountSender-1.2.0-macOS.dmg" \
  "dist/"
```

## 🔐 Code Signing (Optional)

### 1. Get Developer Certificate
- Join Apple Developer Program ($99/year)
- Download certificate from Apple Developer Portal
- Install certificate in Keychain Access

### 2. Sign the Application
```bash
# Sign the application bundle
codesign --force --verify --verbose --sign "Developer ID Application: Your Name" "dist/Telegram Multi-Account Message Sender.app"

# Sign the DMG
codesign --force --verify --verbose --sign "Developer ID Application: Your Name" "TelegramMultiAccountSender-1.2.0-macOS.dmg"
```

### 3. Notarize (Required for Distribution)
```bash
# Create notarization zip
ditto -c -k --keepParent "dist/Telegram Multi-Account Message Sender.app" "notarize.zip"

# Submit for notarization
xcrun altool --notarize-app --primary-bundle-id "dev.voxhash.telegram-multi-account-sender" --username "your-email@example.com" --password "@keychain:AC_PASSWORD" --file "notarize.zip"

# Staple notarization
xcrun stapler staple "TelegramMultiAccountSender-1.2.0-macOS.dmg"
```

## 🧪 Testing the Build

### 1. Test Executable
```bash
# Test standalone executable
./dist/telegram-multi-account-sender

# Test application bundle
open "dist/Telegram Multi-Account Message Sender.app"
```

### 2. Test DMG
```bash
# Mount DMG
hdiutil attach "TelegramMultiAccountSender-1.2.0-macOS.dmg"

# Test installation
open "/Volumes/Telegram Multi-Account Message Sender/Telegram Multi-Account Message Sender.app"

# Unmount DMG
hdiutil detach "/Volumes/Telegram Multi-Account Message Sender"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. "Python not found" Error
```bash
# Make sure Python 3.10+ is installed
python3 --version

# If using Homebrew Python, add to PATH
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### 2. "PyQt5 not found" Error
```bash
# Install PyQt5
pip install PyQt5

# Or using Homebrew
brew install pyqt5
```

#### 3. "Permission denied" Error
```bash
# Make scripts executable
chmod +x create_dmg.sh
chmod +x build_all_platforms.py
```

#### 4. "Module not found" Error
```bash
# Install all dependencies
pip install -r requirements.txt
pip install pyinstaller py2app
```

#### 5. "Icon file not found" Error
```bash
# Make sure icon file exists
ls -la assets/icons/favicon.ico

# If missing, create a simple icon or remove icon parameter
```

### Build Optimization

#### 1. Reduce Bundle Size
```bash
# Use UPX compression (install UPX first)
brew install upx

# Build with UPX
pyinstaller --onefile --upx-dir=/opt/homebrew/bin telegram_sender.spec
```

#### 2. Exclude Unnecessary Modules
```python
# In spec file, add to excludes
excludes=['tkinter', 'matplotlib', 'numpy', 'pandas']
```

#### 3. Use Virtual Environment
```bash
# Always use virtual environment for clean builds
python3 -m venv build_env
source build_env/bin/activate
pip install -r requirements.txt
```

## 📋 Build Checklist

- [ ] Python 3.10+ installed
- [ ] Xcode Command Line Tools installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] Icon file exists
- [ ] Build script runs without errors
- [ ] Executable runs correctly
- [ ] Application bundle created (if using py2app)
- [ ] DMG installer created
- [ ] DMG mounts and installs correctly
- [ ] Application runs from DMG
- [ ] Code signing (if required)
- [ ] Notarization (if distributing)

## 🚀 Distribution

### 1. Upload to GitHub Releases
```bash
# Tag the release
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0

# Upload DMG to GitHub Releases manually or use GitHub CLI
gh release create v1.2.0 "TelegramMultiAccountSender-1.2.0-macOS.dmg"
```

### 2. Upload to PyPI
```bash
# Build package
python3 -m build

# Upload to PyPI
twine upload dist/*
```

## 📞 Support

If you encounter issues during the build process:

1. **Check the logs** - Look for error messages in the terminal output
2. **Verify dependencies** - Make sure all required packages are installed
3. **Check file permissions** - Ensure scripts are executable
4. **Clean build** - Remove build artifacts and try again
5. **Ask for help** - Open an issue on GitHub with detailed error information

## 🔗 Useful Links

- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [py2app Documentation](https://py2app.readthedocs.io/)
- [Apple Developer Documentation](https://developer.apple.com/documentation/)
- [Code Signing Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Homebrew](https://brew.sh/)

---

**Happy Building! 🚀**

For more help, visit our [GitHub Issues](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues) or [Discussions](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/discussions).
