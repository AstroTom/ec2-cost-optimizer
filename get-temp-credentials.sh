#!/bin/bash
# Get temporary AWS credentials and export to profile
# Usage: ./get-temp-credentials.sh [profile-name]

PROFILE_NAME="${1:-temp-profile}"
CREDENTIALS_FILE="$HOME/.aws/credentials"

echo "Getting temporary credentials from AWS STS..."

# Verify AWS CLI is authenticated
if ! aws sts get-caller-identity &>/dev/null; then
    echo "Error: Not authenticated. Please run 'aws login' first."
    exit 1
fi

# Get caller identity
IDENTITY=$(aws sts get-caller-identity --output json)
echo "Current identity:"
echo "$IDENTITY" | grep -E '"UserId"|"Account"|"Arn"'
echo ""

# Try to get session token (this creates temporary credentials)
echo "Requesting session token..."
SESSION_OUTPUT=$(aws sts get-session-token --duration-seconds 3600 --output json 2>&1)

if [ $? -eq 0 ]; then
    # Successfully got session token
    ACCESS_KEY=$(echo "$SESSION_OUTPUT" | python3 -c "import sys, json; print(json.load(sys.stdin)['Credentials']['AccessKeyId'])")
    SECRET_KEY=$(echo "$SESSION_OUTPUT" | python3 -c "import sys, json; print(json.load(sys.stdin)['Credentials']['SecretAccessKey'])")
    SESSION_TOKEN=$(echo "$SESSION_OUTPUT" | python3 -c "import sys, json; print(json.load(sys.stdin)['Credentials']['SessionToken'])")
    EXPIRATION=$(echo "$SESSION_OUTPUT" | python3 -c "import sys, json; print(json.load(sys.stdin)['Credentials']['Expiration'])")
    
    # Create credentials file if it doesn't exist
    if [ ! -f "$CREDENTIALS_FILE" ]; then
        touch "$CREDENTIALS_FILE"
        chmod 600 "$CREDENTIALS_FILE"
    fi
    
    # Remove existing profile section
    if grep -q "^\[$PROFILE_NAME\]" "$CREDENTIALS_FILE" 2>/dev/null; then
        # Create temp file without the profile
        awk -v profile="[$PROFILE_NAME]" '
            $0 == profile { skip=1; next }
            /^\[/ { skip=0 }
            !skip { print }
        ' "$CREDENTIALS_FILE" > "${CREDENTIALS_FILE}.tmp"
        mv "${CREDENTIALS_FILE}.tmp" "$CREDENTIALS_FILE"
    fi
    
    # Append new credentials
    cat >> "$CREDENTIALS_FILE" << EOF

[$PROFILE_NAME]
aws_access_key_id = $ACCESS_KEY
aws_secret_access_key = $SECRET_KEY
aws_session_token = $SESSION_TOKEN
# Expires: $EXPIRATION
EOF
    
    echo "✓ Success! Credentials exported to profile: $PROFILE_NAME"
    echo "  Access Key: ${ACCESS_KEY:0:20}..."
    echo "  Expires: $EXPIRATION"
    echo ""
    echo "To use with Python:"
    echo "  python3 ec2-cost-optimizer.py $PROFILE_NAME"
    echo ""
    echo "Or set as default:"
    echo "  export AWS_PROFILE=$PROFILE_NAME"
    echo "  python3 ec2-cost-optimizer.py"
    
else
    echo "Note: get-session-token failed (this is normal for some auth types)"
    echo ""
    echo "Trying alternative: Using AWS CLI process credentials..."
    
    # For SSO and other auth methods, configure boto3 to use AWS CLI
    CONFIG_FILE="$HOME/.aws/config"
    
    # Check if profile already exists in config
    if ! grep -q "^\[profile $PROFILE_NAME\]" "$CONFIG_FILE" 2>/dev/null; then
        echo "" >> "$CONFIG_FILE"
        echo "[profile $PROFILE_NAME]" >> "$CONFIG_FILE"
        echo "credential_process = aws configure export-credentials --profile default --format process" >> "$CONFIG_FILE"
        echo "region = eu-west-1" >> "$CONFIG_FILE"
    fi
    
    echo "✓ Configured profile to use AWS CLI credentials: $PROFILE_NAME"
    echo ""
    echo "To use with Python:"
    echo "  python3 ec2-cost-optimizer.py $PROFILE_NAME"
fi
