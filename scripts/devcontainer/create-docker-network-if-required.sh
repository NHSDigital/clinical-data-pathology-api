#!/bin/bash

set -e

docker network create pathology-local || echo "Local network already exists"
