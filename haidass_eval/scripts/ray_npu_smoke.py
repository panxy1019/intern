import json
import hashlib
import os
import platform
import time
import urllib.request

import ray


@ray.remote(num_cpus=1, resources={"NPU": 1, "HAIDASS_EVAL": 1})
def inspect_worker():
    import torch
    import torch_npu

    torch.npu.set_device(0)
    left = torch.randn((512, 512), dtype=torch.bfloat16, device="npu:0")
    right = torch.randn((512, 512), dtype=torch.bfloat16, device="npu:0")
    result = left @ right
    torch.npu.synchronize()

    with urllib.request.urlopen(
        "http://haidass-model-cache.haidass-eval.svc.cluster.local:8081/config.json",
        timeout=30,
    ) as response:
        model_config = json.load(response)

    base_url = "http://haidass-model-cache.haidass-eval.svc.cluster.local:8081"
    with urllib.request.urlopen(f"{base_url}/SHA256SUMS", timeout=30) as response:
        checksums = response.read().decode()
    expected_sha256 = next(
        line.split()[0]
        for line in checksums.splitlines()
        if line.endswith("./model.safetensors")
    )
    model_sha256 = hashlib.sha256()
    model_bytes = 0
    download_started = time.monotonic()
    with urllib.request.urlopen(f"{base_url}/model.safetensors", timeout=120) as response:
        while chunk := response.read(8 * 1024 * 1024):
            model_sha256.update(chunk)
            model_bytes += len(chunk)
    model_download_seconds = time.monotonic() - download_started
    actual_sha256 = model_sha256.hexdigest()
    if actual_sha256 != expected_sha256:
        raise RuntimeError(
            f"Model checksum mismatch: expected {expected_sha256}, got {actual_sha256}"
        )

    return {
        "hostname": platform.node(),
        "architecture": platform.machine(),
        "ray_resources": ray.get_runtime_context().get_assigned_resources(),
        "visible_devices": os.environ.get("ASCEND_RT_VISIBLE_DEVICES"),
        "torch": str(torch.__version__),
        "torch_npu": str(torch_npu.__version__),
        "npu_count": torch.npu.device_count(),
        "device_name": torch.npu.get_device_name(0),
        "bf16_matmul_finite": bool(torch.isfinite(result.float()).all().cpu()),
        "model_type": model_config.get("model_type"),
        "architectures": model_config.get("architectures"),
        "model_bytes_verified": model_bytes,
        "model_sha256": actual_sha256,
        "model_download_seconds": round(model_download_seconds, 3),
    }


ray.init(address="auto")
print(json.dumps(ray.get(inspect_worker.remote()), indent=2, ensure_ascii=False))
