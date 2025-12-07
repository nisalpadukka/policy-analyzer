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
        top_p=1,
        seed=42,
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

    Your analysis MUST follow NIST Privacy Framework (v1.0) ideas of privacy risk,
    but use the following **conservative** rules so that not every policy is rated High:

    DATA COLLECTION SEVERITY (what data is collected):
    - High: The policy clearly collects multiple highly sensitive elements
      (e.g., health + biometrics + precise location + detailed behavioral tracking across
      sites/apps, or sells/uses them for profiling), OR explicitly combines many data
      sources for extensive profiling.
    - Medium: The policy collects some sensitive data (e.g., financial, basic health,
      or precise location) OR a broad mix of contact, usage, and tracking data typical
      for large online services or banks.
    - Low: Only minimal, non-sensitive data (e.g., email, basic account info) and
      no strong tracking, profiling, biometrics, or health data.

    DATA SHARING SEVERITY (who receives data):
    - High: The policy clearly says data may be sold, rented, or shared broadly for
      advertising/behavioral profiling, OR shared with many unrelated third parties
      beyond what is reasonably necessary (e.g., vague sharing with "partners" for
      marketing, data brokers, etc.).
    - Medium: Data is shared with service providers, affiliates, regulators, payment
      networks, or other entities necessary to provide the service, prevent fraud, or
      comply with law, but no explicit "selling" or broad advertising sale of personal data.
    - Low: No external sharing is mentioned, or sharing is strictly internal to the same
      organization.

    DATA RETENTION SEVERITY (how long it is kept):
    - High: The policy clearly suggests indefinite retention (e.g., "as long as we choose"
      or no meaningful limits) for most data categories.
    - Medium: Retention is described in general or vague terms (e.g., "as long as needed
      to provide services or meet legal obligations") without clear numeric limits.
    - Low: Clear numeric retention limits are given (e.g., "kept for 2 years then deleted/
      anonymized") for most data categories.

    OVERALL PRIVACY RISK (user-facing risk score):
    - High: At least TWO of the three categories (data_collecting, data_sharing,
      data_retention) are rated High.
    - Medium: Any other combination that includes at least one Medium, and no more than
      one High.
    - Low: All three categories are Low.

    If you are unsure between Medium and High, choose MEDIUM.
    If you are unsure between Medium and Low, choose MEDIUM.

    Your output MUST be a single valid JSON object with this structure:

    {{
        "data_collecting": {{
            "details": "Very short summary (max 100 words) of the types of data explicitly collected. If none stated, write 'Not specified'.",
            "severity": "Low" or "Medium" or "High"
        }},
        "data_sharing": {{
            "details": "Very short summary (max 100 words) of who the data is shared with, based ONLY on what is explicitly written. If not stated, write 'Not specified'.",
            "severity": "Low" or "Medium" or "High"
        }},
        "data_retention": {{
            "details": "State ONLY the retention period explicitly written in the text. If vague, write 'varies'. If no numeric duration is provided, write 'Not specified'. Max 100 words.",
            "severity": "Low" or "Medium" or "High"
        }},
        "overall_privacy_risk": "Low" or "Medium" or "High"
    }}

    STRICT RULES:
    - Each 'details' field MUST NOT exceed 100 words.
    - Do NOT add explanations outside the JSON.
    - Apply the conservative rules above; default to MEDIUM when in doubt.
    """

    user_message = f"{delimiter}{policy_text}{delimiter}"

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]



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

    # Handle CORS preflight OPTIONS request
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Amz-Date, X-Api-Key",
                "Access-Control-Max-Age": "300"
            },
            "body": ""
        }

    # Common CORS headers
    cors_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Amz-Date, X-Api-Key"
    }

    try:
        # Parse request body
        body = parse_request_body(event)
        policy_text = (body.get("policy_text") or "").strip()

        if not policy_text:
            logger.warning("No policy text provided in request")
            return {
                "statusCode": 400,
                "headers": cors_headers,
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
            "headers": cors_headers,
            "body": json.dumps(response_body)
        }

        logger.info("Response prepared successfully")

    except Exception as e:
        # Handle errors gracefully
        logger.error(f"Error occurred: {str(e)}", exc_info=True)

        response = {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({
                "message": "Error analyzing privacy policy",
                "error": str(e),
                "status": "error"
            })
        }

    logger.info(f"Returning response with status code: {response['statusCode']}")
    return response
