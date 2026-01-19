import json
import logging
from typing import Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: dict[str, Any], context):
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
