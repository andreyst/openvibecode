# OpenVibeCode IAM Policy

## Overview

The `openvibecode-policy.json` file contains the comprehensive IAM policy for the OpenVibeCode system, combining password management, instance monitoring, and hibernation control capabilities.

## Policy Sections

### 1. SSM Parameter Store - Password Management
**Purpose**: Manage encrypted login credentials stored in AWS SSM Parameter Store

**Permissions**:
- `ssm:GetParameter`, `ssm:GetParameters` - Retrieve stored passwords
- `ssm:PutParameter` - Create/update password entries  
- `ssm:DeleteParameter` - Remove password entries
- `ssm:DescribeParameters` - List available passwords
- `ssm:AddTagsToResource` - Tag password parameters

**Resource Scope**: `/passwords/*` parameter prefix

### 2. KMS Decryption
**Purpose**: Decrypt SecureString parameters in SSM

**Permissions**:
- `kms:Decrypt` - Decrypt SSM SecureString parameters

**Conditions**: Only for SSM service (`kms:ViaService: ssm.*.amazonaws.com`)

### 3. EC2 Instance Monitoring  
**Purpose**: Monitor EC2 instance status and health checks

**Permissions**:
- `ec2:DescribeInstances` - Get instance state and details
- `ec2:DescribeInstanceStatus` - Get system/instance status checks
- `ec2:DescribeInstanceAttribute` - Get instance configuration

**Resource Scope**: All instances (`*`)
**Security Note**: Read-only operations without tag restrictions (application-level filtering recommended)

### 4. EC2 Instance Hibernation Control
**Purpose**: Control instance hibernation and power states

**Permissions**:
- `ec2:StopInstances` - Stop/hibernate instances
- `ec2:StartInstances` - Start/resume instances  
- `ec2:RebootInstances` - Restart instances

**Resource Scope**: EC2 instances only
**Security Condition**: Only instances tagged with `Environment: openvibecode`


## Security Features

### Tag-Based Access Control
- **EC2 control operations** (start/stop/reboot) are restricted to instances with the `Environment: openvibecode` tag
- **EC2 monitoring operations** allow read access to all instances (filtered at application level)
- This prevents accidental control of unrelated instances while allowing monitoring
- Provides fine-grained access control for destructive operations

### Principle of Least Privilege
- SSM permissions limited to `/passwords/*` prefix
- KMS permissions limited to SSM service context
- EC2 control permissions require specific resource tags

### Resource Restrictions
- SSM operations scoped to password-related parameters only
- **EC2 control operations** limited to tagged instances only
- **EC2 monitoring operations** allow read access (application filters by tags)

## Usage Instructions

### 1. Apply Policy to IAM Role/User
```bash
# Create IAM policy
aws iam create-policy \
    --policy-name OpenVibeCodePolicy \
    --policy-document file://openvibecode-policy.json

# Attach to existing role
aws iam attach-role-policy \
    --role-name YourRoleName \
    --policy-arn arn:aws:iam::ACCOUNT-ID:policy/OpenVibeCodePolicy
```

### 2. Tag Target EC2 Instances
```bash
# Tag instances for hibernation control
aws ec2 create-tags \
    --resources i-1234567890abcdef0 \
    --tags Key=Environment,Value=openvibecode
```

### 3. Set Environment Variables
```bash
export CONTROL_INSTANCE_ID=i-1234567890abcdef0
export SSM_PREFIX=/passwords/
export AWS_DEFAULT_REGION=us-east-1
```

## Flask Application Integration

This policy supports the following Flask app capabilities:

1. **Authentication**: Login validation using SSM-stored credentials
2. **Password Management**: CLI tools for password rotation and management  
3. **Instance Monitoring**: Real-time EC2 instance status display
4. **Instance Control**: Future hibernation/resume functionality

## Lambda Deployment

When deploying to AWS Lambda, this policy provides:
- Access to SSM for user authentication
- EC2 monitoring for dashboard status display
- Instance control capabilities for hibernation features
- Secure, tag-based access controls

## Compliance Notes

- Follows AWS security best practices
- Implements resource-based restrictions
- Uses condition-based access controls
- Maintains audit trail through CloudTrail
- Supports least-privilege access model

## Troubleshooting

### Common Issues

1. **SSM Access Denied**: Verify parameter prefix matches `/passwords/*`
2. **EC2 Monitoring Failed**: Check if policy is attached to correct role
3. **Instance Control Denied**: Ensure target instance has `Environment: openvibecode` tag
4. **KMS Decryption Failed**: Verify KMS key permissions for SSM service

### Testing Policy

```bash
# Test SSM access
aws ssm get-parameter --name "/passwords/testuser" --with-decryption

# Test EC2 monitoring  
aws ec2 describe-instances --instance-ids i-1234567890abcdef0

# Test EC2 control (on tagged instance)
aws ec2 stop-instances --instance-ids i-1234567890abcdef0
```