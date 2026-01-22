from logging.config import dictConfig

import requests
from flask import Flask, request

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

app = Flask(__name__)


@app.route("/<path:path_params>", methods=["POST"])
def forward_request(path_params):
    app.logger.info("received request with data: %s", request.get_data(as_text=True))

    response = requests.post(
        "http://pathology-api:8080/2015-03-31/functions/function/invocations/",
        json={
            "body": request.get_data(as_text=True).replace("\n", "").replace(" ", ""),
            "requestContent": {
                "http:": {
                    "path": f"/{path_params}",
                    "method": "POST",
                }
            },
            "httpMethod": "POST",
            "path": f"/{path_params}",
        },
        headers={"Content-Type": "application/json"},
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
