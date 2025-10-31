#!/usr/bin/env python3
"""
Test suite for SSM Password Manager Library

Uses moto library to mock AWS services for comprehensive testing.
"""

import unittest
import boto3
import json
from unittest.mock import patch, MagicMock
from moto import mock_aws
from ssm_password_manager import (
    PasswordManager,
    PasswordManagerError,
    LoginNotFoundError,
    LoginAlreadyExistsError,
    ValidationError,
    AWSError
)
import argparse
import io
import sys
from contextlib import redirect_stdout, redirect_stderr


class TestPasswordManagerLibrary(unittest.TestCase):
    """Test cases for PasswordManager library."""
    
    @mock_aws
    def setUp(self):
        """Set up test environment with mocked AWS services."""
        import os
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        self.pm = PasswordManager("/test-passwords/")
        
    @mock_aws
    def test_create_login_with_generated_password(self):
        """Test creating login with auto-generated password."""
        password = self.pm.create_login("testuser")
        
        # Verify password was generated and stored
        self.assertIsNotNone(password)
        self.assertGreaterEqual(len(password), 16)
        
        # Verify parameter exists in SSM
        stored_password = self.pm.get_password("testuser")
        self.assertEqual(password, stored_password)
    
    @mock_aws
    def test_create_login_with_custom_password(self):
        """Test creating login with custom password."""
        custom_password = "MyCustomPassword123!"
        password = self.pm.create_login("testuser", custom_password)
        
        self.assertEqual(password, custom_password)
        stored_password = self.pm.get_password("testuser")
        self.assertEqual(stored_password, custom_password)
    
    @mock_aws
    def test_create_duplicate_login(self):
        """Test creating duplicate login should fail."""
        self.pm.create_login("testuser", "password123")
        
        with self.assertRaises(LoginAlreadyExistsError):
            self.pm.create_login("testuser", "password456")
    
    @mock_aws
    def test_update_login(self):
        """Test updating existing login password."""
        # Create initial login
        self.pm.create_login("testuser", "oldpassword")
        
        # Update password
        new_password = "newpassword123"
        self.pm.update_login("testuser", new_password)
        
        # Verify password was updated
        stored_password = self.pm.get_password("testuser")
        self.assertEqual(stored_password, new_password)
    
    @mock_aws
    def test_delete_login(self):
        """Test deleting login."""
        # Create login
        self.pm.create_login("testuser", "password123")
        
        # Verify it exists
        self.assertEqual(self.pm.get_password("testuser"), "password123")
        
        # Delete login
        self.pm.delete_login("testuser")
        
        # Verify it's gone
        with self.assertRaises(LoginNotFoundError):
            self.pm.get_password("testuser")
    
    @mock_aws
    def test_delete_nonexistent_login(self):
        """Test deleting non-existent login should fail."""
        with self.assertRaises(LoginNotFoundError):
            self.pm.delete_login("nonexistent")
    
    @mock_aws
    def test_list_logins(self):
        """Test listing all logins."""
        # Initially empty
        logins = self.pm.list_logins()
        self.assertEqual(logins, [])
        
        # Add some logins
        self.pm.create_login("user1", "pass1")
        self.pm.create_login("user2", "pass2")
        self.pm.create_login("user3", "pass3")
        
        # List should contain all logins in sorted order
        logins = self.pm.list_logins()
        self.assertEqual(logins, ["user1", "user2", "user3"])
    
    @mock_aws
    def test_rotate_password(self):
        """Test password rotation."""
        # Create initial login
        original_password = "originalpass123"
        self.pm.create_login("testuser", original_password)
        
        # Rotate password
        new_password = self.pm.rotate_password("testuser")
        
        # Verify password changed
        self.assertNotEqual(new_password, original_password)
        self.assertGreaterEqual(len(new_password), 16)
        
        # Verify new password is stored
        stored_password = self.pm.get_password("testuser")
        self.assertEqual(stored_password, new_password)
    
    @mock_aws
    def test_rotate_password_custom_length(self):
        """Test password rotation with custom length."""
        self.pm.create_login("testuser", "oldpass")
        
        new_password = self.pm.rotate_password("testuser", length=24)
        self.assertEqual(len(new_password), 24)
    
    @mock_aws
    def test_rotate_nonexistent_login(self):
        """Test rotating password for non-existent login should fail."""
        with self.assertRaises(LoginNotFoundError):
            self.pm.rotate_password("nonexistent")
    
    @mock_aws
    def test_get_nonexistent_password(self):
        """Test getting password for non-existent login should fail."""
        with self.assertRaises(LoginNotFoundError):
            self.pm.get_password("nonexistent")
    
    @mock_aws
    def test_login_exists(self):
        """Test checking if login exists."""
        # Initially doesn't exist
        self.assertFalse(self.pm.login_exists("testuser"))
        
        # Create login
        self.pm.create_login("testuser", "password123")
        
        # Now it exists
        self.assertTrue(self.pm.login_exists("testuser"))
        
        # Delete login
        self.pm.delete_login("testuser")
        
        # Doesn't exist again
        self.assertFalse(self.pm.login_exists("testuser"))
    
    @mock_aws
    def test_get_login_info(self):
        """Test getting detailed login information."""
        self.pm.create_login("testuser", "password123")
        
        info = self.pm.get_login_info("testuser")
        
        self.assertIn('name', info)
        self.assertIn('description', info)
        self.assertIn('type', info)
        self.assertIn('last_modified', info)
        self.assertIn('version', info)
        
        self.assertEqual(info['type'], 'SecureString')
        self.assertIn("testuser", info['description'])
    
    @mock_aws
    def test_get_login_info_nonexistent(self):
        """Test getting info for non-existent login should fail."""
        with self.assertRaises(LoginNotFoundError):
            self.pm.get_login_info("nonexistent")
    
    def test_validation_errors(self):
        """Test validation for empty inputs."""
        with self.assertRaises(ValidationError):
            self.pm.create_login("")
        
        with self.assertRaises(ValidationError):
            self.pm.update_login("", "password")
        
        with self.assertRaises(ValidationError):
            self.pm.update_login("user", "")
        
        with self.assertRaises(ValidationError):
            self.pm.delete_login("")
        
        with self.assertRaises(ValidationError):
            self.pm.get_password("")
        
        with self.assertRaises(ValidationError):
            self.pm.rotate_password("")
        
        with self.assertRaises(ValidationError):
            self.pm.login_exists("")
        
        with self.assertRaises(ValidationError):
            self.pm.get_login_info("")
    
    def test_password_generation(self):
        """Test password generation function."""
        password1 = self.pm._generate_password()
        password2 = self.pm._generate_password()
        
        # Passwords should be different
        self.assertNotEqual(password1, password2)
        
        # Should meet minimum length
        self.assertGreaterEqual(len(password1), 16)
        self.assertGreaterEqual(len(password2), 16)
        
        # Test custom length
        short_password = self.pm._generate_password(8)
        self.assertEqual(len(short_password), 8)
        
        # Test minimum length enforcement
        min_password = self.pm._generate_password(4)
        self.assertEqual(len(min_password), 8)  # Should be enforced to minimum
    
    @mock_aws
    def test_custom_prefix_and_region(self):
        """Test custom prefix and region initialization."""
        pm_custom = PasswordManager("/custom-prefix/", "us-west-2")
        
        # Test that prefix is used correctly
        pm_custom.create_login("testuser", "password123")
        password = pm_custom.get_password("testuser")
        self.assertEqual(password, "password123")


class TestIntegrationWorkflow(unittest.TestCase):
    """Integration tests using actual mocked AWS services."""
    
    @mock_aws
    def test_full_workflow(self):
        """Test complete workflow: create, list, get, update, rotate, delete."""
        import os
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        pm = PasswordManager("/integration-test/")
        
        # Start with empty list
        self.assertEqual(pm.list_logins(), [])
        
        # Create login
        password1 = pm.create_login("testuser")
        self.assertIsNotNone(password1)
        
        # Login should exist
        self.assertTrue(pm.login_exists("testuser"))
        
        # List should show the login
        self.assertEqual(pm.list_logins(), ["testuser"])
        
        # Get password
        retrieved_password = pm.get_password("testuser")
        self.assertEqual(retrieved_password, password1)
        
        # Get login info
        info = pm.get_login_info("testuser")
        self.assertEqual(info['type'], 'SecureString')
        
        # Update password
        new_password = "updated_password_123"
        pm.update_login("testuser", new_password)
        self.assertEqual(pm.get_password("testuser"), new_password)
        
        # Rotate password
        rotated_password = pm.rotate_password("testuser")
        self.assertNotEqual(rotated_password, new_password)
        self.assertEqual(pm.get_password("testuser"), rotated_password)
        
        # Delete login
        pm.delete_login("testuser")
        self.assertEqual(pm.list_logins(), [])
        self.assertFalse(pm.login_exists("testuser"))
        
        # Verify it's gone
        with self.assertRaises(LoginNotFoundError):
            pm.get_password("testuser")


if __name__ == '__main__':
    # Check if moto is available
    try:
        import moto
    except ImportError:
        print("Error: moto library is required for testing.")
        print("Install with: pip install moto[ssm]")
        sys.exit(1)
    
    unittest.main(verbosity=2)