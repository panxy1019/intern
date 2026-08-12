#!/usr/bin/env bash
set -euo pipefail

MODEL_ID="${MODEL_ID:-DALabCommunity/Haidass-143M-v1}"
REVISION="${REVISION:-6f668e57712b756024425dff07c931b55636091f}"
MODEL_DIR="${MODEL_DIR:-/home/admin/models/Haidass-143M-v1}"
HF_ENDPOINT="${HF_ENDPOINT:-https://huggingface.co}"

mkdir -p "$MODEL_DIR"

mapfile -t files < <(
  curl --fail --silent --show-error --location \
    "$HF_ENDPOINT/api/models/$MODEL_ID/revision/$REVISION" |
    jq -r '.siblings[].rfilename'
)

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No files returned for $MODEL_ID at $REVISION" >&2
  exit 1
fi

for file in "${files[@]}"; do
  destination="$MODEL_DIR/$file"
  mkdir -p "$(dirname "$destination")"
  echo "Downloading $file"
  curl --fail --location \
    --retry 6 --retry-all-errors --retry-delay 2 \
    --continue-at - \
    --output "$destination.part" \
    "$HF_ENDPOINT/$MODEL_ID/resolve/$REVISION/$file?download=true"
  mv "$destination.part" "$destination"
done

printf '%s\n' "$MODEL_ID" >"$MODEL_DIR/MODEL_ID"
printf '%s\n' "$REVISION" >"$MODEL_DIR/REVISION"
(
  cd "$MODEL_DIR"
  find . -type f \
    ! -path './.cache/*' \
    ! -name SHA256SUMS \
    -print0 | sort -z | xargs -0 sha256sum >SHA256SUMS
  sha256sum --check SHA256SUMS
)

du -sh "$MODEL_DIR"
