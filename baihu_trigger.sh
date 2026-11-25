#!/usr/bin/env bash
set -euo pipefail

# 白虎面板外部触发 GitHub Actions 工作流脚本
# 定时规则示例（北京时间 06:00）：0 6 * * * （或 6 位含秒格式 0 0 6 * * *）
# 需在白虎面板「变量机密」中配置 GH_PAT（具备 workflow 权限的 GitHub Token）

GH_REPO="${GH_REPO:-yuxiaojie0322-maker/katabump}"
GH_WORKFLOW="${GH_WORKFLOW:-renew.yml}"
GH_REF="${GH_REF:-main}"
TOKEN="${GH_PAT:-${GITHUB_TOKEN:-}}"

if [ -z "$TOKEN" ]; then
  echo "[$(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M:%S')] ❌ 未检测到 GH_PAT 或 GITHUB_TOKEN 环境变量"
  exit 1
fi

API_URL="https://api.github.com/repos/${GH_REPO}/actions/workflows/${GH_WORKFLOW}/dispatches"
BODY="{\"ref\":\"${GH_REF}\"}"

echo "[$(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M:%S')] 🚀 正在触发 GitHub Actions: ${GH_REPO} (${GH_WORKFLOW} @ ${GH_REF})..."

RESP_FILE=$(mktemp)
trap 'rm -f "$RESP_FILE"' EXIT

HTTP_CODE=$(curl -sS -o "$RESP_FILE" -w "%{http_code}" \
  -X POST "$API_URL" \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -H "Content-Type: application/json" \
  -d "$BODY")

if [ "$HTTP_CODE" = "204" ]; then
  echo "[$(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M:%S')] ✅ 触发成功 (HTTP 204)"
  exit 0
else
  echo "[$(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M:%S')] ❌ 触发失败 (HTTP ${HTTP_CODE})"
  cat "$RESP_FILE"
  echo ""
  exit 1
fi
