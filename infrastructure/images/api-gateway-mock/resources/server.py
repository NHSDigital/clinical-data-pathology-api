import os
from logging.config import dictConfig

import requests
from flask import Flask, request
from flask_cors import CORS

# Very simple logging configuration taken from https://flask.palletsprojects.com/en/stable/logging/
dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            },
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

app = Flask(__name__)  # NOSONAR python:S4502
TARGET_CONTAINER = os.environ.get("TARGET_CONTAINER")

if TARGET_CONTAINER == "MOCKS":
    cors = CORS(app, resources={r"/*": {"origins": "http://localhost:5004"}})
else:
    cors = CORS(app, resources={r"/*": {"origins": "http://localhost:5002"}})


@app.route(  # NOSONAR python:S3752
    "/",
    methods=["POST", "GET"],
    defaults={"path_params": None},
)
@app.route("/<path:path_params>", methods=["POST", "GET"])
def forward_request(path_params):
    app.logger.info("received request with data: %s", request.get_data(as_text=True))

    if TARGET_CONTAINER == "MOCKS":
        base_url = "http://mocks:8080"  # NOSONAR python:S5332
        content_type = "application/x-www-form-urlencoded"
    else:
        base_url = "http://pathology-api:8080"  # NOSONAR python:S5332
        content_type = "application/json"

    response = requests.post(
        f"{base_url}/2015-03-31/functions/function/invocations",
        json={
            "body": request.get_data(as_text=True).replace("\n", "").replace(" ", ""),
            "requestContext": {
                "http": {
                    "path": f"/{path_params}",
                    "method": request.method,
                },
                "requestId": "request-id",
                "stage": "$default",
            },
            "httpMethod": request.method,
            "rawPath": f"/{path_params}",
            "rawQueryString": "",
            "pathParameters": {"proxy": path_params},
        },
        headers={"Content-Type": content_type},
        timeout=120,
    )

    app.logger.info(
        "response: status_code=%s, body=%s", response.status_code, response.text
    )

    app.logger.info("response: %s", response.text)
    response_data = response.json()

    output = (
        (
            response_data["body"],
            response_data["statusCode"],
            response_data["headers"],
        )
        if "body" in response_data
        else (response_data, 500, {"Content-Type": "text/plain"})
    )

    return output
