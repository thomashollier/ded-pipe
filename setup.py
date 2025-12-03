"""
Setup script for the footage ingest pipeline package.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="ded-io",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="DED-IO: Digital Editorial Data - Input/Output pipeline for VFX production",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ded-io",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "mypy>=0.990",
            "flake8>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ingest-cli=ingest_cli:main",
        ],
    },
    scripts=[
        'ingest-cli.py',
    ],
)
