"""
Simple lambda handler function for an debugging environment.
This is used to verify that the environment is working and to inspect incoming requests.
"""

import json
import logging
from typing import Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: dict[str, Any], context: Any):
    """Handler for the preview environment. This simply returns a 200 response with
        the request headers, which can be used to verify and debug how the environment
        is working and to inspect the incoming request.

    Args:
        event (dict[str, Any]): Dictionary containing request data from API Gateway.
        context (Any): AWS lambda context object (what the lambda is running in)

    Returns:
        dict: Diagnostic 200 response with request headers.
    """
    logger.info("Lambda context: %s", context)
    headers = event.get("headers", {}) or {}

    # Log headers to CloudWatch
    logger.info("Incoming request headers:")
    for k, v in headers.items():
        logger.info("%s: %s", k, v)

    response_body = {
        "message": "ok",
        "headers": headers,
        "requestContext": event.get("requestContext", {}),
    }

    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(response_body, indent=2),
        "isBase64Encoded": False,
    }
