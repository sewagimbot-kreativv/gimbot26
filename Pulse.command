#!/bin/bash
# Move to the script's directory
cd "$(dirname "$0")"

echo "=========================================================="
echo " Starting GimbotSaham Stock Intelligence Web Dashboard..."
echo "=========================================================="
echo "Server output will be shown below."
echo "Press Ctrl+C in this terminal window to stop the server."
echo "=========================================================="

# Start backend server in the background
.venv/bin/python pulse_web_server.py &
SERVER_PID=$!

# Wait for server to start
sleep 2.5

# Open default browser
open http://localhost:8080

# Keep script running and catch Ctrl+C to stop python process
trap "kill $SERVER_PID" EXIT
wait $SERVER_PID
