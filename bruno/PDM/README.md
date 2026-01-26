# PDM Collection Setup

## Install dependencies

While in the dev container, navigate to the PDM collection directory and run the command `npm install`

## Authentication Setup

Follow the instructions on this [confluence page](https://nhsd-confluence.digital.nhs.uk/spaces/DCA/pages/1288182155/Clinical+Data+Gateway+-+Bruno+PDM+Authentication+Setup) to setup Bruno with the PDS INT Environment

## Getting Auth Token

Once you have completed the previous instructions you should be able to run the Get Auth Token request, once the request is complete it should copy the returned token into the `auth_token` environment variable. The collection has been setup to automatically use this variable to authenticate requests
