"""
AWS SSM Parameter Store Password Manager Library

A Python library for managing login-password pairs stored as SecureString parameters 
in AWS SSM Parameter Store.
"""

from .password_manager import PasswordManager
from .exceptions import (
    PasswordManagerError,
    LoginNotFoundError,
    LoginAlreadyExistsError,
    ValidationError,
    AWSError
)

__version__ = "1.0.0"
__author__ = "Password Manager"
__email__ = "noreply@example.com"

__all__ = [
    "PasswordManager",
    "PasswordManagerError",
    "LoginNotFoundError", 
    "LoginAlreadyExistsError",
    "ValidationError",
    "AWSError"
]