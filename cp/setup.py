"""
Setup script for SSM Password Manager Library
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ssm-password-manager",
    version="1.0.0",
    author="Password Manager",
    author_email="noreply@example.com",
    description="A Python library for managing login-password pairs in AWS SSM Parameter Store",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ssm-password-manager",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.7",
    install_requires=[
        "boto3>=1.34.0",
    ],
    extras_require={
        "dev": [
            "moto[ssm]>=4.2.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
        "cli": [
            "click>=8.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ssm-password-manager=password_manager:main",
        ],
    },
    keywords="aws ssm parameter-store password-manager security credentials",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/ssm-password-manager/issues",
        "Source": "https://github.com/yourusername/ssm-password-manager",
        "Documentation": "https://github.com/yourusername/ssm-password-manager/blob/main/README.md",
    },
)