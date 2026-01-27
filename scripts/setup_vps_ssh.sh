#!/bin/bash
# Script to help set up SSH key for VPS deployment

VPS_HOST="5.189.180.67"
VPS_DOMAIN="channel-manager.revnext.in"
KEY_NAME="vps_channel_manager"
KEY_PATH="$HOME/.ssh/$KEY_NAME"

echo "=== VPS SSH Key Setup for GitHub Actions ==="
echo ""
echo "VPS Details:"
echo "  Host: $VPS_HOST"
echo "  Domain: $VPS_DOMAIN"
echo ""

# Check if key already exists
if [ -f "$KEY_PATH" ]; then
    echo "⚠️  SSH key already exists at: $KEY_PATH"
    read -p "Do you want to generate a new one? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing key..."
        KEY_EXISTS=true
    else
        KEY_EXISTS=false
    fi
else
    KEY_EXISTS=false
fi

# Generate key if needed
if [ "$KEY_EXISTS" = false ]; then
    echo ""
    echo "Step 1: Generating SSH key pair..."
    ssh-keygen -t ed25519 -C "github-actions-channel-manager" -f "$KEY_PATH" -N ""
    
    if [ $? -eq 0 ]; then
        echo "✅ SSH key generated successfully!"
    else
        echo "❌ Failed to generate SSH key"
        exit 1
    fi
fi

# Display public key
echo ""
echo "Step 2: Your public key (add this to VPS):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat "$KEY_PATH.pub"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ask for VPS username
read -p "Enter your VPS username (default: root): " VPS_USER
VPS_USER=${VPS_USER:-root}

echo ""
echo "Step 3: Copying public key to VPS..."
echo "You may be prompted for your VPS password..."

# Try to copy key
ssh-copy-id -i "$KEY_PATH.pub" "$VPS_USER@$VPS_HOST" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Public key copied to VPS successfully!"
else
    echo ""
    echo "⚠️  Automatic copy failed. Please manually add the public key:"
    echo ""
    echo "1. SSH into your VPS:"
    echo "   ssh $VPS_USER@$VPS_HOST"
    echo ""
    echo "2. On the VPS, run:"
    echo "   mkdir -p ~/.ssh"
    echo "   chmod 700 ~/.ssh"
    echo "   echo '$(cat $KEY_PATH.pub)' >> ~/.ssh/authorized_keys"
    echo "   chmod 600 ~/.ssh/authorized_keys"
    echo ""
fi

# Test connection
echo ""
echo "Step 4: Testing SSH connection..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$VPS_USER@$VPS_HOST" "echo 'SSH connection successful!'" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ SSH connection test passed!"
else
    echo "❌ SSH connection test failed"
    echo "Please verify:"
    echo "  - Public key is added to VPS ~/.ssh/authorized_keys"
    echo "  - VPS username is correct: $VPS_USER"
    echo "  - VPS is accessible: ping $VPS_HOST"
fi

# Display private key for GitHub
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Add this PRIVATE KEY to GitHub Secrets"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Go to: https://github.com/octavertexmedia/ChannelManager/settings/secrets/actions"
echo ""
echo "Add these secrets:"
echo ""
echo "1. Name: VPS_SSH_PRIVATE_KEY"
echo "   Value: (see below)"
echo ""
cat "$KEY_PATH"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "2. Name: VPS_HOST"
echo "   Value: $VPS_HOST"
echo ""
echo "3. Name: VPS_USER"
echo "   Value: $VPS_USER"
echo ""
echo "4. Name: VPS_DOMAIN"
echo "   Value: $VPS_DOMAIN"
echo ""
echo "✅ Setup complete!"
echo ""
echo "Next: Add secrets to GitHub and test deployment"

