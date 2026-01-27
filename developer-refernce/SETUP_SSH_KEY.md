# Setting Up SSH Key for GitHub Actions Deployment

This guide explains how to generate and configure SSH keys for deploying to your VPS at `5.189.180.67` (channel-manager.revnext.in).

## Step 1: Generate SSH Key Pair

On your **local machine**, generate a new SSH key pair:

```bash
# Generate SSH key (use a descriptive name)
ssh-keygen -t ed25519 -C "github-actions-channel-manager" -f ~/.ssh/vps_channel_manager

# Or if ed25519 is not supported, use RSA:
ssh-keygen -t rsa -b 4096 -C "github-actions-channel-manager" -f ~/.ssh/vps_channel_manager
```

**When prompted:**
- **Passphrase**: You can leave it empty for GitHub Actions (or set one if you prefer)
- This creates two files:
  - `~/.ssh/vps_channel_manager` (private key - **KEEP SECRET**)
  - `~/.ssh/vps_channel_manager.pub` (public key - safe to share)

## Step 2: Copy Public Key to VPS

You need to add the public key to your VPS so GitHub Actions can authenticate.

### Option A: Using ssh-copy-id (if you have password access)

```bash
# Copy public key to VPS
ssh-copy-id -i ~/.ssh/vps_channel_manager.pub user@5.189.180.67

# Replace 'user' with your actual VPS username (usually 'root' or your username)
```

### Option B: Manual Copy (if you have VPS access)

1. **Display your public key:**
   ```bash
   cat ~/.ssh/vps_channel_manager.pub
   ```

2. **SSH into your VPS:**
   ```bash
   ssh user@5.189.180.67
   ```

3. **On the VPS, add the public key:**
   ```bash
   # Create .ssh directory if it doesn't exist
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   
   # Add the public key to authorized_keys
   echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

   Replace `YOUR_PUBLIC_KEY_HERE` with the output from `cat ~/.ssh/vps_channel_manager.pub`

## Step 3: Test SSH Connection

Test that you can connect using the private key:

```bash
# Test connection
ssh -i ~/.ssh/vps_channel_manager user@5.189.180.67

# If successful, you should be logged into your VPS
# Exit with: exit
```

## Step 4: Get Private Key for GitHub Secrets

**Display your private key:**

```bash
cat ~/.ssh/vps_channel_manager
```

**Copy the entire output** - it should look like:
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
...
(many lines)
...
-----END OPENSSH PRIVATE KEY-----
```

## Step 5: Add to GitHub Secrets

1. **Go to your GitHub repository:**
   - Navigate to: `https://github.com/octavertexmedia/ChannelManager`

2. **Go to Settings:**
   - Click on **Settings** tab
   - Click on **Secrets and variables** → **Actions**

3. **Add the secrets:**
   
   Click **New repository secret** and add each:

   - **Name**: `VPS_SSH_PRIVATE_KEY`
     - **Value**: Paste the entire private key (from Step 4)
   
   - **Name**: `VPS_HOST`
     - **Value**: `5.189.180.67`
   
   - **Name**: `VPS_USER`
     - **Value**: Your VPS username (e.g., `root` or your username)
   
   - **Name**: `VPS_DOMAIN`
     - **Value**: `channel-manager.revnext.in`

## Step 6: Verify Setup

After adding the secrets, you can test the deployment by:

1. **Making a small change and pushing:**
   ```bash
   git commit --allow-empty -m "Test deployment"
   git push origin main
   ```

2. **Check GitHub Actions:**
   - Go to **Actions** tab in your repository
   - Watch the workflow run
   - Check if deployment succeeds

## Troubleshooting

### SSH Connection Fails

1. **Check VPS is accessible:**
   ```bash
   ping 5.189.180.67
   ```

2. **Check SSH service is running on VPS:**
   ```bash
   ssh user@5.189.180.67 "systemctl status ssh"
   ```

3. **Verify key permissions:**
   ```bash
   chmod 600 ~/.ssh/vps_channel_manager
   chmod 644 ~/.ssh/vps_channel_manager.pub
   ```

### GitHub Actions Deployment Fails

1. **Check secret names match exactly:**
   - `VPS_SSH_PRIVATE_KEY` (not `VPS_SSH_KEY` or similar)
   - `VPS_HOST` (not `VPS_IP`)
   - `VPS_USER` (not `VPS_USERNAME`)

2. **Verify private key format:**
   - Must include `-----BEGIN` and `-----END` lines
   - No extra spaces or line breaks
   - Copy the entire key including headers

3. **Check VPS firewall:**
   ```bash
   # On VPS, ensure SSH port 22 is open
   sudo ufw allow 22/tcp
   sudo ufw status
   ```

### Permission Denied Errors

1. **Check authorized_keys permissions on VPS:**
   ```bash
   chmod 600 ~/.ssh/authorized_keys
   chmod 700 ~/.ssh
   ```

2. **Verify user has write access to deployment directory:**
   ```bash
   # On VPS
   mkdir -p ~/channel-manager
   chmod 755 ~/channel-manager
   ```

## Security Best Practices

1. **Use a dedicated key for GitHub Actions** (not your personal SSH key)
2. **Restrict key usage** (optional - add to `~/.ssh/authorized_keys` on VPS):
   ```
   command="cd /home/user/channel-manager && $SSH_ORIGINAL_COMMAND",no-port-forwarding,no-X11-forwarding,no-agent-forwarding ssh-ed25519 AAAA... github-actions
   ```
3. **Rotate keys periodically**
4. **Monitor GitHub Actions logs** for unauthorized access attempts

## Quick Reference

```bash
# Generate key
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/vps_channel_manager

# Copy to VPS
ssh-copy-id -i ~/.ssh/vps_channel_manager.pub user@5.189.180.67

# Test connection
ssh -i ~/.ssh/vps_channel_manager user@5.189.180.67

# Get private key for GitHub
cat ~/.ssh/vps_channel_manager
```

## Next Steps

After setting up SSH keys:
1. ✅ Add secrets to GitHub
2. ✅ Test deployment with a push
3. ✅ Set up `.env` file on VPS
4. ✅ Configure domain and SSL
5. ✅ Monitor first deployment

