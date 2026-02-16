# pathology API

## Testing

The pathology API has four types of tests, each serving a different purpose:

- **[Unit, Contract, & Schema Tests](tests/README.md)** - Developer-focused technical tests using pytest
- **[BDD Acceptance Tests](tests/README.md)** - Business-focused assurance tests using behave

### Continuous Integration

All four test types (unit, contract, schema, and integration) run automatically in the CI/CD pipeline on every push and pull request. **Any test failure at any level will cause the pipeline to fail and prevent the PR from being merged.**

Additionally, code coverage is collected from all test types, merged, and analyzed by SonarCloud. PRs must meet minimum coverage thresholds to pass quality gates.

### Quick Test Commands

```bash
# After running
make deploy

# Run all tests against local Lambda + api-gateway-mock
make test-local

# Run all tests against remote APIM proxy (generates APIGEE token automatically)
make test-remote

# Run a single test type (ensure your .env file is set correctly and sourced)
make test-unit          # local-only
make test-integration
make test-contract
make test-schema
make test-acceptance    # remote-only
```

For detailed testing documentation, see the [testing README](tests/README.md).

## Project Structure

```text
pathology-api/
├── src/
│   └── pathology_api/
│       └── main.py                         # Flask application
│       └── test_**.py                      # Unit tests (pytest)
├── tests/                                  # Acceptance, contract & schema tests pytest
│   ├── conftest.py                         # Shared pytest fixtures
|   ├── acceptance/                         # BDD acceptance/assurance tests (behave)
│   │   ├── features/
│   │   │   └── bundle_endpoint.feature     # Gherkin feature files
│   │   ├── scenarios/
│   │   │   └── test_bundle_endpoint.py     # Behave setup
│   │   └── steps/
│   │       └── bundle_endpoint_steps.py    # Step definitions
│   │
│   ├── contract/                           # Contract tests (Pact)
│   │   ├── test_consumer_contract.py       # Consumer contract definitions
│   │   ├── test_provider_contract.py       # Provider contract verification
│   │   └── pacts/                          # Generated pact files
│   │       └── PathologyAPIConsumer-PathologyAPIProvider.json
│   │
│   ├── integration/
│   │   └── test_endpoints.py               # Integration tests
│   │
│   └── schema/                             # Schema validation tests
│       └── test_openapi_schema.py          # Schemathesis property-based tests
├── features/
│   ├── environment.py
│   ├── steps/
│   └── *.feature
├── openapi.yaml                            # OpenAPI 3.0 specification
├── pyproject.toml                          # Dependencies and config
└── README.md
```
