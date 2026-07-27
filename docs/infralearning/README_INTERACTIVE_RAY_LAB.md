# Interactive Ray + vLLM Infra Lab

This lab is isolated in `infra-learning`. It uses ordinary Kubernetes
Deployments with `schedulerName: default-scheduler`; it does not use KubeRay,
Volcano, production `k12` Ray, MinerU, Dagster, or MinIO resources.

## Architecture and modes

```text
ray-vllm-lab-head (server-00, no NPU)
  ├─ GCS 6379
  ├─ Dashboard 8265
  └─ Ray Client 10001

mode 4:   worker-4a=1 (physical 8-11), worker-4b=0, worker-8=0
mode 4x2: worker-4a=1 (physical 8-11), worker-4b=1 (physical 12-15), worker-8=0
mode 8:   worker-4a=0, worker-4b=0, worker-8=1 (physical 8-15)
mode off: all Workers=0; Head remains running
```

Two four-card Workers are two independent TP4 model replicas. They are not a
cross-Pod TP8 model. TP8 can have higher communication overhead than TP4 and
must be evaluated with throughput and latency measurements.

## Initial deployment

Run as root on `server-00`:

```bash
cd /home/admin/testpanxy/infralearning

k3s kubectl apply -f vllm-interactive-lab-head.yaml
k3s kubectl -n infra-learning create configmap vllm-lab-scripts \
  --from-file=discover_npu_mapping.py \
  --from-file=vllm-command-examples.sh \
  --dry-run=client -o yaml | k3s kubectl apply -f -

k3s kubectl apply -f vllm-interactive-lab-worker-4a.yaml
k3s kubectl apply -f vllm-interactive-lab-worker-4b.yaml
k3s kubectl apply -f vllm-interactive-lab-worker-8.yaml
k3s kubectl -n infra-learning get deploy,pod,svc -o wide
./validate-vllm-lab.sh
```

Only Head and Worker 4A start. Mapping validation runs before `ray start`; a
mapping mismatch exits the Worker without starting Ray or vLLM.

The privileged container exposes all raw `/dev/davinci*` nodes on this cluster.
Physical ownership is still enforced by the Kubernetes NPU request plus the
fixed-card annotation. `discover_npu_mapping.py` verifies that allocation and
the requested physical/logical mapping. `ASCEND_VISIBLE_DEVICES` then restricts
the experiment process to the verified logical set; it is an auxiliary process
isolation control, never a replacement for Kubernetes device allocation.

## Enter Worker 4A

```bash
WORKER=$(
  k3s kubectl -n infra-learning get pod \
    -l app=ray-vllm-lab-worker-4a \
    -o jsonpath='{.items[0].metadata.name}'
)
k3s kubectl -n infra-learning exec -it "$WORKER" -c ray-worker -- bash
```

Inside the Worker:

```bash
cat /tmp/vllm-lab/npu-mapping.json
ray status
npu-smi info
source /opt/vllm-lab/vllm-command-examples.sh
tp4
```

The Worker starts only Ray automatically. `tp4` is always a manual action.

## Access

```bash
# Dashboard
k3s kubectl -n infra-learning port-forward svc/ray-vllm-lab-head 8265:8265

# Worker 4A vLLM
k3s kubectl -n infra-learning port-forward pod/"$WORKER" 8000:8000

# dual TP4: use local 8000 for 4A and local 8001 for 4B
k3s kubectl -n infra-learning port-forward pod/<worker-4a> 8000:8000
k3s kubectl -n infra-learning port-forward pod/<worker-4b> 8001:8000
```

## Safe mode switching

Stop every manually started `vllm serve` process first. The script refuses to
switch while it detects vLLM, scales overlapping groups to zero, waits for Pod
deletion, checks cluster-wide NPU annotations, and only then starts the target
group.

```bash
./set-vllm-lab-mode.sh status
./set-vllm-lab-mode.sh 4
./set-vllm-lab-mode.sh 4x2
./set-vllm-lab-mode.sh 8
./set-vllm-lab-mode.sh off
```

For mode `8`, enter `ray-vllm-lab-worker-8`, source the examples file, and run
`tp8`. Do not start `npu-8` together with either four-card Worker.

## Validation and shutdown

```bash
./validate-vllm-lab.sh

# Stop Workers but retain Head
./set-vllm-lab-mode.sh off

# Remove only this experiment
k3s kubectl delete namespace infra-learning
```

The deprecated KubeRay manifest is retained under `deprecated/` for history
only. Do not apply it while the operator is configured with
`--batch-scheduler=volcano`.
