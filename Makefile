# This file is for you! Edit it to implement your own hooks (make targets) into
# the project as automated steps to be executed on locally and in the CD pipeline.

include scripts/init.mk

# Within the build container the `doas` command is required when running docker commands as we're running as a non-root user.
ifeq (${IN_BUILD_CONTAINER}, true)
docker := doas docker
else
docker := docker
endif

dockerNetwork := pathology-local

# ==============================================================================

# Example CI/CD targets are: dependencies, build, publish, deploy, clean, etc.

.PHONY: dependencies
dependencies: # Install dependencies needed to build and test the project @Pipeline
	cd pathology-api && poetry sync

.PHONY: build
build: clean-artifacts dependencies
	@cd pathology-api
	@echo "Running type checks..."
	@rm -rf target && rm -rf dist
	@poetry run mypy --no-namespace-packages .
	@echo "Packaging dependencies..."
	@poetry build --format=wheel
	VERSION=$$(poetry version -s)
	@pip install "dist/pathology_api-$$VERSION-py3-none-any.whl" --target "./target/pathology-api" --platform manylinux2014_x86_64 --only-binary=:all:
	# Copy lambda_handler file separately as it is not included within the package.
	@cp lambda_handler.py ./target/pathology-api/
	@cd ./target/pathology-api
	@zip -r "../artifact.zip" .

.PHONY: build-images
build-images: build # Build the project artefact @Pipeline
	@mkdir infrastructure/images/pathology-api/resources/build/
	@cp pathology-api/target/artifact.zip infrastructure/images/pathology-api/resources/build/
	@mkdir infrastructure/images/pathology-api/resources/build/pathology-api
	@unzip infrastructure/images/pathology-api/resources/build/artifact.zip -d infrastructure/images/pathology-api/resources/build/pathology-api

	@echo "Building Docker image using Docker. Utilising python version: ${PYTHON_VERSION} ..."
	@$(docker) buildx build --load --platform=linux/amd64 --provenance=false --build-arg PYTHON_VERSION=${PYTHON_VERSION} -t localhost/pathology-api-image infrastructure/images/pathology-api
	@echo "Docker image 'pathology-api-image' built successfully!"

	@echo "Building api-gateway-mock using Docker. Utilising python version: ${PYTHON_VERSION} ..."
	@$(docker) buildx build --load --build-arg PYTHON_VERSION=${PYTHON_VERSION} -t localhost/api-gateway-mock-image infrastructure/images/api-gateway-mock
	@echo "Docker image 'api-gateway-mock-image' built successfully!"

publish: # Publish the project artefact @Pipeline
	# TODO: Implement the artefact publishing step

deploy: clean-docker build-images # Deploy the project artefact to the target environment @Pipeline
	$(docker) network create $(dockerNetwork) || echo "Docker network '$(dockerNetwork)' already exists."
	$(docker) run  --platform linux/amd64 --name pathology-api -p 5001:8080 --network $(dockerNetwork) -d localhost/pathology-api-image
	$(docker) run --name api-gateway-mock -p 5002:5000 --network $(dockerNetwork) -d localhost/api-gateway-mock-image

clean-artifacts:
	@echo "Removing build artefacts..."
	@rm -rf infrastructure/images/pathology-api/resources/build/
	@rm -rf pathology-api/target && rm -rf pathology-api/dist

clean-docker: stop
	@echo "Removing pathology API container..."
	@$(docker) rm pathology-api || echo "No pathology API container currently exists."

	@echo "Removing api-gateway-mock container..."
	@$(docker) rm api-gateway-mock || echo "No api-gateway-mock container currently exists."

clean:: clean-artifacts clean-docker  # Clean-up project resources (main) @Operations

.PHONY: stop
stop:
	@echo "Stopping pathology API container..."
	@$(docker) stop pathology-api || echo "No pathology API container currently running."

	@echo "Stopping api-gateway-mock container..."
	@$(docker) stop api-gateway-mock || echo "No api-gateway-mock container currently running."

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
