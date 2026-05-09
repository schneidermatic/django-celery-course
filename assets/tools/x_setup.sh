#!/usr/bin/env bash
#==============================================================================
# FILE:    x_setup.sh
# AUTHOR:  Markus Schneider
# PURPOSE: Build and start all Docker Compose services.
# USAGE:   x_setup.sh [directory]  — defaults to current working directory
#==============================================================================

set -e

TARGET_DIR="${1:-$PWD}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

if ! command -v docker &>/dev/null; then
    echo -e "${RED}✗ Docker not found.${NC}" && exit 1
fi

if docker compose version &>/dev/null 2>&1; then
    DC="docker compose"
elif docker-compose version &>/dev/null 2>&1; then
    DC="docker-compose"
else
    echo -e "${RED}✗ Docker Compose not found.${NC}" && exit 1
fi

cd "$TARGET_DIR"

if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}✗ No docker-compose.yml found in $(pwd).${NC}" && exit 1
fi

echo -e "${GREEN}=== Setup: $(basename "$TARGET_DIR") ===${NC}"
echo -e "${YELLOW}Building and starting services...${NC}"
$DC up -d --build
echo -e "${GREEN}✓ All services started.${NC}"
