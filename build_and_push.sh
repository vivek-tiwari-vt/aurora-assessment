#!/bin/bash

# Fast Docker build and push script with BuildKit caching
# Optimized for linux/amd64 platform

set -e

IMAGE_NAME="vivektiwari007/aurora-qa-system:latest"
DOCKERFILE="docker/Dockerfile"
PLATFORM="linux/amd64"

echo "=========================================="
echo "Building Docker Image (Fast Build)"
echo "=========================================="
echo "Platform: $PLATFORM"
echo "Image: $IMAGE_NAME"
echo ""
echo "⚡ Optimizations:"
echo "  - Using torch CPU-only (~200MB vs ~4GB)"
echo "  - Multi-stage build for smaller image"
echo "  - BuildKit cache for faster rebuilds"
echo ""

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build with BuildKit cache and push in one command
# This uses buildx with cache mounts and inline cache
echo "Building and pushing image with BuildKit cache..."
docker buildx build \
    --platform $PLATFORM \
    --file $DOCKERFILE \
    --tag $IMAGE_NAME \
    --cache-from type=registry,ref=$IMAGE_NAME \
    --cache-to type=inline \
    --push \
    --progress=plain \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully built and pushed image!"
    echo ""
    echo "📦 Docker Image URL:"
    echo "   https://hub.docker.com/r/vivektiwari007/aurora-qa-system"
    echo ""
    echo "🐳 Pull command:"
    echo "   docker pull $IMAGE_NAME"
    echo ""
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi

