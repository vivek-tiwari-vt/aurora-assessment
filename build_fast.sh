#!/bin/bash

# Fast local build script for testing
# Builds for linux/amd64 platform with BuildKit caching

set -e

IMAGE_NAME="vivektiwari007/aurora-qa-system:latest"
DOCKERFILE="docker/Dockerfile"
PLATFORM="linux/amd64"

echo "=========================================="
echo "Fast Local Docker Build"
echo "=========================================="
echo "Platform: $PLATFORM"
echo "Image: $IMAGE_NAME"
echo ""

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1

# Build with BuildKit cache (local build, no push)
echo "Building image with BuildKit cache..."
docker buildx build \
    --platform $PLATFORM \
    --file $DOCKERFILE \
    --tag $IMAGE_NAME \
    --load \
    --progress=plain \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully built image!"
    echo ""
    echo "📦 Image: $IMAGE_NAME"
    echo ""
    echo "To push to Docker Hub:"
    echo "   docker push $IMAGE_NAME"
    echo ""
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi

