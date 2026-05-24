#!/usr/bin/env python3
"""
Setup script for Telegram Multi-Account Message Sender.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

def _read_requirements(filename: str) -> list[str]:
    path = this_directory / filename
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


requirements = _read_requirements("requirements.txt")
cloud_requirements = _read_requirements("requirements-cloud.txt")
dev_requirements = _read_requirements("requirements-dev.txt")
docs_requirements = _read_requirements("requirements-docs.txt")

# Read version
version = "1.2.13"

setup(
    name="telegram-multi-account-sender",
    version=version,
    author="VoxHash",
    author_email="contact@voxhash.dev",
    description="Professional-grade desktop application for managing and sending messages across multiple Telegram accounts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender",
    project_urls={
        "Bug Reports": "https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/issues",
        "Source": "https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender",
        "Documentation": "https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/wiki",
        "Changelog": "https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/blob/main/CHANGELOG.md",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications :: Qt",
        "Environment :: Win32 (MS Windows)",
        "Environment :: MacOS X",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
        "docs": docs_requirements,
        "cloud": cloud_requirements,
    },
    entry_points={
        "console_scripts": [
            "telegram-sender=app.cli:main",
            "telegram-multi-account-sender=app.cli:main",
        ],
        "gui_scripts": [
            "telegram-sender-gui=app.cli:main",
            "telegram-multi-account-sender-gui=app.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "app": [
            "translations/*.json",
            "assets/icons/*.ico",
            "assets/icons/*.png",
        ],
    },
    data_files=[
        ("example_files", [
            "example_files/env_template.txt",
            "example_files/recipients_example.csv",
            "example_files/templates_example.csv",
            "example_files/accounts_example.csv",
            "example_files/campaigns_example.csv",
            "example_files/sample_media_urls.txt",
            "example_files/spintax_examples.txt",
        ]),
    ],
    keywords=[
        "telegram",
        "messaging",
        "multi-account",
        "automation",
        "campaign",
        "spintax",
        "scheduling",
        "pyqt5",
        "desktop",
        "gui",
    ],
    license="BSD 3-Clause License",
    zip_safe=False,
    platforms=["Windows", "macOS", "Linux"],
    maintainer="VoxHash",
    maintainer_email="contact@voxhash.dev",
    download_url=f"https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/archive/v{version}.tar.gz",
    provides=["telegram_multi_account_sender"],
    requires_python=">=3.10",
    setup_requires=[
        "setuptools>=61.0.0",
        "wheel>=0.37.0",
    ],
    tests_require=[
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-qt>=4.0.0",
    ],
)