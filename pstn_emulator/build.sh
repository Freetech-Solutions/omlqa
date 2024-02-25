#!/bin/bash

set -e

IMAGE_VERSION=$(cat version.txt)
IMAGE_REPO=$(cat repo.txt)
docker build --tag=$IMAGE_REPO:$IMAGE_VERSION .
docker push $IMAGE_REPO:$IMAGE_VERSION