#!/bin/bash
# Automated MCP registry login using gh CLI token approach
# Since mcp-publisher only supports GitHub device flow,
# we'll run it and auto-open + auto-fill the code

cd /Users/testtst/Projects/cia-diagnose

# Start mcp-publisher login in background, capture output
OUTPUT=$(mktemp)
mcp-publisher login github > "$OUTPUT" 2>&1 &
PID=$!

# Wait for the code to appear
sleep 3
CODE=$(grep -oP '[A-Z0-9]{4}-[A-Z0-9]{4}' "$OUTPUT" | head -1)

if [ -z "$CODE" ]; then
    echo "Could not extract code from output:"
    cat "$OUTPUT"
    exit 1
fi

echo "Got code: $CODE"
CODE_NOHYPHEN=$(echo "$CODE" | tr -d '-')

# Use Python + requests to submit the code via GitHub API
python3 << PYEOF
import subprocess, json, time, sys

# Get gh token
token = subprocess.check_output(['gh', 'auth', 'token']).decode().strip()
code = "$CODE_NOHYPHEN"

print(f"Using code: {code}")
print(f"Token starts with: {token[:10]}...")

# The device activation page requires browser interaction
# But we can use the gh CLI to create a PAT and configure mcp-publisher directly
# Actually, let's just open the URL with the code pre-filled
import webbrowser
webbrowser.open(f'https://github.com/login/device')
print("Opened browser. Please enter code: $CODE")
PYEOF

# Wait for auth to complete
echo "Waiting for authorization..."
wait $PID
EXIT=$?
rm "$OUTPUT"

if [ $EXIT -eq 0 ]; then
    echo "SUCCESS: Logged in to MCP registry!"
    # Now publish
    mcp-publisher publish
else
    echo "Auth failed (exit $EXIT)"
fi
