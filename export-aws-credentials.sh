#!/bin/bash
# Export AWS credentials to a profile for boto3/Python SDK usage
# Usage: ./export-aws-credentials.sh [profile-name]

PROFILE_NAME="${1:-temp-profile}"
CREDENTIALS_FILE="$HOME/.aws/credentials"

echo "Fetching current AWS credentials..."

# Get current caller identity to verify credentials work
if ! aws sts get-caller-identity &>/dev/null; then
    echo "Error: No valid AWS credentials found. Please run 'aws login' first."
    exit 1
fi

# Get temporary credentials using current session
# This works by having AWS CLI export its current credentials
echo "Exporting credentials to profile: $PROFILE_NAME"

# Get the credentials from environment or AWS CLI cache
# AWS CLI stores credentials differently depending on auth method
# We'll use aws configure to set them up properly

# Method 1: Try to get session token (works for IAM users)
if aws sts get-session-token --duration-seconds 3600 &>/dev/null; then
    CREDS=$(aws sts get-session-token --duration-seconds 3600 --output json)
    
    ACCESS_KEY=$(echo "$CREDS" | grep -o '"AccessKeyId": "[^"]*' | cut -d'"' -f4)
    SECRET_KEY=$(echo "$CREDS" | grep -o '"SecretAccessKey": "[^"]*' | cut -d'"' -f4)
    SESSION_TOKEN=$(echo "$CREDS" | grep -o '"SessionToken": "[^"]*' | cut -d'"' -f4)
    
    # Write to credentials file
    if [ ! -f "$CREDENTIALS_FILE" ]; then
        touch "$CREDENTIALS_FILE"
        chmod 600 "$CREDENTIALS_FILE"
    fi
    
    # Remove existing profile if it exists
    sed -i "/^\[$PROFILE_NAME\]/,/^$/d" "$CREDENTIALS_FILE" 2>/dev/null
    
    # Append new profile
    cat >> "$CREDENTIALS_FILE" << EOF

[$PROFILE_NAME]
aws_access_key_id = $ACCESS_KEY
aws_secret_access_key = $SECRET_KEY
aws_session_token = $SESSION_TOKEN
EOF
    
    echo "✓ Credentials exported successfully to profile: $PROFILE_NAME"
    echo "  Access Key: ${ACCESS_KEY:0:10}..."
    echo "  Expires: in 1 hour"
    
else
    # Method 2: For SSO or other auth methods, try to extract from CLI cache
    echo "Note: Using alternative credential export method..."
    
    # Get AWS CLI's cached credentials
    # This is a workaround for SSO and other auth methods
    AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id 2>/dev/null)
    AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key 2>/dev/null)
    AWS_SESSION_TOKEN=$(aws configure get aws_session_token 2>/dev/null)
    
    if [ -z "$AWS_ACCESS_KEY_ID" ]; then
        # Try to get from environment
        if [ -n "$AWS_ACCESS_KEY_ID" ] || [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
            echo "Using credentials from environment variables"
        else
            echo "Warning: Could not extract credentials automatically."
            echo "Your AWS CLI is authenticated but credentials are not in a standard format."
            echo ""
            echo "Alternative: Run this command to get credentials manually:"
            echo "  aws sts get-session-token --duration-seconds 3600"
            echo ""
            echo "Or if using SSO, the credentials are cached in:"
            echo "  ~/.aws/sso/cache/"
            echo ""
            echo "For SSO users, boto3 should work if you configure it to use SSO."
            exit 1
        fi
    fi
    
    # Write to credentials file
    if [ ! -f "$CREDENTIALS_FILE" ]; then
        touch "$CREDENTIALS_FILE"
        chmod 600 "$CREDENTIALS_FILE"
    fi
    
    # Remove existing profile if it exists
    sed -i "/^\[$PROFILE_NAME\]/,/^$/d" "$CREDENTIALS_FILE" 2>/dev/null
    
    # Append new profile
    cat >> "$CREDENTIALS_FILE" << EOF

[$PROFILE_NAME]
aws_access_key_id = $AWS_ACCESS_KEY_ID
aws_secret_access_key = $AWS_SECRET_ACCESS_KEY
EOF
    
    if [ -n "$AWS_SESSION_TOKEN" ]; then
        echo "aws_session_token = $AWS_SESSION_TOKEN" >> "$CREDENTIALS_FILE"
    fi
    
    echo "✓ Credentials exported to profile: $PROFILE_NAME"
fi

echo ""
echo "To use this profile:"
echo "  export AWS_PROFILE=$PROFILE_NAME"
echo "  python3 ec2-cost-optimizer.py"
echo ""
echo "Or the Python script will use it automatically if configured."
