#!/bin/bash
# Quick credential test for Datafordeler API

# Load .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ .env file not found!"
    exit 1
fi

echo "========================================"
echo "Datafordeler API Credential Test"
echo "========================================"
echo
echo "Username: $DATAFORDELER_USERNAME"
echo "Password: ${DATAFORDELER_PASSWORD:0:10}..."
echo
echo "Testing connection to BBR API..."
echo

# Test with curl
URL="https://services.datafordeler.dk/BBR/BBRPublic/1/rest/bygning?username=${DATAFORDELER_USERNAME}&password=${DATAFORDELER_PASSWORD}&format=json&page=1"

echo "Making request..."
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$URL")

http_status=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_STATUS/d')

echo
echo "HTTP Status: $http_status"
echo

if [ "$http_status" = "200" ]; then
    echo "✅ SUCCESS! Credentials are correct!"
    echo
    echo "Response preview:"
    echo "$body" | head -c 500
    echo
elif [ "$http_status" = "500" ]; then
    echo "❌ FAILED: 500 Internal Server Error"
    echo
    echo "This means credentials are WRONG or API is down"
    echo
    echo "Action required:"
    echo "1. Check your GitHub Secrets at:"
    echo "   https://github.com/svanecode/Shelter-updater/settings/secrets/actions"
    echo "2. Update your .env file with the correct credentials"
    echo
elif [ "$http_status" = "403" ]; then
    echo "❌ FAILED: 403 Unauthorized"
    echo
    echo "Credentials are recognized but rejected"
    echo "They might be expired or incorrect"
    echo
else
    echo "❌ FAILED: Unexpected status $http_status"
    echo
    echo "Response:"
    echo "$body"
    echo
fi

echo "========================================"
