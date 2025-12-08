# API

This directory contains the backend API for the Privacy Policy Analyzer application.

## Overview

The API is implemented as an AWS Lambda function that processes privacy policy text using OpenAI's GPT model. It provides a RESTful endpoint that accepts privacy policy text and returns a structured analysis with severity ratings across four dimensions: data collection, data sharing, data retention, and overall privacy risk.

## Architecture

The Lambda function (`lambda_function.py`) implements:

- **Request Handling**: Parses API Gateway events and validates input
- **CORS Support**: Handles preflight OPTIONS requests and sets appropriate headers
- **OpenAI Integration**: Constructs prompts and calls GPT model with deterministic settings
- **Response Processing**: Parses and validates LLM JSON output
- **Error Handling**: Comprehensive logging and graceful error responses

## Implementation Details

### Lambda Handler

The `lambda_handler` function processes API Gateway events:

1. Validates request body contains `policy_text` field
2. Constructs analysis prompt using `create_analysis_prompt()`
3. Calls OpenAI API via `get_completion_from_messages()`
4. Parses JSON response with fallback regex extraction
5. Structures response with four analysis dimensions
6. Returns API Gateway-compatible response with CORS headers

### Prompt Engineering

The `create_analysis_prompt()` function generates a structured prompt with:

- **System Message**: Defines analysis framework and severity classification rules
- **User Message**: Contains delimited policy text for analysis
- **Conservative Rules**: Prevents over-classification by defaulting to Medium when uncertain
- **JSON Output Format**: Strict structure with details and severity for each dimension

### Severity Classification

The prompt implements three-level severity ratings (Low, Medium, High) based on:

- **Data Collection**: Sensitivity and scope of collected data
- **Data Sharing**: Breadth of third-party sharing and selling practices  
- **Data Retention**: Clarity and duration of retention policies
- **Overall Risk**: Aggregated score from individual dimensions

### OpenAI Configuration

- **Model**: GPT-4 (configurable via model parameter)
- **Temperature**: 0 (deterministic outputs)
- **Seed**: 42 (reproducibility)
- **Top-p**: 1

## API Endpoint

### POST /analyze

Analyzes privacy policy text and returns structured summary.

**Request:**
```json
{
  "policy_text": "Privacy policy text here..."
}
```

**Response:**
```json
{
  "status": "success",
  "summary": {
    "data_collecting": {
      "details": "Summary of data collection practices...",
      "severity": "Medium"
    },
    "data_sharing": {
      "details": "Summary of data sharing practices...",
      "severity": "High"
    },
    "data_retention": {
      "details": "Retention period information...",
      "severity": "Low"
    },
    "overall_privacy_risk": "Medium"
  }
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Error description",
  "error": "Detailed error information"
}
```

## Setup

### Prerequisites

- Python 3.9+
- OpenAI API key
- AWS credentials (for deployment)

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

3. Test locally using AWS SAM or by simulating API Gateway events

### Deployment

The Lambda function is deployed using Terraform (see `../cloud-infra/terraform/`):

1. Package the function:
```bash
cd ../cloud-infra/terraform
./build-lambda.sh
```

2. Deploy with Terraform:
```bash
terraform init
terraform apply
```

The function requires the `OPENAI_API_KEY` environment variable to be set in Terraform.

## Dependencies

- `openai`: OpenAI Python client library for API calls
- Standard library: `json`, `os`, `logging`, `re`

## Error Handling

The function implements multiple error handling layers:

- **Request Validation**: Returns 400 for missing or invalid input
- **JSON Parsing**: Fallback regex extraction if LLM output is malformed
- **API Errors**: Returns 500 with descriptive error messages
- **Logging**: Comprehensive CloudWatch logging for debugging

## Security Considerations

- API key stored as environment variable (not in code)
- CORS configured to allow browser extension origins
- Input validation to prevent injection attacks
- No persistent storage of user data
- Stateless API design

## Testing

Test the function locally by creating a test event:

```python
event = {
    "body": json.dumps({"policy_text": "Test policy text..."}),
    "requestContext": {
        "http": {"method": "POST"}
    }
}
response = lambda_handler(event, None)
```

