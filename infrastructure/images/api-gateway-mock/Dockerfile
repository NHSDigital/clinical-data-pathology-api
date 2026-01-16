# Retrieve the python version from build arguments, deliberately set to "invalid" by default to highlight when no version is provided when building the container.
ARG PYTHON_VERSION=invalid
# Use the specified python version to retrieve the required base lambda image.
ARG url=python:${PYTHON_VERSION}-alpine3.23
FROM $url

COPY resources/ /resources
WORKDIR /resources

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["flask", "--app", "server", "run", "--host=0.0.0.0"]
# ENTRYPOINT ["sleep", "infinity"]
