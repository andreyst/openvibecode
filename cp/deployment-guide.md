# Flask SSM Login App - Deployment Guide

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Node.js and npm installed
3. Serverless Framework installed globally: `npm install -g serverless`
4. Python 3.9+ and pip

## Setup for Lambda Deployment

### 1. Install Serverless Plugins

```bash
npm install serverless-python-requirements serverless-wsgi
```

### 2. Install Python Dependencies

```bash
pip install -r flask-requirements.txt
```

### 3. Set Environment Variables

```bash
export FLASK_SECRET_KEY="your-secure-secret-key-here"
export SSM_PREFIX="/passwords/"
```

### 4. Deploy to AWS Lambda

```bash
# Deploy to dev stage
serverless deploy

# Deploy to production stage
serverless deploy --stage prod

# Deploy to specific region
serverless deploy --region eu-west-1
```

### 5. Create Test Users in SSM

Use the password manager CLI to create test users:

```bash
python password_manager.py create testuser --password testpass123
python password_manager.py create admin --password admin123
```

## Local Development

### 1. Install Dependencies

```bash
pip install -r flask-requirements.txt
```

### 2. Set Environment Variables

```bash
export AWS_DEFAULT_REGION=us-east-1
export SSM_PREFIX="/passwords/"
export FLASK_SECRET_KEY="dev-key"
```

### 3. Run Locally

```bash
python app.py
```

Visit `http://localhost:5000` to access the login page.

## Configuration

### Environment Variables

- `FLASK_SECRET_KEY`: Secret key for Flask sessions (required for production)
- `SSM_PREFIX`: Prefix for SSM parameters (default: `/passwords/`)
- `AWS_DEFAULT_REGION`: AWS region for SSM operations

### IAM Permissions

The Lambda function needs the following IAM permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:DescribeParameters"
            ],
            "Resource": "arn:aws:ssm:*:*:parameter/passwords/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt"
            ],
            "Resource": "*",
            "Condition": {
                "StringLike": {
                    "kms:ViaService": "ssm.*.amazonaws.com"
                }
            }
        }
    ]
}
```

## Security Notes

1. Always use a strong `FLASK_SECRET_KEY` in production
2. Use HTTPS in production (API Gateway provides this automatically)
3. Consider implementing rate limiting for login attempts
4. Passwords are stored encrypted in SSM Parameter Store as SecureString parameters
5. The application uses Flask sessions for authentication state

## Troubleshooting

### Common Issues

1. **NoRegionError**: Set `AWS_DEFAULT_REGION` environment variable
2. **AccessDenied**: Ensure IAM permissions are correctly configured
3. **ParameterNotFound**: Verify SSM parameters exist with correct prefix
4. **ImportError**: Install all required dependencies from flask-requirements.txt

### Testing Authentication

Create a test user and verify login:

```bash
# Create test user
python password_manager.py create testuser --password mypassword123

# Verify user exists
python password_manager.py exists testuser

# Test login with created credentials
```