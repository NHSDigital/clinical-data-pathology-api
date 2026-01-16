import requests
from flask import Flask, request

app = Flask(__name__)


@app.route("/", methods=["POST"])
def forward_request():
    print(f"received request with data: {request.get_data(as_text=True)}")

    response = requests.post(
        "http://pathology-api:8080/2015-03-31/functions/function/invocations",
        json={
            "body": request.get_data(as_text=True).replace("\n", "").replace(" ", "")
        },
        headers={"Content-Type": "application/json"},
        timeout=120,
    )

    response_data = response.json()
    return (
        response_data["body"],
        response_data["statusCode"],
        response_data["headers"],
    )
