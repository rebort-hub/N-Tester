#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
	echo "请先安装 Docker：https://docs.docker.com/get-docker/"
	exit 1
fi

dc() {
	if docker compose version >/dev/null 2>&1; then
		docker compose "$@"
	else
		docker-compose "$@"
	fi
}

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-vue-fastapi-admin}"

echo ">>> 启动栈（首次会构建镜像，可能较久）..."
dc -f docker-compose.yml up -d --build "$@"

echo ""
echo ">>> 就绪（默认端口）："
echo "    前端  http://localhost"
echo "    后端  http://localhost:8100"
echo "    MySQL localhost:3306  Redis localhost:6379"
echo ""
echo ">>> 更新：在本目录执行"
echo "    git pull && ./deploy/quick-start.sh"
echo "或发布镜像后："
echo "    docker compose pull && docker compose up -d"
