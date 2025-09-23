# Linux Build Guide

This guide will walk you through building the Telegram Multi-Account Message Sender for various Linux distributions.

## 📋 Prerequisites

### Required Software
- **Python 3.10+**
- **PyQt5**
- **pip** (Python package manager)
- **build-essential** (for compilation)
- **fakeroot** (for package creation)

## 🐧 Distribution-Specific Setup

### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install Python and dependencies
sudo apt install python3 python3-pip python3-pyqt5 python3-venv build-essential fakeroot

# Install additional tools for packaging
sudo apt install dh-make devscripts debhelper
```

### Fedora/CentOS/RHEL
```bash
# Install Python and dependencies
sudo dnf install python3 python3-pip python3-qt5 python3-venv gcc gcc-c++ make

# Install RPM build tools
sudo dnf install rpm-build rpmdevtools
```

### Arch Linux
```bash
# Install Python and dependencies
sudo pacman -S python python-pip python-pyqt5 python-virtualenv base-devel

# Install AUR helper (optional)
yay -S python-pyqt5
```

### openSUSE
```bash
# Install Python and dependencies
sudo zypper install python3 python3-pip python3-qt5 python3-venv gcc gcc-c++ make

# Install RPM build tools
sudo zypper install rpm-build
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
pip install pyinstaller
```

#### Step 2: Build Executable
```bash
# Build standalone executable
pyinstaller --onefile --name telegram-multi-account-sender main.py

# Build directory distribution
pyinstaller --onedir --name telegram-multi-account-sender-dir main.py
```

## 📦 Creating Linux Packages

### Debian/Ubuntu (.deb) Package

#### Method 1: Using dh_make
```bash
# Install dh_make
sudo apt install dh-make

# Create package directory
mkdir telegram-multi-account-sender-1.2.0
cd telegram-multi-account-sender-1.2.0

# Copy source files
cp -r ../app .
cp ../main.py .
cp ../requirements.txt .
cp ../README.md .
cp ../LICENSE .

# Initialize Debian package
dh_make --createorig --single

# Edit debian/control file
cat > debian/control << EOF
Source: telegram-multi-account-sender
Section: net
Priority: optional
Maintainer: VoxHash <contact@voxhash.dev>
Build-Depends: debhelper (>= 9), python3 (>= 3.10), python3-setuptools
Standards-Version: 4.1.3
Homepage: https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender

Package: telegram-multi-account-sender
Architecture: all
Depends: \${python3:Depends}, python3-pyqt5, python3-pip
Description: Professional-grade desktop application for managing and sending messages across multiple Telegram accounts
 A comprehensive desktop application for managing multiple Telegram accounts with advanced features like scheduling, spintax, media support, and compliance controls.
EOF

# Build package
dpkg-buildpackage -us -uc
```

#### Method 2: Using setup.py
```bash
# Create setup.py for Debian
cat > setup_debian.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name='telegram-multi-account-sender',
    version='1.2.0',
    packages=find_packages(),
    install_requires=[
        'PyQt5>=5.15.0',
        'telethon>=1.24.0',
        'sqlmodel>=0.0.8',
        'pydantic>=1.10.0',
        'rich>=12.0.0',
        'cryptography>=3.4.8',
        'qrcode>=7.3.1',
    ],
    entry_points={
        'console_scripts': [
            'telegram-multi-account-sender=main:main',
        ],
    },
    data_files=[
        ('share/applications', ['telegram-multi-account-sender.desktop']),
        ('share/pixmaps', ['assets/icons/favicon.ico']),
    ],
)
EOF

# Create desktop entry
cat > telegram-multi-account-sender.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Telegram Multi-Account Message Sender
Comment=Professional-grade desktop application for managing and sending messages across multiple Telegram accounts
Exec=telegram-multi-account-sender
Icon=telegram-multi-account-sender
Terminal=false
Categories=Network;InstantMessaging;
EOF

# Build package
python3 setup_debian.py bdist_deb
```

### Fedora/CentOS/RHEL (.rpm) Package

#### Method 1: Using rpmbuild
```bash
# Set up RPM build environment
rpmdev-setuptree

# Create spec file
cat > ~/rpmbuild/SPECS/telegram-multi-account-sender.spec << 'EOF'
Name: telegram-multi-account-sender
Version: 1.2.0
Release: 1%{?dist}
Summary: Professional-grade desktop application for managing and sending messages across multiple Telegram accounts
License: BSD-3-Clause
URL: https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender
Source0: https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/archive/v%{version}.tar.gz

BuildArch: noarch
Requires: python3 >= 3.10, python3-PyQt5, python3-pip

%description
A comprehensive desktop application for managing multiple Telegram accounts with advanced features like scheduling, spintax, media support, and compliance controls.

%prep
%setup -q

%build
# Nothing to build for Python application

%install
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/pixmaps

# Install application files
cp -r * %{buildroot}/usr/share/%{name}/

# Create executable script
cat > %{buildroot}/usr/bin/%{name} << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/usr/share/telegram-multi-account-sender')
os.chdir('/usr/share/telegram-multi-account-sender')
exec(open('main.py').read())
EOF

chmod +x %{buildroot}/usr/bin/%{name}

# Create desktop entry
cat > %{buildroot}/usr/share/applications/%{name}.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Telegram Multi-Account Message Sender
Comment=Professional-grade desktop application for managing and sending messages across multiple Telegram accounts
Exec=telegram-multi-account-sender
Icon=telegram-multi-account-sender
Terminal=false
Categories=Network;InstantMessaging;
EOF

%files
/usr/bin/%{name}
/usr/share/%{name}/
/usr/share/applications/%{name}.desktop

%post
# Install Python dependencies
pip3 install --user telethon sqlmodel pydantic rich cryptography qrcode

%changelog
* 1.2.0-1 VoxHash <contact@voxhash.dev> - 1.2.0-1
- Initial package
EOF

# Build RPM
rpmbuild -ba ~/rpmbuild/SPECS/telegram-multi-account-sender.spec
```

#### Method 2: Using setup.py
```bash
# Create setup.py for RPM
cat > setup_rpm.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name='telegram-multi-account-sender',
    version='1.2.0',
    packages=find_packages(),
    install_requires=[
        'PyQt5>=5.15.0',
        'telethon>=1.24.0',
        'sqlmodel>=0.0.8',
        'pydantic>=1.10.0',
        'rich>=12.0.0',
        'cryptography>=3.4.8',
        'qrcode>=7.3.1',
    ],
    entry_points={
        'console_scripts': [
            'telegram-multi-account-sender=main:main',
        ],
    },
    data_files=[
        ('share/applications', ['telegram-multi-account-sender.desktop']),
        ('share/pixmaps', ['assets/icons/favicon.ico']),
    ],
)
EOF

# Build RPM
python3 setup_rpm.py bdist_rpm
```

### Arch Linux (PKGBUILD)

#### Method 1: Using makepkg
```bash
# Create PKGBUILD
cat > PKGBUILD << 'EOF'
# Maintainer: VoxHash <contact@voxhash.dev>
pkgname=telegram-multi-account-sender
pkgver=1.2.0
pkgrel=1
pkgdesc="Professional-grade desktop application for managing and sending messages across multiple Telegram accounts"
arch=('any')
url="https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender"
license=('BSD-3-Clause')
depends=('python' 'python-pyqt5' 'python-pip')
makedepends=('python-setuptools')
source=("https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')

package() {
    cd "$srcdir/Telegram-Multi-Account-Message-Sender-$pkgver"
    
    # Install application
    python setup.py install --root="$pkgdir" --optimize=1
    
    # Create desktop entry
    install -Dm644 assets/icons/favicon.ico "$pkgdir/usr/share/pixmaps/$pkgname.ico"
    
    cat > "$pkgdir/usr/share/applications/$pkgname.desktop" << 'DESKTOP'
[Desktop Entry]
Version=1.0
Type=Application
Name=Telegram Multi-Account Message Sender
Comment=Professional-grade desktop application for managing and sending messages across multiple Telegram accounts
Exec=telegram-multi-account-sender
Icon=telegram-multi-account-sender
Terminal=false
Categories=Network;InstantMessaging;
DESKTOP
}
EOF

# Build package
makepkg -s
```

#### Method 2: Using AUR
```bash
# Create AUR package
git clone https://aur.archlinux.org/telegram-multi-account-sender.git
cd telegram-multi-account-sender

# Edit PKGBUILD if needed
nano PKGBUILD

# Build package
makepkg -s

# Install package
sudo pacman -U telegram-multi-account-sender-1.2.0-1-any.pkg.tar.zst
```

### Generic Linux (.tar.gz)

#### Create Source Distribution
```bash
# Create setup.py
cat > setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name='telegram-multi-account-sender',
    version='1.2.0',
    packages=find_packages(),
    install_requires=[
        'PyQt5>=5.15.0',
        'telethon>=1.24.0',
        'sqlmodel>=0.0.8',
        'pydantic>=1.10.0',
        'rich>=12.0.0',
        'cryptography>=3.4.8',
        'qrcode>=7.3.1',
    ],
    entry_points={
        'console_scripts': [
            'telegram-multi-account-sender=main:main',
        ],
    },
    data_files=[
        ('share/applications', ['telegram-multi-account-sender.desktop']),
        ('share/pixmaps', ['assets/icons/favicon.ico']),
    ],
)
EOF

# Create source distribution
python3 setup.py sdist

# Create binary distribution
python3 setup.py bdist
```

## 🧪 Testing the Build

### Test Executable
```bash
# Test standalone executable
./dist/telegram-multi-account-sender

# Test directory distribution
./dist/telegram-multi-account-sender-dir/telegram-multi-account-sender
```

### Test Package Installation
```bash
# Test .deb package
sudo dpkg -i telegram-multi-account-sender_1.2.0-1_all.deb

# Test .rpm package
sudo rpm -i telegram-multi-account-sender-1.2.0-1.noarch.rpm

# Test Arch package
sudo pacman -U telegram-multi-account-sender-1.2.0-1-any.pkg.tar.zst
```

## 🐛 Troubleshooting

### Common Issues

#### 1. "Python not found" Error
```bash
# Make sure Python 3.10+ is installed
python3 --version

# If using system Python, install python3-venv
sudo apt install python3-venv  # Ubuntu/Debian
sudo dnf install python3-venv  # Fedora
```

#### 2. "PyQt5 not found" Error
```bash
# Install PyQt5
sudo apt install python3-pyqt5  # Ubuntu/Debian
sudo dnf install python3-qt5    # Fedora
sudo pacman -S python-pyqt5     # Arch
```

#### 3. "Permission denied" Error
```bash
# Make scripts executable
chmod +x build_all_platforms.py
chmod +x create_*.sh
```

#### 4. "Module not found" Error
```bash
# Install all dependencies
pip install -r requirements.txt
pip install pyinstaller
```

#### 5. "Build tools not found" Error
```bash
# Install build tools
sudo apt install build-essential  # Ubuntu/Debian
sudo dnf groupinstall "Development Tools"  # Fedora
sudo pacman -S base-devel  # Arch
```

### Build Optimization

#### 1. Reduce Bundle Size
```bash
# Use UPX compression (install UPX first)
sudo apt install upx  # Ubuntu/Debian
sudo dnf install upx  # Fedora
yay -S upx  # Arch

# Build with UPX
pyinstaller --onefile --upx-dir=/usr/bin telegram_sender.spec
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
- [ ] PyQt5 installed
- [ ] Build tools installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] Build script runs without errors
- [ ] Executable runs correctly
- [ ] Package created successfully
- [ ] Package installs correctly
- [ ] Application runs from package
- [ ] Desktop entry works
- [ ] Icon displays correctly

## 🚀 Distribution

### 1. Upload to GitHub Releases
```bash
# Tag the release
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0

# Upload packages to GitHub Releases manually or use GitHub CLI
gh release create v1.2.0 "telegram-multi-account-sender-1.2.0-linux.tar.gz"
```

### 2. Upload to PyPI
```bash
# Build package
python3 -m build

# Upload to PyPI
twine upload dist/*
```

### 3. Submit to Distribution Repositories

#### Debian/Ubuntu
- Submit to Debian NEW queue
- Create PPA for Ubuntu
- Submit to Ubuntu universe

#### Fedora
- Submit to Fedora review
- Create COPR repository

#### Arch Linux
- Submit to AUR
- Submit to community repository

## 📞 Support

If you encounter issues during the build process:

1. **Check the logs** - Look for error messages in the terminal output
2. **Verify dependencies** - Make sure all required packages are installed
3. **Check file permissions** - Ensure scripts are executable
4. **Clean build** - Remove build artifacts and try again
5. **Ask for help** - Open an issue on GitHub with detailed error information

## 🔗 Useful Links

- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [Debian Packaging Guide](https://www.debian.org/doc/manuals/debian-faq/ch-pkg_basics.en.html)
- [RPM Packaging Guide](https://rpm-packaging-guide.github.io/)
- [Arch Linux Packaging Guide](https://wiki.archlinux.org/title/Creating_packages)
- [Python Packaging Guide](https://packaging.python.org/)

---

**Happy Building! 🚀**

For more help, visit our [GitHub Issues](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues) or [Discussions](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/discussions).
