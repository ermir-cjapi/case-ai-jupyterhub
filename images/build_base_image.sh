#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

REGISTRY="${REGISTRY:-registry.example.com}"
IMAGE_NAME="${IMAGE_NAME:-gpu-notebook}"
IMAGE_TAG="${IMAGE_TAG:-v1}"

FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "Building image ${FULL_IMAGE} ..."

cd "${ROOT_DIR}/images"
DOCKER_BUILDKIT=0 docker build -t "${FULL_IMAGE}" .

echo "Pushing image ${FULL_IMAGE} ..."
docker push "${FULL_IMAGE}"

echo "Done."


