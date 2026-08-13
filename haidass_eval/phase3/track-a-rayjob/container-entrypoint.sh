#!/usr/bin/env bash
set -e
source /root/miniconda3/etc/profile.d/conda.sh
conda activate ms
set +u
if [[ -f /usr/local/Ascend/driver/bin/setenv.bash ]]; then
  source /usr/local/Ascend/driver/bin/setenv.bash
fi
source /usr/local/Ascend/cann/ascend-toolkit/set_env.sh
if [[ -f /usr/local/Ascend/cann/nnal/atb/set_env.sh ]]; then
  source /usr/local/Ascend/cann/nnal/atb/set_env.sh
fi
set -u
export LD_LIBRARY_PATH="/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:${LD_LIBRARY_PATH:-}"
ulimit -n 65536
exec "$@"
