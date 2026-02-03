#!/bin/bash
# render_init.sh
# Restores the SSH key from environment variable and starts the bot

# Create SSH directory
mkdir -p /root/.ssh

# Decode the base64 SSH key from env var if present
if [ -n "$SSH_PRIVATE_KEY_BASE64" ]; then
    echo "🔑 Restoring SSH key from environment variable..."
    echo "$SSH_PRIVATE_KEY_BASE64" | base64 -d > /root/.ssh/cpanel_mysql_key
    chmod 600 /root/.ssh/cpanel_mysql_key
elif [ -n "$SSH_KEY_PATH" ] && [ ! -f "$SSH_KEY_PATH" ]; then
    echo "⚠️ Warning: SSH_KEY_PATH is set but file not found. Ensure you added the key content to secrets."
fi

# Start the bot
python bot_main.py
