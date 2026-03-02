#!/usr/bin/env bash
# .env の内容を SSM Parameter Store に同期する
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ENV_FILE=${ENV_FILE:-"${REPO_ROOT}/.env"}
SSM_DOTENV_PARAMETER=${SSM_DOTENV_PARAMETER:-/ai-curated-newsletter/dotenv}

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: ${ENV_FILE} not found"
  exit 1
fi

set -a; source "${ENV_FILE}"; set +a
AWS_REGION=${AWS_REGION:-ap-northeast-1}

PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
[[ -x "${PYTHON_BIN}" ]] || PYTHON_BIN="python3"

echo ">>> Uploading .env to SSM: ${SSM_DOTENV_PARAMETER} (region: ${AWS_REGION})"
"${PYTHON_BIN}" "${REPO_ROOT}/scripts/sync_env_to_ssm.py" \
  --env-file "${ENV_FILE}" \
  --parameter-name "${SSM_DOTENV_PARAMETER}" \
  --region "${AWS_REGION}"
