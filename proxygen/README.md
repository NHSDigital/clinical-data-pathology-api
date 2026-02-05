# Proxygen

Proxygen is the tool created by the API Platform team to support the deployment of NHS APIs.

We use this tool in the pipelines (and manually) to create, destroy and interact more generally with the proxy instances.

For more information on Proxygen, [read the docs](https://nhsd-confluence.digital.nhs.uk/spaces/APM/pages/375329782/Proxygen).

Proxygen needs:

* a settings file stating which API we are attempting to update;
* a credentials file to authenticate us as the owner/maintainer of the API;
* a specification file that outlines the behaviour of the proxy.

## Settings File

A template is stored at `proxygen/settings.template.yaml` where the `<proxygen_api_name>` needs to be inserted. This specifies which API the Proxygen command line tool will update.

During the GitHub workflows, the API name is injected into the new copy, `settings.yaml` from repository variables.

## Credentials File

A template is stored at `proxygen/credentials.template.yaml` where several placeholders need to be replaced:

* `<proxygen_private_key_path>` - path to a file that holds the private key secret identifying us as the owner/maintainer of the API
* `<proxygen_key_id>` - the key ID associated with the private key
* `<proxygen_client_id>` - the client ID for authentication

During the GitHub workflows, the private key secret is pulled from AWS secrets manager, written to a file and the path to that file, along with the other two values, are injected into the new copy, `credentials.yaml`, using the values from repository variables.

## Specification file

Proxygen deploys an instance of a proxy using a specification file. This is of the OpenAPI format with a custom extension, `x-nhsd-apim` which provides Proxygen with information as to how the proxy should behave. This includes:

* the target endpoint, to which it will forward traffic;
* the scopes that a user needs in order to access the proxy's endpoint;
* a key that points to the mTLS certificate which the targeted backend expects to be used.

A template, `proxygen/x-nhsd-api.template.yaml`, is concatenated with the general OpenAPI specification for the API, `openapi.yaml`, and the key to the mTLS certificate to be used for that proxy is written in. All of which is then written to a file and the path to that file is passed to Proxygen to deploy the proxy in the stated environment.
