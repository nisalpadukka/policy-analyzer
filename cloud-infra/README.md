# Cloud Infrastructure

This directory contains cloud infrastructure configuration and deployment scripts for the Privacy Policy Analyzer application.

## Overview

Infrastructure as Code (IaC) configurations for deploying the Privacy Policy Analyzer backend to AWS. The infrastructure consists of an AWS Lambda function for processing privacy policy analysis and an API Gateway HTTP API for exposing the endpoint.

## Architecture

The infrastructure includes:

- **AWS Lambda Function**: Serverless compute for privacy policy analysis
- **API Gateway HTTP API**: RESTful endpoint with CORS support
- **IAM Roles**: Least-privilege access policies
- **Environment Variables**: Secure configuration management

## Structure

```
terraform/
├── main.tf           # Terraform provider and backend configuration
├── lambda.tf         # Lambda function and IAM role definitions
├── api-gateway.tf    # API Gateway HTTP API setup
├── variables.tf      # Input variable definitions
├── outputs.tf        # Output values (API endpoint URL)
├── build-lambda.sh   # Script to package Lambda function
└── deploy.sh         # Deployment automation script
```

## Implementation Details

### Lambda Function (`lambda.tf`)

- **Runtime**: Python 3.9+ (configurable via variable)
- **Timeout**: 60 seconds
- **Handler**: `lambda_function.lambda_handler`
- **IAM Role**: Basic execution role with CloudWatch logging
- **Environment Variables**: 
  - `OPENAI_API_KEY`: OpenAI API key for LLM access
  - `PROJECT_NAME`: Project identifier

### API Gateway (`api-gateway.tf`)

- **Protocol**: HTTP API (v2)
- **CORS Configuration**: 
  - Allow origins: `*` (configurable)
  - Allow methods: `POST`, `OPTIONS`
  - Allow headers: `content-type`, `x-amz-date`, `authorization`, `x-api-key`
  - Max age: 300 seconds
- **Integration**: AWS_PROXY integration with Lambda
- **Route**: `POST /analyze`
- **Stage**: `$default` with auto-deploy enabled

### IAM Configuration

The Lambda function uses a minimal IAM role with:
- Basic execution permissions (CloudWatch logging)
- No access to other AWS services (stateless design)

## Setup

### Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.0
- Python 3.9+ (for Lambda packaging)
- S3 bucket for Terraform state backend (optional but recommended)

### Configuration

1. **Set Terraform Variables**:

Create `terraform.tfvars` (not committed to git):

```hcl
project_name = "privacy-policy-analyzer"
aws_region = "us-east-1"
lambda_runtime = "python3.9"
openai_api_key = "your-openai-api-key"
aws_access_key = "your-aws-access-key"
aws_secret_key = "your-aws-secret-key"
```

2. **Configure Terraform Backend** (optional):

Update `main.tf` backend configuration with your S3 bucket details.

## Deployment

### Automated Deployment

Use the provided deployment script:

```bash
cd terraform
./deploy.sh
```

This script:
1. Packages the Lambda function
2. Initializes Terraform
3. Plans infrastructure changes
4. Applies changes (with confirmation)

### Manual Deployment

1. **Package Lambda Function**:

```bash
cd terraform
./build-lambda.sh
```

This creates `lambda_function.zip` with the Lambda code and dependencies.

2. **Initialize Terraform**:

```bash
terraform init
```

3. **Review Changes**:

```bash
terraform plan
```

4. **Deploy Infrastructure**:

```bash
terraform apply
```

5. **Get API Endpoint**:

```bash
terraform output api_endpoint_url
```

Copy this URL and update `background.js` in the browser extension.

## Configuration Files

### `variables.tf`

Defines input variables:
- `project_name`: Project identifier
- `aws_region`: AWS region for deployment
- `lambda_runtime`: Python runtime version
- `openai_api_key`: OpenAI API key (sensitive)
- `aws_access_key`: AWS access key
- `aws_secret_key`: AWS secret key

### `outputs.tf`

Exports:
- `api_endpoint_url`: API Gateway endpoint URL for browser extension

### `build-lambda.sh`

Packages the Lambda function:
- Copies `lambda_function.py` from `../../api/`
- Installs dependencies from `requirements.txt`
- Creates ZIP archive with all files
- Outputs to `lambda_function.zip`

## Security Considerations

- **API Keys**: Stored as Terraform variables (use `terraform.tfvars` with `.gitignore`)
- **IAM Roles**: Minimal permissions following least-privilege principle
- **CORS**: Configurable origins (currently `*` for development)
- **HTTPS**: API Gateway enforces HTTPS-only connections
- **Environment Variables**: Sensitive data stored securely in Lambda environment

## Cost Estimation

- **Lambda**: Pay per request (first 1M requests free tier)
- **API Gateway**: Pay per API call (first 1M requests free tier)
- **CloudWatch**: Logging costs (first 5GB free tier)

Estimated cost for moderate usage: < $10/month

## Troubleshooting

### Lambda Function Errors

- Check CloudWatch Logs for detailed error messages
- Verify `OPENAI_API_KEY` environment variable is set
- Ensure Lambda package includes all dependencies

### API Gateway Issues

- Verify CORS configuration matches browser extension origin
- Check Lambda permissions for API Gateway invocation
- Review API Gateway logs in CloudWatch

### Deployment Failures

- Ensure AWS credentials are configured correctly
- Verify Terraform state backend (if using S3) is accessible
- Check IAM permissions for Terraform execution

## Cleanup

To remove all infrastructure:

```bash
terraform destroy
```
