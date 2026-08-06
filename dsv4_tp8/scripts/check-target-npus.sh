#!/usr/bin/env bash
set -euo pipefail

TARGET_MAX_BOARD_ID="${TARGET_MAX_BOARD_ID:-3}"
OUTPUT="$(npu-smi info)"

PROCESS_ROWS="$({
  printf '%s\n' "${OUTPUT}" | awk -F'|' -v max_board="${TARGET_MAX_BOARD_ID}" '
    function trim(value) {
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
      return value
    }
    {
      device = trim($2)
      pid = trim($3)
      name = trim($4)
      split(device, parts, /[[:space:]]+/)
      if (parts[1] ~ /^[0-9]+$/ && parts[1] <= max_board &&
          pid ~ /^[0-9]+$/ && name != "") {
        print $0
      }
    }
  '
} || true)"

if [[ -n "${PROCESS_ROWS}" ]]; then
  echo "Target physical boards 0..${TARGET_MAX_BOARD_ID} are busy:" >&2
  printf '%s\n' "${PROCESS_ROWS}" >&2
  exit 50
fi

echo "Target physical boards 0..${TARGET_MAX_BOARD_ID} are process-free."

