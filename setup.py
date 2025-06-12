"""Setup configuration for RouterOS parser."""
from setuptools import setup, find_packages
import os

# Read version from package
def get_version():
    """Get version from package init file."""
    here = os.path.abspath(os.path.dirname(__file__))
    init_file = os.path.join(here, 'src', '__init__.py')
    
    with open(init_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"\'')
    return "0.0.0"

# Read long description from README
def get_long_description():
    """Get long description from README file."""
    here = os.path.abspath(os.path.dirname(__file__))
    readme_file = os.path.join(here, 'README.md')
    
    if os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

setup(
    name="routeros-parser",
    version=get_version(),
    author="RouterOS Parser Team",
    author_email="",
    description="Parse RouterOS configuration files and generate GitHub-friendly summaries",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/routeros-parser",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators", 
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies for core functionality
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0", 
            "black>=21.0.0",
            "flake8>=3.8.0",
            "mypy>=0.812",
        ],
    },
    entry_points={
        "console_scripts": [
            "routeros-parser=src.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)