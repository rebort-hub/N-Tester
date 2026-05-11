#!/usr/bin/env bash
# 可被托管后使用：curl -fsSL https://域名/deploy/curl-install.sh | bash
# 行为：克隆（或更新）本仓库到 INSTALL_DIR，再 docker compose up -d --build
set -euo pipefail

: "${INSTALL_DIR:=${HOME}/vue-fastapi-admin}"
: "${GIT_REPO:=}"
: "${GIT_BRANCH:=main}"

if ! command -v docker >/dev/null 2>&1; then
	echo "请先安装 Docker 与 Compose：https://docs.docker.com/compose/install/"
	exit 1
fi

dc() {
	if docker compose version >/dev/null 2>&1; then
		docker compose "$@"
	else
		docker-compose "$@"
	fi
}

if [[ -z "${GIT_REPO}" ]]; then
	echo "请设置环境变量 GIT_REPO 为你的仓库地址，例如："
	echo "  export GIT_REPO=https://github.com/rebort-hub/N-Tester.git"
	echo "  curl -fsSL .../curl-install.sh | bash"
	exit 1
fi

if [[ -d "${INSTALL_DIR}/.git" ]]; then
	echo ">>> 更新代码: ${INSTALL_DIR}"
	git -C "${INSTALL_DIR}" fetch --depth 1 origin "${GIT_BRANCH}" || true
	git -C "${INSTALL_DIR}" checkout "${GIT_BRANCH}" || true
	git -C "${INSTALL_DIR}" pull --ff-only origin "${GIT_BRANCH}" || true
else
	echo ">>> 克隆到: ${INSTALL_DIR}"
	git clone --depth 1 --branch "${GIT_BRANCH}" "${GIT_REPO}" "${INSTALL_DIR}"
fi

cd "${INSTALL_DIR}"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-vue-fastapi-admin}"

echo ">>> 启动 Docker 栈..."
dc -f docker-compose.yml up -d --build

echo ""
echo ">>> 完成：前端 http://localhost （映射 80）"
