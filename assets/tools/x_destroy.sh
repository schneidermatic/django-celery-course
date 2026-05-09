#!/usr/bin/env bash
#==============================================================================
# FILE:    x_destroy.sh
# AUTHOR:  Markus Schneider
# PURPOSE: Stop and remove all containers, volumes, and locally built images.
# USAGE:   x_destroy.sh [directory]  — defaults to current working directory
#==============================================================================

set -e

TARGET_DIR="${1:-$PWD}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

echo -e "${RED}=== Destroy: $(basename "$TARGET_DIR") ===${NC}"
echo -e "${YELLOW}Removing containers and data volumes...${NC}"
$DC down -v
echo -e "${YELLOW}Removing orphans and locally built images...${NC}"
$DC down --remove-orphans --volumes --rmi local
if [ -f "app/db.sqlite3" ]; then
    rm -f "app/db.sqlite3"
    echo -e "${YELLOW}Removed app/db.sqlite3.${NC}"
fi
echo -e "${GREEN}✓ Teardown complete.${NC}"
