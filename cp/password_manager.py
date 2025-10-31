#!/usr/bin/env python3
"""
AWS SSM Parameter Store Password Manager CLI

Command-line interface for managing login-password pairs stored in AWS SSM Parameter Store.
Uses the ssm_password_manager library for all operations.
"""

import argparse
import sys
from ssm_password_manager import (
    PasswordManager,
    PasswordManagerError,
    LoginNotFoundError,
    LoginAlreadyExistsError,
    ValidationError
)


def main():
    parser = argparse.ArgumentParser(description='AWS SSM Parameter Store Password Manager CLI')
    parser.add_argument('--prefix', default='/passwords/', help='Parameter prefix (default: /passwords/)')
    parser.add_argument('--region', help='AWS region (uses default if not specified)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all logins')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new login')
    create_parser.add_argument('login', help='Login name')
    create_parser.add_argument('--password', help='Password (if not provided, will be generated)')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update existing login password')
    update_parser.add_argument('login', help='Login name')
    update_parser.add_argument('password', help='New password')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete login')
    delete_parser.add_argument('login', help='Login name')
    
    
    # Rotate command
    rotate_parser = subparsers.add_parser('rotate', help='Rotate password for login')
    rotate_parser.add_argument('login', help='Login name')
    rotate_parser.add_argument('--length', type=int, default=16, help='Password length (default: 16)')
    
    # Exists command
    exists_parser = subparsers.add_parser('exists', help='Check if login exists')
    exists_parser.add_argument('login', help='Login name')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get detailed information about a login')
    info_parser.add_argument('login', help='Login name')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        pm = PasswordManager(args.prefix, args.region)
        
        if args.command == 'list':
            logins = pm.list_logins()
            if logins:
                print("Available logins:")
                for login in logins:
                    print(f"  - {login}")
            else:
                print("No logins found")
        
        elif args.command == 'create':
            password = pm.create_login(args.login, args.password)
            if args.password:
                print(f"Login '{args.login}' created successfully")
            else:
                print(f"Login '{args.login}' created with generated password: {password}")
        
        elif args.command == 'update':
            pm.update_login(args.login, args.password)
            print(f"Password for login '{args.login}' updated successfully")
        
        elif args.command == 'delete':
            pm.delete_login(args.login)
            print(f"Login '{args.login}' deleted successfully")
        
        
        elif args.command == 'rotate':
            new_password = pm.rotate_password(args.login, args.length)
            print(f"Password for login '{args.login}' rotated. New password: {new_password}")
        
        elif args.command == 'exists':
            exists = pm.login_exists(args.login)
            if exists:
                print(f"Login '{args.login}' exists")
            else:
                print(f"Login '{args.login}' does not exist")
        
        elif args.command == 'info':
            info = pm.get_login_info(args.login)
            print(f"Login information for '{args.login}':")
            print(f"  Name: {info['name']}")
            print(f"  Description: {info['description']}")
            print(f"  Type: {info['type']}")
            print(f"  Last Modified: {info['last_modified']}")
            print(f"  Version: {info['version']}")
    
    except PasswordManagerError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()