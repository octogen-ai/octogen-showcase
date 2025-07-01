#!/bin/bash

GIT_ROOT=$(git rev-parse --show-toplevel)

function build_python_docker_image() {
    local IMAGE_NAME=$1
    local DOCKER_FILENAME=${2:-Dockerfile}
    local SKIP_LATEST_TAG=${3:-false}

    REPOSITORY_URL="us-central1-docker.pkg.dev"
    PROJECT_ID="octogen-prod"
    REPOSITORY_NAME="octogen-repo"
    TIMESTAMP=$(date -u +%Y%m%d%H%M%S)
    IMAGE_TAG="$REPOSITORY_URL/$PROJECT_ID/$REPOSITORY_NAME/$IMAGE_NAME:$TIMESTAMP"
    LATEST_TAG="$REPOSITORY_URL/$PROJECT_ID/$REPOSITORY_NAME/$IMAGE_NAME:latest"
    PACKAGE_DIR="${GIT_ROOT}/feed"

    pushd "${PACKAGE_DIR}" > /dev/null || exit

    # Check if the builder instance exists
    if ! docker buildx ls | grep -q 'octogen-multiarch-builder'; then
        # Create a new builder instance
        docker buildx create --use --name octogen-multiarch-builder
    fi

    # Enable experimental features
    export DOCKER_CLI_EXPERIMENTAL=enabled

    # Add the platforms that you want to support
    docker buildx inspect --bootstrap

    echo "Building and pushing image with tags:"
    echo "  - $IMAGE_TAG"
    if [ "$SKIP_LATEST_TAG" != "true" ]; then
        echo "  - $LATEST_TAG"
    fi

    # Build the docker command
    DOCKER_CMD="docker buildx build -f \"${PACKAGE_DIR}/${DOCKER_FILENAME}\" \
        --platform linux/amd64,linux/arm64 \
        --target runtime \
        -t \"$IMAGE_TAG\""

    # Add latest tag if not skipping
    if [ "$SKIP_LATEST_TAG" != "true" ]; then
        DOCKER_CMD="$DOCKER_CMD -t \"$LATEST_TAG\""
    fi

    DOCKER_CMD="$DOCKER_CMD --push ."

    # Execute the command
    # shellcheck disable=SC2086
    eval $DOCKER_CMD

    popd > /dev/null || exit
}

build_python_docker_image "octogen-showcase-feed"
