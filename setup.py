#!/usr/bin/env python3
"""Setup script for Hytale CurseForge CLI."""
from setuptools import setup, find_packages

setup(
    name="hytale-cf",
    version="1.0.0",
    description="APT-style CLI for managing Hytale mods via CurseForge",
    author="rederyk",
    url="https://github.com/rederyk/Hytale_CurseForge_CLI",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],  # No required dependencies! Uses stdlib only
    extras_require={
        "pretty": ["click>=8.0", "rich>=13.0"],  # Enhanced CLI output
        "gui": ["PySide6>=6.0"],
        "tui": ["textual>=0.40"],
    },
    entry_points={
        "console_scripts": [
            "hytale-cf=cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Games/Entertainment",
    ],
)
