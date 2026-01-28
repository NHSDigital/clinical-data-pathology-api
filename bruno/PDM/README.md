# PDM Collection Setup

## Authentication Setup

Follow the instructions on this [confluence page](https://nhsd-confluence.digital.nhs.uk/x/ixnIT) to setup Bruno with the PDM INT Environment. Authentication can then be completed via the `Get Auth Token` call within the `APIM` collection.

## Getting Auth Token

Once the `Get Auth Token` request is complete it should copy the returned token into the `auth_token` global environment variable. The collection has been setup to automatically use this variable to authenticate requests
