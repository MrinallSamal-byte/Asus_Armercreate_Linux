#!/usr/bin/env python3
"""
ASUS Armoury Crate Linux - Setup Script

This script installs the application and its dependencies.
"""

from setuptools import setup, find_packages
import os

# Read version from package
version = "1.0.0"

# Read long description from README
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="asus-armoury-crate",
    version=version,
    author="ASUS Armoury Crate Linux Contributors",
    author_email="",
    description="Linux desktop application for ASUS laptop hardware control",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/asus-armoury-linux/asus-armoury-crate",
    project_urls={
        "Bug Tracker": "https://github.com/asus-armoury-linux/asus-armoury-crate/issues",
        "Documentation": "https://github.com/asus-armoury-linux/asus-armoury-crate/wiki",
    },
    license="GPL-3.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Hardware",
        "Topic :: Utilities",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[
        # Core dependencies (GTK4 and libadwaita are system packages)
        # Optional D-Bus library
    ],
    extras_require={
        "dbus": ["dasbus>=1.6"],
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "asus-armoury=frontend.ui.application:main",
            "asus-armoury-daemon=backend.services.daemon:main",
        ],
        "gui_scripts": [
            "asus-armoury-gui=frontend.ui.application:main",
        ],
    },
    data_files=[
        ("share/applications", ["data/org.asus.armoury.desktop"]),
        ("share/icons/hicolor/scalable/apps", ["data/icons/org.asus.armoury.svg"]),
        ("share/polkit-1/actions", ["polkit/org.asus.armoury.policy"]),
        ("lib/udev/rules.d", ["udev/99-asus-armoury.rules"]),
        ("lib/systemd/system", ["systemd/asus-armoury-daemon.service"]),
    ],
    include_package_data=True,
    zip_safe=False,
)
