#!/usr/bin/env bash

# Fail fast: 未定義変数・コマンド失敗・パイプ失敗を即時検知する
set -euo pipefail

# 実行時オプション（必要に応じて環境変数で上書き可能）
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ENV_FILE=${ENV_FILE:-"${REPO_ROOT}/.env"}
STACK_NAME=${STACK_NAME:-ai-curated-newsletter}
SAM_CONFIG_FILE=${SAM_CONFIG_FILE:-"${REPO_ROOT}/samconfig.toml"}
SAM_CONFIG_ENV=${SAM_CONFIG_ENV:-default}
SAM_S3_BUCKET=${SAM_S3_BUCKET:-}
SAM_CAPABILITIES=${SAM_CAPABILITIES:-CAPABILITY_IAM}

echo ">>> Starting SAM deployment at $(date +%s%3N)"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: ${ENV_FILE} not found"
  exit 1
fi

# .env を export 付きで読み込み、後続コマンドから参照可能にする
echo ">>> Loading environment from ${ENV_FILE}"
# shellcheck disable=SC1090
set -a
source "${ENV_FILE}"
set +a

# デフォルトリージョン（.env 未設定時のフォールバック）
AWS_REGION=${AWS_REGION:-ap-northeast-1}

# SAM パラメータとして渡すメールアドレスが空ならここで停止する
: "${FROM_EMAIL:?FROM_EMAIL is required in ${ENV_FILE}}"
: "${TO_EMAIL:?TO_EMAIL is required in ${ENV_FILE}}"

# samconfig.toml があればそれを利用し、なければデフォルト設定で build
echo ">>> sam build"
if [[ -f "${SAM_CONFIG_FILE}" ]]; then
  sam build \
    --config-file "${SAM_CONFIG_FILE}" \
    --config-env "${SAM_CONFIG_ENV}"
else
  sam build
fi

echo ">>> sam deploy"
# 引数は末尾 "$@" で透過的に渡せる（例: --no-confirm-changeset）
DEPLOY_ARGS=(
  --region "${AWS_REGION}"
  --stack-name "${STACK_NAME}"
  --parameter-overrides
  "FromEmail=${FROM_EMAIL}"
  "ToEmail=${TO_EMAIL}"
)

if [[ -f "${SAM_CONFIG_FILE}" ]]; then
  DEPLOY_ARGS+=(--config-file "${SAM_CONFIG_FILE}" --config-env "${SAM_CONFIG_ENV}")
fi

has_cli_s3_option=false
for arg in "$@"; do
  case "${arg}" in
    --resolve-s3|--s3-bucket|--s3-bucket=*)
      has_cli_s3_option=true
      break
      ;;
  esac
done

has_config_s3_option=false
if [[ -f "${SAM_CONFIG_FILE}" ]]; then
  if grep -Eq '^[[:space:]]*s3_bucket[[:space:]]*=' "${SAM_CONFIG_FILE}" || \
     grep -Eq '^[[:space:]]*resolve_s3[[:space:]]*=[[:space:]]*true' "${SAM_CONFIG_FILE}"; then
    has_config_s3_option=true
  fi
fi

if [[ "${has_cli_s3_option}" == false && "${has_config_s3_option}" == false ]]; then
  if [[ -n "${SAM_S3_BUCKET}" ]]; then
    echo ">>> sam deploy uses SAM_S3_BUCKET=${SAM_S3_BUCKET}"
    DEPLOY_ARGS+=(--s3-bucket "${SAM_S3_BUCKET}")
  else
    echo ">>> sam deploy enables --resolve-s3 (no S3 setting found)"
    DEPLOY_ARGS+=(--resolve-s3)
  fi
fi

has_cli_capabilities_option=false
for arg in "$@"; do
  case "${arg}" in
    --capabilities|--capabilities=*)
      has_cli_capabilities_option=true
      break
      ;;
  esac
done

has_config_capabilities_option=false
if [[ -f "${SAM_CONFIG_FILE}" ]]; then
  if grep -Eq '^[[:space:]]*capabilities[[:space:]]*=' "${SAM_CONFIG_FILE}"; then
    has_config_capabilities_option=true
  fi
fi

if [[ "${has_cli_capabilities_option}" == false && "${has_config_capabilities_option}" == false ]]; then
  echo ">>> sam deploy enables --capabilities ${SAM_CAPABILITIES}"
  DEPLOY_ARGS+=(--capabilities "${SAM_CAPABILITIES}")
fi

sam deploy "${DEPLOY_ARGS[@]}" "$@"
