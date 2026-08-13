#!/usr/bin/env bash
set -euo pipefail

IMAGE="swr.cn-south-1.myhuaweicloud.com/ascendhub/verl_pt27_25rc3:a2-arm"
docker rm -f verl-lighteval-test >/dev/null 2>&1 || true
docker run -d \
  --name verl-lighteval-test \
  --user root \
  --device /dev/davinci1:/dev/davinci0 \
  --device /dev/davinci_manager \
  --device /dev/hisi_hdc \
  --device /dev/devmm_svm \
  --device /dev/dvpp_cmdlist \
  -v /usr/local/Ascend/driver:/usr/local/Ascend/driver:ro \
  -v /usr/local/dcmi:/usr/local/dcmi:ro \
  -v /data/haidass-eval/models:/cache/models:ro \
  -v /data/haidass-eval/datasets:/cache/datasets:ro \
  -v /data/haidass-eval/build/track-a-rayjob/wheelhouse:/opt/wheelhouse:ro \
  -v /data/haidass-eval/build/track-a-rayjob:/opt/phase3-code:ro \
  -e HTTP_PROXY=http://110.120.0.3:18080 \
  -e HTTPS_PROXY=http://110.120.0.3:18080 \
  -e ALL_PROXY=socks5h://110.120.0.3:18081 \
  -e NO_PROXY=localhost,127.0.0.1,110.120.0.0/16,110.129.0.0/16 \
  "$IMAGE" sleep infinity
