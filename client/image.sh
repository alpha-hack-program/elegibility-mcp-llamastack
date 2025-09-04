#!/bin/bash

set -euo pipefail

# --- Load .env (optional, for build-time defaults) ---
if [ -f .env ]; then
  source .env
fi

# --- Default values ---
COMPONENT_NAME="${COMPONENT_NAME:-$DEFAULT_COMPONENT_NAME}"
TAG="${TAG:-$DEFAULT_TAG}"
BASE_IMAGE="${BASE_IMAGE:-$DEFAULT_BASE_IMAGE}"
BASE_TAG="${BASE_TAG:-$DEFAULT_BASE_TAG}"
CONTAINER_FILE="${CONTAINER_FILE:-$DEFAULT_CONTAINER_FILE}"
CACHE_FLAG="${CACHE_FLAG:-$DEFAULT_CACHE_FLAG}"
REGISTRY="${REGISTRY:-$DEFAULT_REGISTRY}"

LOCAL_IMAGE="${COMPONENT_NAME}:${TAG}"
REMOTE_IMAGE="${REGISTRY}/${COMPONENT_NAME}:${TAG}"

# --- Build the image ---
function build() {
  echo "🔨 Building image ${LOCAL_IMAGE} with base image ${BASE_IMAGE}:${BASE_TAG}"
  podman build ${CACHE_FLAG} \
    -t "${LOCAL_IMAGE}" \
    -f "${CONTAINER_FILE}" . \
    --build-arg BASE_IMAGE="${BASE_IMAGE}:${BASE_TAG}" \
    --build-arg COMPONENT_NAME="${COMPONENT_NAME}"
  echo "✅ Build complete: ${LOCAL_IMAGE}"
}

# --- Push the image to registry ---
function push() {
  echo "📤 Pushing image to ${REMOTE_IMAGE}..."
  podman tag "${LOCAL_IMAGE}" "${REMOTE_IMAGE}"
  podman push "${REMOTE_IMAGE}"
  echo "✅ Image pushed to: ${REMOTE_IMAGE}"
}

# --- Run the image ---
function run() {
  USE_REMOTE=false

  if [[ "${1:-}" == "--remote" ]]; then
    USE_REMOTE=true
    shift
  fi

  IMAGE_TO_RUN="${LOCAL_IMAGE}"
  if $USE_REMOTE; then
    echo "🌐 Pulling remote image ${REMOTE_IMAGE}..."
    podman pull "${REMOTE_IMAGE}"
    IMAGE_TO_RUN="${REMOTE_IMAGE}"
    echo "✅ Image pulled from: ${REMOTE_IMAGE}"
  else
    echo "🚀 Running local image ${LOCAL_IMAGE}..."
  fi

  # Pick env file
  if [ -f .test.env ]; then
    ENV_FILE=".test.env"
  else
    echo "❌ No .test.env file found."
    exit 1
  fi

  # source the env file
  source "${ENV_FILE}"

  # Check if DOCS_FOLDER is set
  if [ -z "${DOCS_FOLDER}" ]; then
    echo "❌ DOCS_FOLDER is not defined in ${ENV_FILE}"
    exit 1
  fi

  echo "📄 Using environment file: ${ENV_FILE}"

  # If LLAMA_STACK_HOST is localhost and OS is macOS, then set LLAMA_STACK_HOST to host.containers.internal
  if [ "${LLAMA_STACK_HOST}" = "localhost" ] && [ "$(uname -s)" = "Darwin" ]; then
    LLAMA_STACK_HOST="host.containers.internal"
  fi

  podman run --rm -it --name elegibility-aux \
    -e EMBEDDING_MODEL="${EMBEDDING_MODEL}" \
    -e EMBEDDING_DIMENSION="${EMBEDDING_DIMENSION}" \
    -e EMBEDDING_MODEL_PROVIDER="${EMBEDDING_MODEL_PROVIDER}" \
    -e LLAMA_STACK_HOST="${LLAMA_STACK_HOST}" \
    -e LLAMA_STACK_PORT="${LLAMA_STACK_PORT}" \
    -e LLAMA_STACK_SECURE="${LLAMA_STACK_SECURE}" \
    -e DOCS_FOLDER="${DOCS_FOLDER}" \
    -e CHUNK_SIZE_IN_TOKENS="${CHUNK_SIZE_IN_TOKENS}" \
    -e NO_PROXY="localhost,127.0.0.1,host.containers.internal" \
    -v "./docs:${DOCS_FOLDER}:ro,Z" \
    "${IMAGE_TO_RUN}"
}

# --- Show usage ---
function help() {
  echo "Usage: ./image.sh [build|push|run [--remote]|all]"
  echo "  build         Build the container image"
  echo "  push          Push the image to the registry"
  echo "  run           Run the local image"
  echo "  run --remote  Run the image pulled from the registry"
  echo "  all           Build, push, and run locally"
}

# --- Entrypoint ---
case "${1:-}" in
  build) build ;;
  push) push ;;
  run) shift; run "$@" ;;
  all)
    build
    push
    run
    ;;
  *) help ;;
esac
