"""
Custom exceptions for SSM Password Manager
"""


class PasswordManagerError(Exception):
    """Base exception for password manager operations."""
    pass


class LoginNotFoundError(PasswordManagerError):
    """Raised when a login is not found in SSM Parameter Store."""
    pass


class LoginAlreadyExistsError(PasswordManagerError):
    """Raised when trying to create a login that already exists."""
    pass


class ValidationError(PasswordManagerError):
    """Raised when input validation fails."""
    pass


class AWSError(PasswordManagerError):
    """Raised when AWS operations fail."""
    pass