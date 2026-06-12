#!/bin/bash
# Bare-metal production deploy (systemd + Caddy, no Docker).
# Run on the prod box. See DEPLOY.md for the ONE-TIME setup that must happen
# before the first run (Postgres provisioning, strong secret, initial migrate).

# Slack Webhook URL (Optional)
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXXXX/YYYYY/ZZZZZ"

send_slack_message() {
    MESSAGE="$1"
    echo "$MESSAGE"
    # Uncomment to enable Slack:
    # curl -X POST -H 'Content-type: application/json' --data "{\"text\":\"$MESSAGE\"}" "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 &
}

send_slack_message "🚀 *Deployment started!* Pulling latest changes..."

cd /home/omni/flashcards || { send_slack_message "❌ Deployment failed! Could not find project directory."; exit 1; }

# Pull latest changes
GIT_OUTPUT=$(git pull origin main)
if [[ "$GIT_OUTPUT" == *"Already up to date."* ]]; then
    send_slack_message "😴 *No changes detected!* Deployment skipped."
    exit 0
fi

send_slack_message "✅ *Git pull successful!* Building production frontend..."

# Load Node.js environment
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 22.17.0

# Install and build
npm install && npm run build
if [ $? -ne 0 ]; then
    send_slack_message "❌ *Frontend build failed!*"
    exit 1
fi

# Restart Caddy service
sudo /bin/systemctl restart flashcardscaddy
send_slack_message "✅ *Frontend built and Caddy restarted!*"

# --- Backend ---
send_slack_message "🔧 *Building backend...*"
cd api || { send_slack_message "❌ Deployment failed! Could not find backend directory."; exit 1; }

source /home/omni/flashcards/api/.venv/bin/activate
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    send_slack_message "❌ *Backend dependency install failed!*"
    exit 1
fi

# Apply database migrations BEFORE restarting the service (Phase 2+: Postgres).
# Reads DATABASE_URL from api/.env. Fails the deploy if the schema can't be
# brought up to date rather than restarting into a broken state.
alembic upgrade head
if [ $? -ne 0 ]; then
    send_slack_message "❌ *Database migration failed!*"
    exit 1
fi

sudo /bin/systemctl restart flashcardsapi
send_slack_message "🎉 *Deployment complete!* Backend and frontend successfully updated."
