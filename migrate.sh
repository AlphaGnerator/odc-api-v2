#!/bin/bash
# --- Safer Migration Script for odc-api (v3) ---

# Exit immediately if any command fails.
set -e

# --- Configuration ---
DB_INSTANCE_CONNECTION_NAME="project-cod-476918:asia-south1:cook-postgres"
DB_NAME="odc"
DB_USER="postgres"

# !!! IMPORTANT: REPLACE THIS PASSWORD PLACEHOLDER !!!

DB_PASSWORD="honeyP@1996"

# --- Safer Cleanup ---
PROXY_PID=""

# Define the cleanup function. It will only run if PROXY_PID is set.
cleanup() {
  echo "--- Cleaning up ---"
  if [ -n "$PROXY_PID" ]; then
    echo "Stopping Cloud SQL Proxy (PID: $PROXY_PID)..."
    # Kill only the specific proxy process
    kill "$PROXY_PID" || true
  fi
}

# Trap ensures cleanup runs on script exit (success, error, or Ctrl+C)
trap cleanup EXIT INT TERM

# --- Script Execution ---

# 1. Check for Password
if [ "$DB_PASSWORD" == "<YOUR_DATABASE_PASSWORD>" ]; then
    echo "❌ ERROR: Please edit 'migrate.sh' and set your DB_PASSWORD."
    exit 1
fi

# 2. Check for Proxy executable
if [ ! -f ./cloud-sql-proxy ]; then
    echo "❌ ERROR: 'cloud-sql-proxy' executable not found here."
    exit 1
fi

# 3. Start Proxy and capture its specific PID
echo "--- Starting Cloud SQL Proxy in the background... ---"
./cloud-sql-proxy "$DB_INSTANCE_CONNECTION_NAME" &
PROXY_PID=$!
echo "Proxy started with PID: $PROXY_PID"
sleep 5 # Give it time to connect
# Function to check if a process is running
is_process_running() {
  pid=$1
  if [ -z "$pid" ]; then
    return 1 # Not running as PID is empty
  fi
  ps -p "$pid" > /dev/null 2>&1
  return $? # 0 if running, 1 if not
}

# 4. Run Django Migrations
echo "--- Running Django migrations... ---"
(
    export DB_NAME="$DB_NAME"
    export DB_USER="$DB_USER"
    if [ -z "$DB_PASSWORD" ]; then
      echo "❌ ERROR: DB_PASSWORD is not set!" && exit 1
    fi
    export DB_PASSWORD="$DB_PASSWORD"
    export DB_HOST="127.0.0.1"
    export DB_PORT="5432"
    
    python3 manage.py migrate --noinput
)

if [ $? -ne 0 ]; then
  echo "❌ ERROR: Django migrations failed. Check output above."
  exit 1
fi
echo "--- ✅ SUCCESS: Database Migration Complete ---"

# The script will now exit, and the 'trap' will automatically call the cleanup function.
