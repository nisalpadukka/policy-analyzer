import json
import os
import logging
import re
from openai import OpenAI

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configure OpenAI client with API key from environment variable
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])


def parse_request_body(event):
    """Parse the request body from API Gateway event."""
    try:
        body = event.get('body')
        if isinstance(body, str):
            body = json.loads(body)
        elif body is None:
            body = {}
        return body
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse request body: {str(e)}")
        return {}


def get_completion_from_messages(messages, model="gpt-5.1"):
    """Get completion from OpenAI with deterministic settings."""
    logger.info("Messages sent to OpenAI:")
    try:
        logger.info(json.dumps(messages, indent=2))
    except Exception:
        # In case of non-serializable content
        logger.info(str(messages))

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,   # deterministic / less “creative”
        top_p=0.1
    )
    logger.info(f"OpenAI raw response: {response.model_dump_json(indent=2)}")
    return response.choices[0].message.content


def create_analysis_prompt(policy_text: str):
    """Create system message and user message for privacy policy analysis."""
    delimiter = "####"

    system_message = f"""
    You will be given privacy policy text inside {delimiter} characters.

    Analyze ONLY the text inside the delimiters.   
    If something is not directly stated, output: "Not specified".

    Your output MUST be a single valid JSON object with this exact structure:

    {{
        "data_collecting": {{
            "details": "Summary of data types explicitly stated in the policy comma separated list. If none are stated, write 'Not specified'.",
            "severity": "Low" or "Medium" or "High"
        }},
        "data_sharing": {{
            "details": "Summary of who data is shared with, based ONLY on what is explicitly written in a once sentence. If not stated, write 'Not specified'.",
            "severity": "Low" or "Medium" or "High"
        }},
        "data_retention": {{
            "details": "State ONLY the retention period explicitly written in the text. If it's vague mention vary. If the policy does NOT contain a numeric time period (e.g., a number AND a time unit), write 'Not specified'. Never guess or invent time periods.",
            "severity": "Low" or "Medium" or "High"
        }},
        "overall_privacy_risk": "Low" or "Medium" or "High"
    }}

    STRICT RULES:
    - Do NOT add any explanation outside the JSON.
    """

    user_message = f"{delimiter}{policy_text}{delimiter}"

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]

    return messages


def lambda_handler(event, context):
    """
    Lambda handler function that analyzes privacy policies using OpenAI.

    Args:
        event: API Gateway event containing policy text in body
        context: Lambda context

    Returns:
        dict: API Gateway response with privacy policy analysis
    """
    logger.info("Lambda function invoked")
    # context might be None in local tests; guard access
    request_id = getattr(context, "aws_request_id", "local-test")
    logger.info(f"Request ID: {request_id}")

    try:
        # Parse request body
        body = parse_request_body(event)
        policy_text = (body.get("policy_text") or "").strip()

        if not policy_text:
            logger.warning("No policy text provided in request")
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "message": "Missing required field: policy_text",
                    "status": "error"
                })
            }

        logger.info(f"Analyzing policy text (length: {len(policy_text)} characters)")

        # Create messages using the new prompt
        messages = create_analysis_prompt(policy_text)

        # Call OpenAI API
        logger.info("Starting OpenAI API call")
        openai_response = get_completion_from_messages(
            messages=messages,
            model="gpt-5.1"
        )

        logger.info("OpenAI API call successful")
        logger.info(f"OpenAI raw response content: {openai_response}")

        # Parse the JSON response
        try:
            analysis_result = json.loads(openai_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {str(e)}")
            # Try to extract JSON from response if it's wrapped in text
            json_match = re.search(r'\{.*\}', openai_response, re.DOTALL)
            if json_match:
                analysis_result = json.loads(json_match.group())
            else:
                raise ValueError("OpenAI response is not valid JSON")

        # Structure the response
        response_body = {
            "status": "success",
            "summary": {
                "data_collecting": {
                    "details": analysis_result.get("data_collecting", {}).get("details", "Not specified"),
                    "severity": analysis_result.get("data_collecting", {}).get("severity", "Unknown")
                },
                "data_sharing": {
                    "details": analysis_result.get("data_sharing", {}).get("details", "Not specified"),
                    "severity": analysis_result.get("data_sharing", {}).get("severity", "Unknown")
                },
                "data_retention": {
                    "details": analysis_result.get("data_retention", {}).get("details", "Not specified"),
                    "severity": analysis_result.get("data_retention", {}).get("severity", "Unknown")
                },
                "overall_privacy_risk": analysis_result.get("overall_privacy_risk", "Unknown")
            }
        }

        response = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(response_body)
        }

        logger.info("Response prepared successfully")

    except Exception as e:
        # Handle errors gracefully
        logger.error(f"Error occurred: {str(e)}", exc_info=True)

        response = {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "message": "Error analyzing privacy policy",
                "error": str(e),
                "status": "error"
            })
        }

    logger.info(f"Returning response with status code: {response['statusCode']}")
    return response
