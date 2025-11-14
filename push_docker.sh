#!/bin/bash

# Script to push Docker image to Docker Hub and make it public

set -e

IMAGE_NAME="vivek-tiwari-vt/aurora-qa-system:latest"
DOCKER_HUB_USERNAME="vivek-tiwari-vt"

echo "=========================================="
echo "Pushing Docker Image to Docker Hub"
echo "=========================================="
echo ""

# Check if logged in
if ! docker info | grep -q "Username"; then
    echo "⚠️  Not logged into Docker Hub"
    echo ""
    echo "Please log in with:"
    echo "  docker login"
    echo ""
    echo "Or log in directly:"
    echo "  docker login -u vivek-tiwari-vt"
    echo ""
    read -p "Press Enter after logging in, or Ctrl+C to cancel..."
fi

# Build the image if not exists
if ! docker images | grep -q "aurora-qa-system"; then
    echo "Building Docker image..."
    docker build -f docker/Dockerfile -t $IMAGE_NAME .
fi

# Push the image
echo ""
echo "Pushing image to Docker Hub..."
echo "Image: $IMAGE_NAME"
echo ""

if docker push $IMAGE_NAME; then
    echo ""
    echo "✅ Successfully pushed to Docker Hub!"
    echo ""
    echo "📦 Docker Image URL:"
    echo "   https://hub.docker.com/r/vivek-tiwari-vt/aurora-qa-system"
    echo ""
    echo "🐳 Pull command:"
    echo "   docker pull vivek-tiwari-vt/aurora-qa-system:latest"
    echo ""
    echo "⚠️  IMPORTANT: Make sure the repository is PUBLIC on Docker Hub:"
    echo "   1. Go to: https://hub.docker.com/r/vivek-tiwari-vt/aurora-qa-system/settings"
    echo "   2. Scroll to 'Repository Visibility'"
    echo "   3. Click 'Make Public'"
    echo ""
else
    echo ""
    echo "❌ Failed to push. Please check:"
    echo "   1. You're logged in: docker login"
    echo "   2. You have permission to push to vivek-tiwari-vt/aurora-qa-system"
    echo "   3. The repository exists on Docker Hub"
    exit 1
fi

