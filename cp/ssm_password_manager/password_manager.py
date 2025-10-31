"""
AWS SSM Parameter Store Password Manager

Core library for managing login-password pairs stored as SecureString parameters 
in AWS SSM Parameter Store.
"""

import secrets
import string
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, List, Optional

from .exceptions import (
    PasswordManagerError,
    LoginNotFoundError,
    LoginAlreadyExistsError,
    ValidationError,
    AWSError
)


class PasswordManager:
    """
    Manages login-password pairs in AWS SSM Parameter Store.
    
    Each login is stored as a separate SecureString parameter with the naming 
    convention: {prefix}{login}
    """
    
    def __init__(self, prefix: str = "/passwords/", region: str = None):
        """
        Initialize the password manager with AWS SSM client.
        
        Args:
            prefix: Parameter name prefix (default: "/passwords/")
            region: AWS region (optional, uses default region if not specified)
        """
        try:
            if region:
                self.ssm = boto3.client('ssm', region_name=region)
            else:
                self.ssm = boto3.client('ssm')
            self.prefix = prefix
        except NoCredentialsError:
            raise AWSError("AWS credentials not configured. Please configure AWS CLI or set environment variables.")
    
    def list_logins(self) -> List[str]:
        """
        List all available logins.
        
        Returns:
            List of login names in sorted order
            
        Raises:
            AWSError: If AWS operation fails
        """
        try:
            paginator = self.ssm.get_paginator('describe_parameters')
            logins = []
            
            for page in paginator.paginate(
                ParameterFilters=[
                    {
                        'Key': 'Name',
                        'Option': 'BeginsWith',
                        'Values': [self.prefix]
                    }
                ]
            ):
                for param in page['Parameters']:
                    login = param['Name'][len(self.prefix):]
                    logins.append(login)
            
            return sorted(logins)
        except ClientError as e:
            raise AWSError(f"Failed to list logins: {e}")
    
    def create_login(self, login: str, password: str = None) -> str:
        """
        Create a new login with password.
        
        Args:
            login: Login name
            password: Password (if None, generates secure random password)
            
        Returns:
            The password that was stored
            
        Raises:
            ValidationError: If login is empty
            LoginAlreadyExistsError: If login already exists
            AWSError: If AWS operation fails
        """
        if not login:
            raise ValidationError("Login cannot be empty")
        
        param_name = f"{self.prefix}{login}"
        
        if password is None:
            password = self._generate_password()
        
        try:
            self.ssm.put_parameter(
                Name=param_name,
                Value=password,
                Type='SecureString',
                Overwrite=False,
                Description=f"Password for login: {login}",
                Tags=[
                    {
                        'Key': 'Type',
                        'Value': 'Password'
                    },
                    {
                        'Key': 'Login',
                        'Value': login
                    }
                ]
            )
            return password
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterAlreadyExists':
                raise LoginAlreadyExistsError(f"Login '{login}' already exists. Use update to modify existing login.")
            else:
                raise AWSError(f"Failed to create login: {e}")
    
    def update_login(self, login: str, password: str) -> None:
        """
        Update password for existing login.
        
        Args:
            login: Login name
            password: New password
            
        Raises:
            ValidationError: If login or password is empty
            AWSError: If AWS operation fails
        """
        if not login:
            raise ValidationError("Login cannot be empty")
        if not password:
            raise ValidationError("Password cannot be empty")
        
        param_name = f"{self.prefix}{login}"
        
        try:
            # Update parameter value without tags (can't use tags with Overwrite=True)
            self.ssm.put_parameter(
                Name=param_name,
                Value=password,
                Type='SecureString',
                Overwrite=True,
                Description=f"Password for login: {login}"
            )
            
            # Update tags separately
            self.ssm.add_tags_to_resource(
                ResourceType='Parameter',
                ResourceId=param_name,
                Tags=[
                    {
                        'Key': 'Type',
                        'Value': 'Password'
                    },
                    {
                        'Key': 'Login',
                        'Value': login
                    }
                ]
            )
        except ClientError as e:
            raise AWSError(f"Failed to update login: {e}")
    
    def delete_login(self, login: str) -> None:
        """
        Delete a login.
        
        Args:
            login: Login name to delete
            
        Raises:
            ValidationError: If login is empty
            LoginNotFoundError: If login doesn't exist
            AWSError: If AWS operation fails
        """
        if not login:
            raise ValidationError("Login cannot be empty")
        
        param_name = f"{self.prefix}{login}"
        
        try:
            self.ssm.delete_parameter(Name=param_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                raise LoginNotFoundError(f"Login '{login}' not found")
            else:
                raise AWSError(f"Failed to delete login: {e}")
    
    def get_password(self, login: str) -> str:
        """
        Get password for a login.
        
        Args:
            login: Login name
            
        Returns:
            The password for the login
            
        Raises:
            ValidationError: If login is empty
            LoginNotFoundError: If login doesn't exist
            AWSError: If AWS operation fails
        """
        if not login:
            raise ValidationError("Login cannot be empty")
        
        param_name = f"{self.prefix}{login}"
        
        try:
            response = self.ssm.get_parameter(Name=param_name, WithDecryption=True)
            return response['Parameter']['Value']
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                raise LoginNotFoundError(f"Login '{login}' not found")
            else:
                raise AWSError(f"Failed to get password: {e}")
    
    def rotate_password(self, login: str, length: int = 16) -> str:
        """
        Rotate password for existing login.
        
        Args:
            login: Login name
            length: New password length (minimum 8)
            
        Returns:
            The new password
            
        Raises:
            ValidationError: If login is empty
            LoginNotFoundError: If login doesn't exist
            AWSError: If AWS operation fails
        """
        if not login:
            raise ValidationError("Login cannot be empty")
        
        # Verify login exists first
        self.get_password(login)  # This will raise LoginNotFoundError if not found
        
        new_password = self._generate_password(length)
        self.update_login(login, new_password)
        return new_password
    
    def login_exists(self, login: str) -> bool:
        """
        Check if a login exists.
        
        Args:
            login: Login name to check
            
        Returns:
            True if login exists, False otherwise
            
        Raises:
            ValidationError: If login is empty
        """
        if not login:
            raise ValidationError("Login cannot be empty")
        
        try:
            self.get_password(login)
            return True
        except LoginNotFoundError:
            return False
    
    def get_login_info(self, login: str) -> Dict[str, str]:
        """
        Get detailed information about a login parameter.
        
        Args:
            login: Login name
            
        Returns:
            Dictionary with parameter metadata
            
        Raises:
            ValidationError: If login is empty
            LoginNotFoundError: If login doesn't exist
            AWSError: If AWS operation fails
        """
        if not login:
            raise ValidationError("Login cannot be empty")
        
        param_name = f"{self.prefix}{login}"
        
        try:
            response = self.ssm.describe_parameters(
                ParameterFilters=[
                    {
                        'Key': 'Name',
                        'Values': [param_name]
                    }
                ]
            )
            
            if not response['Parameters']:
                raise LoginNotFoundError(f"Login '{login}' not found")
            
            param = response['Parameters'][0]
            return {
                'name': param['Name'],
                'description': param.get('Description', ''),
                'type': param['Type'],
                'last_modified': param['LastModifiedDate'].isoformat(),
                'version': param['Version']
            }
        except ClientError as e:
            raise AWSError(f"Failed to get login info: {e}")
    
    def _generate_password(self, length: int = 16) -> str:
        """
        Generate a secure random password.
        
        Args:
            length: Password length (minimum 8)
            
        Returns:
            Secure random password
        """
        if length < 8:
            length = 8
        
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password