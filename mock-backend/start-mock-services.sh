#!/bin/bash

echo "Starting Mock Backend Services..."
echo "================================"

# Kill any existing mockoon processes
pkill -f mockoon-cli

# Start main API service
echo "Starting Main API Service on port 3001..."
mockoon-cli start --data ./mockoon-config.json &
MAIN_PID=$!

# Wait a bit for first service to start
sleep 2

# Start analytics service
echo "Starting Analytics Service on port 3002..."
mockoon-cli start --data ./mockoon-analytics-service.json &
ANALYTICS_PID=$!

# Start notification service
echo "Starting Notification Service on port 3003..."
mockoon-cli start --data ./mockoon-notification-service.json &
NOTIF_PID=$!

echo ""
echo "All services started!"
echo "===================="
echo "Main API:          http://localhost:3001"
echo "Analytics Service: http://localhost:3002"
echo "Notification:      http://localhost:3003"
echo ""
echo "Process IDs:"
echo "Main API: $MAIN_PID"
echo "Analytics: $ANALYTICS_PID"
echo "Notification: $NOTIF_PID"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping all services..."
    kill $MAIN_PID $ANALYTICS_PID $NOTIF_PID 2>/dev/null
    pkill -f mockoon-cli
    echo "Services stopped."
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup INT TERM

# Wait for all background processes
wait