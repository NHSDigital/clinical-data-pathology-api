# APIM Bruno Collection

This Bruno collection provides end-to-end testing capability for the API Management (APIM) integration.

## Prerequisites

Before using this collection, ensure the following requirements are met:

### 1. Active Pull Request

Your feature branch must have an open pull request (draft or ready for review) to ensure the preview Lambda function and proxy are deployed and operational.

### 2. Bruno Environment Variables

The following environment variables will need to be configured in Bruno:

| Variable           | Description                                          | Example                       |
| ------------------ | ---------------------------------------------------- | ----------------------------- |
| `PRIVATE_KEY_PATH` | Path to your private key file on your local machine  | `/home/user/.ssh/api-key.pem` |
| `JWT_SECRET`       | Active API Key from your Developer Hub application   | `your-api-key-here`           |
| `PR_NUMBER`        | The pull request number for your preview environment | `123`                         |

### 3. Developer Hub Application Setup

Register an application on the [Internal Developer Hub](https://dos-internal.ptl.api.platform.nhs.uk/Index):

1. Generate a public/private key pair
2. Upload the public key to your application
3. Copy the **Active API Key** and set it as the `JWT_SECRET` environment variable in Bruno

### 4. Configure Proxy Endpoint

The POST request URL automatically targets your preview environment proxy using the `PR_NUMBER` environment variable, which you will need to set. The URL follows this format:

```text
https://internal-dev.api.service.nhs.uk/pathology-laboratory-reporting-pr-{{PR_NUMBER}}/FHIR/R4/Bundle
```
