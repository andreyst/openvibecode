#!/usr/bin/env python3
"""
Flask Login App for AWS Lambda

A simple Flask application that provides login functionality using 
AWS SSM Parameter Store for credential validation.
"""

import os
import logging
import boto3
from botocore.exceptions import ClientError
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from ssm_password_manager import PasswordManager, LoginNotFoundError, PasswordManagerError

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
limiter.init_app(app)

# Initialize password manager
try:
    pm = PasswordManager(
        prefix=os.environ.get('SSM_PREFIX', '/passwords/'),
        region=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    )
    logger.info(f"PasswordManager initialized with prefix: {os.environ.get('SSM_PREFIX', '/passwords/')}, region: {os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')}")
except Exception as e:
    logger.error(f"Failed to initialize PasswordManager: {e}")
    pm = None

# Initialize EC2 client for instance status checking
try:
    ec2_client = boto3.client('ec2', region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))
    logger.info(f"EC2 client initialized for region: {os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')}")
except Exception as e:
    logger.error(f"Failed to initialize EC2 client: {e}")
    ec2_client = None


def get_instance_status(instance_id):
    """Get the status of an EC2 instance."""
    if not ec2_client or not instance_id:
        return {
            'status': 'unknown',
            'state': 'N/A',
            'error': 'EC2 client not available or instance ID not configured'
        }
    
    try:
        logger.info(f"Checking status for instance: {instance_id}")
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        
        if not response['Reservations']:
            return {
                'status': 'not_found',
                'state': 'N/A', 
                'error': f'Instance {instance_id} not found'
            }
        
        instance = response['Reservations'][0]['Instances'][0]
        instance_state = instance['State']['Name']
        
        # Auto-start instance if it's stopped
        auto_started = False
        if instance_state == 'stopped':
            logger.info(f"Instance {instance_id} is stopped. Attempting to start it automatically.")
            try:
                start_response = ec2_client.start_instances(InstanceIds=[instance_id])
                logger.info(f"Start command sent for instance {instance_id}: {start_response}")
                instance_state = 'pending'  # Update state to reflect starting
                auto_started = True
            except ClientError as start_error:
                logger.error(f"Failed to auto-start instance {instance_id}: {start_error}")
                # Continue with the original stopped state
        
        # Get instance status checks
        status_response = ec2_client.describe_instance_status(InstanceIds=[instance_id])
        
        status_info = {
            'instance_id': instance_id,
            'state': instance_state,
            'instance_type': instance.get('InstanceType', 'N/A'),
            'launch_time': instance.get('LaunchTime', 'N/A'),
            'private_ip': instance.get('PrivateIpAddress', 'N/A'),
            'public_ip': instance.get('PublicIpAddress', 'N/A'),
            'status': 'running' if instance_state == 'running' else instance_state,
            'auto_started': auto_started
        }
        
        # Add status checks if available
        if status_response['InstanceStatuses']:
            status_check = status_response['InstanceStatuses'][0]
            status_info.update({
                'system_status': status_check['SystemStatus']['Status'],
                'instance_status': status_check['InstanceStatus']['Status']
            })
        else:
            status_info.update({
                'system_status': 'N/A',
                'instance_status': 'N/A'
            })
        
        logger.info(f"Instance {instance_id} status: {instance_state}")
        return status_info
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidInstanceID.NotFound':
            error_msg = f'Instance {instance_id} not found'
        elif error_code == 'UnauthorizedOperation':
            error_msg = 'Access denied - insufficient permissions to describe instances'
        else:
            error_msg = f'AWS error: {e.response["Error"]["Message"]}'
        
        logger.error(f"Error checking instance {instance_id}: {error_msg}")
        return {
            'status': 'error',
            'state': 'N/A',
            'error': error_msg
        }
    except Exception as e:
        logger.error(f"Unexpected error checking instance {instance_id}: {e}")
        return {
            'status': 'error',
            'state': 'N/A',
            'error': f'Unexpected error: {str(e)}'
        }


@app.route('/')
def index():
    """Home page - redirect to login if not authenticated."""
    if 'logged_in' in session and session['logged_in']:
        # Get control instance status
        control_instance_id = os.environ.get('CONTROL_INSTANCE_ID')
        instance_status = None
        
        if control_instance_id:
            instance_status = get_instance_status(control_instance_id)
        else:
            logger.warning("CONTROL_INSTANCE_ID environment variable not set")
        
        return render_template('dashboard.html', 
                             username=session.get('username'),
                             instance_status=instance_status,
                             control_instance_id=control_instance_id)
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """Login page and authentication handler."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        logger.info(f"Login attempt for username: '{username}'")
        
        if not pm:
            logger.error("PasswordManager not initialized")
            flash('System error: Password manager not available', 'error')
            return render_template('login.html')
        
        if not username or not password:
            logger.warning(f"Empty credentials provided - username: '{username}', password: {'***' if password else 'empty'}")
            flash('Please enter both username and password', 'error')
            return render_template('login.html')
        
        try:
            # Check if login exists and verify password
            logger.info(f"Checking if login exists: '{username}'")
            exists = pm.login_exists(username)
            logger.info(f"Login exists result for '{username}': {exists}")
            
            if exists:
                logger.info(f"Attempting to get password for '{username}'")
                stored_password = pm.get_password(username)
                logger.info(f"Retrieved password for '{username}' (length: {len(stored_password) if stored_password else 0})")
                
                if password == stored_password:
                    # Successful login
                    logger.info(f"Successful login for '{username}'")
                    session['logged_in'] = True
                    session['username'] = username
                    flash(f'Welcome, {username}!', 'success')
                    return redirect(url_for('index'))
                else:
                    logger.warning(f"Password mismatch for '{username}' - provided: {len(password)} chars, stored: {len(stored_password) if stored_password else 0} chars")
                    flash('Invalid username or password', 'error')
            else:
                logger.warning(f"Login does not exist: '{username}'")
                flash('Invalid username or password', 'error')
        
        except PasswordManagerError as e:
            logger.error(f"PasswordManagerError during login for '{username}': {e}")
            flash(f'Authentication error: {e}', 'error')
        except Exception as e:
            logger.error(f"Unexpected error during login for '{username}': {e}")
            flash('System error occurred. Please try again.', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout handler."""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))


@app.errorhandler(404)
def not_found(error):
    """404 error handler."""
    return render_template('error.html', error_code=404, error_message='Page not found'), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    return render_template('error.html', error_code=500, error_message='Internal server error'), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    """Rate limit exceeded handler."""
    logger.warning(f"Rate limit exceeded for IP: {get_remote_address()}")
    flash('Too many login attempts. Please try again later.', 'error')
    return render_template('login.html'), 429


# Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler using serverless-wsgi."""
    try:
        import serverless_wsgi
        return serverless_wsgi.handle_request(app, event, context)
    except ImportError:
        # Fallback for local development
        return {
            'statusCode': 500,
            'body': 'serverless-wsgi not available'
        }


if __name__ == '__main__':
    # Local development server
    app.run(debug=True, host='0.0.0.0', port=5000)