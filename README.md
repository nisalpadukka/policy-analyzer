# Privacy Policy Analyzer

A browser extension that uses AI-assisted summarization to help users understand privacy policies by extracting and presenting key information about data collection, data sharing, data retention, and overall privacy risk in plain language.

[![Chrome Web Store](https://img.shields.io/badge/Chrome%20Web%20Store-Available-brightgreen)](https://chromewebstore.google.com/detail/mlmdjpffmmojkiidoleibkpjnaabpndd)

## Overview

The Privacy Policy Analyzer addresses the gap between what privacy policies are intended to provide (transparent notice and meaningful consent) and what users can realistically read, understand, and act on in practice. Privacy policies are typically long, legally dense documents that most people do not read, which means individuals often accept data practices they do not fully grasp.

This project implements a browser extension that uses a large language model (LLM) backend to convert user-selected sections of privacy policies into structured summaries with severity ratings (Low, Medium, High) across four dimensions:

- **Data Collection**: What types of data are collected
- **Data Sharing**: Who the data is shared with
- **Data Retention**: How long data is kept
- **Overall Privacy Risk**: Aggregate risk assessment

## Architecture

The system follows a modular architecture with three main components:

1. **Browser Extension Frontend** (`browser-plugin/`): User interface and client-side logic
2. **Backend API** (`api/`): AWS Lambda function with OpenAI integration
3. **Infrastructure** (`cloud-infra/`): Terraform configuration for AWS deployment

### System Flow

1. User opens the browser extension popup and pastes privacy policy text
2. Extension sends text to background service worker
3. Background worker makes HTTP POST request to API Gateway endpoint
4. Lambda function processes the request, constructs analysis prompt, and calls OpenAI API
5. LLM response is parsed and returned to the extension
6. Popup displays structured summary with color-coded severity badges

## Implementation Details

### Browser Extension

The extension is built using Manifest V3 and consists of:

- **popup.html/js/css**: User interface with textarea input and four summary sections
- **background.js**: Service worker that handles API communication
- **manifest.json**: Extension configuration and permissions

**Key Features:**
- Minimal permissions (only activates when user opens popup)
- Manual text input (no automatic content extraction)
- Visual severity indicators (green/yellow/red badges)
- Error handling with fallback mock summaries

### Backend API

The Lambda function (`api/lambda_function.py`) implements:

- **Request Validation**: Checks for required `policy_text` field
- **CORS Support**: Handles cross-origin requests from browser extensions
- **OpenAI Integration**: Uses GPT model with deterministic settings (temperature=0, seed=42)
- **Prompt Engineering**: Structured system message with conservative severity classification rules
- **Response Parsing**: Robust JSON extraction with fallback regex matching
- **Error Handling**: Comprehensive error logging and user-friendly error messages

**API Endpoint:**
- **Method**: POST
- **Path**: `/analyze`
- **Request Body**: `{ "policy_text": "..." }`
- **Response**: Structured JSON with four analysis dimensions

### Prompt Engineering

The analysis prompt implements conservative severity classification based on NIST Privacy Framework concepts:

- **Data Collection**: Evaluates sensitivity and scope of collected data
- **Data Sharing**: Assesses breadth of third-party sharing and selling practices
- **Data Retention**: Examines clarity and duration of retention policies
- **Overall Risk**: Aggregates individual dimension scores

The prompt includes explicit instructions to default to "Medium" when uncertain, preventing over-classification of policies as high risk.

### Infrastructure

Infrastructure is provisioned using Terraform:

- **AWS Lambda**: Serverless function execution
- **API Gateway**: HTTP API with CORS configuration
- **IAM Roles**: Least-privilege access policies
- **Environment Variables**: Secure API key management

## Project Structure

```
policy-analyzer/
├── api/                    # Lambda function and dependencies
│   ├── lambda_function.py  # Main Lambda handler
│   └── requirements.txt    # Python dependencies
├── browser-plugin/         # Browser extension
│   └── privacy-policy-analyzer-extension/
│       ├── popup.html      # Extension UI
│       ├── popup.js        # UI logic
│       ├── popup.css       # Styling
│       ├── background.js   # Service worker
│       └── manifest.json   # Extension config
└── cloud-infra/            # Infrastructure as Code
    └── terraform/          # Terraform configurations
        ├── lambda.tf       # Lambda resources
        ├── api-gateway.tf  # API Gateway setup
        └── main.tf         # Provider configuration
```

## Setup and Installation

### Prerequisites

- Python 3.9+ (for Lambda function)
- Node.js/npm (for development)
- AWS CLI configured with appropriate credentials
- Terraform >= 1.0
- OpenAI API key

### Browser Extension Installation

**Option 1: Install from Chrome Web Store (Recommended)**

The extension is available on the Chrome Web Store:

🔗 **[Install Privacy Policy Analyzer from Chrome Web Store](https://chromewebstore.google.com/detail/mlmdjpffmmojkiidoleibkpjnaabpndd)**

Simply click "Add to Chrome" to install the extension. No additional configuration needed.

**Option 2: Manual Installation (For Development)**

1. Navigate to `browser-plugin/privacy-policy-analyzer-extension/`
2. Open Chrome/Edge and go to `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked" and select the extension directory
5. Update `background.js` with your API Gateway URL

### Backend Deployment

1. Set up AWS credentials and configure Terraform backend
2. Navigate to `cloud-infra/terraform/`
3. Set Terraform variables (including `openai_api_key`)
4. Run `./build-lambda.sh` to package the Lambda function
5. Run `terraform init` and `terraform apply`

### API Configuration

Update the `ANALYSIS_API_URL` in `browser-plugin/privacy-policy-analyzer-extension/background.js` with your deployed API Gateway endpoint URL.

## Usage

1. Open the browser extension popup
2. Copy and paste a section of a privacy policy into the textarea
3. Click "Summarize"
4. Review the four-dimensional analysis with severity ratings
5. Use the color-coded badges to quickly assess privacy risk

## Privacy and Security

The extension implements privacy-by-design principles:

- **Data Minimization**: Only processes explicitly pasted text
- **No Persistent Storage**: Summaries generated in real-time, not stored
- **User Control**: All actions require explicit user initiation
- **No Tracking**: No analytics or logging of user behavior
- **Secure API Communication**: HTTPS-only API requests

## Development

### Local Testing

The Lambda function can be tested locally using AWS SAM or by simulating the API Gateway event structure. The extension includes a mock summarizer fallback for offline development.

### Adding Features

- **Content Script**: To enable automatic text extraction from web pages
- **Storage**: To save analysis history (requires privacy considerations)
- **Export**: To download summaries as PDF or text files
- **Comparison**: To compare multiple policies side-by-side

## References

This project builds upon research in usable privacy and automated policy analysis. The severity classification system is informed by the NIST Privacy Framework (v1.0) and conservative risk assessment principles.


## Authors

Nisal Padukka, Patrick Abu  
MCTI, University of Guelph