# SSM Password Manager

A Python library and CLI tool for managing login-password pairs stored as SecureString parameters in AWS SSM Parameter Store.

## Features

- **Secure Storage**: Uses AWS SSM Parameter Store SecureString type for encryption at rest
- **Library & CLI**: Use as a Python library in your applications or as a command-line tool
- **Password Generation**: Automatic generation of cryptographically secure passwords
- **Comprehensive Management**: Create, read, update, delete, and rotate passwords
- **Tagging Support**: Automatic tagging for organization and compliance
- **Error Handling**: Comprehensive exception handling with specific error types

## Installation

### From Source

```bash
git clone <repository-url>
cd ssm-password-manager
pip install -e .
```

### Install with Development Dependencies

```bash
pip install -e ".[dev]"
```

## Library Usage

```python
from ssm_password_manager import PasswordManager, LoginNotFoundError

# Initialize password manager
pm = PasswordManager(prefix="/my-app/passwords/", region="us-east-1")

# Create a new login with auto-generated password
password = pm.create_login("api-user")
print(f"Generated password: {password}")

# Create a login with custom password
pm.create_login("admin", "MySecurePassword123!")

# List all logins
logins = pm.list_logins()
print(f"Available logins: {logins}")

# Get a password
try:
    password = pm.get_password("api-user")
    print(f"Password: {password}")
except LoginNotFoundError:
    print("Login not found")

# Update a password
pm.update_login("api-user", "NewPassword456!")

# Rotate a password (generates new random password)
new_password = pm.rotate_password("api-user", length=20)
print(f"New password: {new_password}")

# Check if login exists
if pm.login_exists("api-user"):
    print("Login exists")

# Get detailed login information
info = pm.get_login_info("api-user")
print(f"Last modified: {info['last_modified']}")

# Delete a login
pm.delete_login("api-user")
```

## CLI Usage

### Setup AWS Credentials

```bash
aws configure
# or set environment variables:
# export AWS_ACCESS_KEY_ID=your_key
# export AWS_SECRET_ACCESS_KEY=your_secret
# export AWS_DEFAULT_REGION=us-east-1
```

### Command Examples

```bash
# List all logins
python password_manager.py list

# Create login with auto-generated password
python password_manager.py create myuser

# Create login with custom password
python password_manager.py create myuser --password "MyPassword123!"

# Get password for a login
python password_manager.py get myuser

# Update password
python password_manager.py update myuser "NewPassword456!"

# Rotate password (generates new random password)
python password_manager.py rotate myuser --length 24

# Check if login exists
python password_manager.py exists myuser

# Get detailed login information
python password_manager.py info myuser

# Delete login
python password_manager.py delete myuser

# Use custom prefix and region
python password_manager.py --prefix "/myapp/creds/" --region "eu-west-1" list
```

## Exception Handling

The library provides specific exception types for different error conditions:

```python
from ssm_password_manager import (
    PasswordManager,
    PasswordManagerError,      # Base exception
    LoginNotFoundError,        # Login doesn't exist
    LoginAlreadyExistsError,   # Login already exists
    ValidationError,           # Invalid input
    AWSError                   # AWS operation failed
)

try:
    pm.create_login("existing-user", "password")
except LoginAlreadyExistsError:
    print("User already exists, updating instead...")
    pm.update_login("existing-user", "password")
except AWSError as e:
    print(f"AWS error: {e}")
except ValidationError as e:
    print(f"Invalid input: {e}")
```

## IAM Permissions

Your AWS credentials need the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:PutParameter",
                "ssm:DeleteParameter",
                "ssm:DescribeParameters",
                "ssm:AddTagsToResource"
            ],
            "Resource": "arn:aws:ssm:*:*:parameter/passwords/*"
        },
        {
            "Effect": "Allow",
            "Action": "ssm:DescribeParameters",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "kms:Decrypt",
            "Resource": "arn:aws:kms:*:*:key/*",
            "Condition": {
                "StringLike": {
                    "kms:ViaService": "ssm.*.amazonaws.com"
                }
            }
        }
    ]
}
```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run tests
AWS_DEFAULT_REGION=us-east-1 python test_library.py

# Or use pytest
python -m pytest test_library.py -v
```

## Security Considerations

- **Encryption**: All passwords are stored as SecureString parameters, encrypted at rest using AWS KMS
- **Access Control**: Use IAM policies to restrict access to specific parameter paths
- **Auditing**: AWS CloudTrail logs all parameter store operations for audit purposes
- **Password Generation**: Uses `secrets` module for cryptographically secure random password generation
- **No Local Storage**: Passwords are never stored locally, only in AWS SSM Parameter Store

## Parameter Naming Convention

By default, parameters are stored with the naming convention:
- Prefix: `/passwords/`
- Full path: `/passwords/{login_name}`

You can customize the prefix when initializing the PasswordManager.

## Tags

Each parameter is automatically tagged with:
- `Type`: `Password`
- `Login`: `{login_name}`

These tags help with organization, cost tracking, and compliance reporting.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.