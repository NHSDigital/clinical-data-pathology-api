# This file is for you! Edit it to implement your own hooks (make targets) into
# the project as automated steps to be executed on locally and in the CD pipeline.

include scripts/init.mk

# Within the build container the `doas` command is required when running docker commands as we're running as a non-root user.
ifeq (${IN_BUILD_CONTAINER}, true)
docker := doas docker
else
docker := docker
endif
# ==============================================================================

# Example CI/CD targets are: dependencies, build, publish, deploy, clean, etc.

.PHONY: dependencies
dependencies: # Install dependencies needed to build and test the project @Pipeline
	cd pathology-api && poetry sync

.PHONY: build-pathology-api
build-pathology-api: dependencies
	@cd pathology-api
	@echo "Running type checks..."
	@rm -rf target && rm -rf dist
	@poetry run mypy --no-namespace-packages .
	@echo "Packaging dependencies..."
	@poetry build --format=wheel
	@pip install "dist/pathology_api-0.1.0-py3-none-any.whl" --target "./target/pathology-api"
	# Copy main file separately as it is not included within the package.
	@cp lambda_handler.py ./target/pathology-api/
	@rm -rf ../infrastructure/images/pathology-api/resources/build/
	@mkdir ../infrastructure/images/pathology-api/resources/build/
	@cp -r ./target/pathology-api ../infrastructure/images/pathology-api/resources/build/
	# Remove temporary build artefacts once build has completed
	@rm -rf target && rm -rf dist

.PHONY: build
build: build-pathology-api # Build the project artefact @Pipeline
	@echo "Building Docker image using Docker. Utilising python version: ${PYTHON_VERSION} ..."
	@$(docker) buildx build --load --provenance=false --build-arg PYTHON_VERSION=${PYTHON_VERSION} -t localhost/pathology-api-image infrastructure/images/pathology-api
	@echo "Docker image 'pathology-api-image' built successfully!"

publish: # Publish the project artefact @Pipeline
	# TODO: Implement the artefact publishing step

deploy: clean build # Deploy the project artefact to the target environment @Pipeline
	@if [[ -n "$${IN_BUILD_CONTAINER}" ]]; then \
		echo "Starting using local docker network ..." ; \
		$(docker) run --name pathology-api -p 5001:8080 --network pathology-local -d localhost/pathology-api-image ; \
	else \
		$(docker) run --name pathology-api -p 5001:8080 -d localhost/pathology-api-image ; \
	fi

clean:: stop # Clean-up project resources (main) @Operations
	@echo "Removing pathology API container..."
	@$(docker) rm pathology-api || echo "No pathology API container currently exists."

.PHONY: stop
stop:
	@echo "Stopping pathology API container..."
	@$(docker) stop pathology-api || echo "No pathology API container currently running."

config:: # Configure development environment (main) @Configuration
	# Configure poetry to trust dev certificate if specified
	@if [[ -n "$${DEV_CERTS_INCLUDED}" ]]; then \
		echo "Configuring poetry to trust the dev certificate..."  ; \
		poetry config certificates.PyPI.cert /etc/ssl/cert.pem ; \
	fi
	make _install-dependencies

# ==============================================================================

${VERBOSE}.SILENT: \
	build \
	clean \
	config \
	dependencies \
	deploy \
