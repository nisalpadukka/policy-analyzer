#!/bin/bash

# Deploy script for Policy Analyzer
# This script builds the Lambda package, deploys infrastructure, and tests the API

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_SCRIPT="$SCRIPT_DIR/build-lambda.sh"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Policy Analyzer Deployment Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Build Lambda package
echo -e "${YELLOW}Step 1: Building Lambda package...${NC}"
if [ -f "$BUILD_SCRIPT" ]; then
    bash "$BUILD_SCRIPT"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Lambda build failed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Lambda package built successfully${NC}"
else
    echo -e "${RED}Error: build-lambda.sh not found at $BUILD_SCRIPT${NC}"
    exit 1
fi
echo ""

# Step 2: Initialize Terraform (if needed)
echo -e "${YELLOW}Step 2: Checking Terraform initialization...${NC}"
if [ ! -d "$SCRIPT_DIR/.terraform" ]; then
    echo "Initializing Terraform..."
    terraform init
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Terraform initialization failed${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ Terraform initialized${NC}"
echo ""

# Step 3: Run Terraform plan
echo -e "${YELLOW}Step 3: Running Terraform plan...${NC}"
terraform plan
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Terraform plan failed${NC}"
    exit 1
fi
echo ""

# Step 4: Apply Terraform
echo -e "${YELLOW}Step 4: Deploying infrastructure with Terraform...${NC}"
terraform apply -auto-approve
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Terraform apply failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Infrastructure deployed successfully${NC}"
echo ""

# Step 5: Get API Gateway URL
echo -e "${YELLOW}Step 5: Getting API Gateway URL...${NC}"
API_URL=$(terraform output -raw api_gateway_url 2>/dev/null)

if [ -z "$API_URL" ]; then
    echo -e "${RED}Error: Could not retrieve API Gateway URL${NC}"
    exit 1
fi

echo -e "${GREEN}✓ API Gateway URL: $API_URL${NC}"
echo ""

# Step 6: Test the API endpoint
echo -e "${YELLOW}Step 6: Testing API endpoint /analyze...${NC}"
ENDPOINT_URL="${API_URL}/analyze"
echo "Calling: $ENDPOINT_URL"
echo ""

# Wait a few seconds for Lambda to be ready
sleep 3

# Create dummy policy text for testing
DUMMY_POLICY='{
  "policy_text": "We collect personal information including your name, email address, payment information, and browsing history when you use our services. This data is shared with third-party service providers and advertising partners to improve our services and deliver targeted advertisements. We retain your personal information while your account is active and for a period of 30 days after account closure. We may also share your information with law enforcement when required by law."
}'

# Make the API call with POST request and JSON body
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d "$DUMMY_POLICY" \
  "$ENDPOINT_URL" || echo -e "\n000")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo -e "${BLUE}Response Status: $HTTP_CODE${NC}"
echo -e "${BLUE}Response Body:${NC}"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ API test successful!${NC}"
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "API Endpoint: ${BLUE}$ENDPOINT_URL${NC}"
    echo ""
    echo "You can test it with:"
    echo -e "  ${YELLOW}curl -X POST -H \"Content-Type: application/json\" -d '{\"policy_text\": \"Your policy text here...\"}' $ENDPOINT_URL${NC}"
else
    echo -e "${YELLOW}⚠ API test returned status code: $HTTP_CODE${NC}"
    echo -e "${YELLOW}The deployment completed, but the API test failed.${NC}"
    echo -e "${YELLOW}This might be normal if the Lambda is still warming up.${NC}"
    echo ""
    echo "You can test it manually with:"
    echo -e "  ${YELLOW}curl -X POST -H \"Content-Type: application/json\" -d '{\"policy_text\": \"Your policy text here...\"}' $ENDPOINT_URL${NC}"
fi

