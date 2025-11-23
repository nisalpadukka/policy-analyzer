# IAM role for Lambda execution
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for Lambda basic execution
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda function
# Note: Run ./build-lambda.sh before terraform plan/apply to create the package
resource "aws_lambda_function" "policy_analyzer" {
  filename         = "${path.module}/lambda_function.zip"
  function_name    = "${var.project_name}-lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/lambda_function.zip")
  runtime          = var.lambda_runtime
  timeout          = 60  # 1 minute

  environment {
    variables = {
      PROJECT_NAME = var.project_name
      OPENAI_API_KEY = var.openai_api_key
    }
  }
}

