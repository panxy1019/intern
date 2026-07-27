#!/usr/bin/env python3
"""Validate the exact physical Ascend devices exposed to this container."""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
from pathlib import Path


DEVICE_RE = re.compile(r"^davinci(\d+)$")


def read_mapping(mapping_file: Path | None) -> str:
    if mapping_file:
        return mapping_file.read_text(encoding="utf-8")
    return subprocess.run(
        ["npu-smi", "info", "-m"], check=True, capture_output=True, text=True
    ).stdout


def parse_mapping(text: str) -> dict[int, dict[str, int | str]]:
    rows: dict[int, dict[str, int | str]] = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 5 or fields[-1] != "Ascend910":
            continue
        npu_id, chip_id, logical_id, physical_id, _ = fields
        if not all(value.isdigit() for value in (npu_id, chip_id, logical_id, physical_id)):
            continue
        rows[int(logical_id)] = {
            "npu_id": int(npu_id),
            "chip_id": int(chip_id),
            "logical_id": int(logical_id),
            "physical_id": int(physical_id),
        }
    if not rows:
        raise RuntimeError("npu-smi info -m returned no Ascend910 mapping rows")
    return rows


def visible_logical_ids(device_root: Path) -> set[int]:
    visible: set[int] = set()
    for path in glob.glob(str(device_root / "davinci*")):
        match = DEVICE_RE.match(Path(path).name)
        if match:
            visible.add(int(match.group(1)))
    return visible


def validate(
    requested: set[int], mapping_text: str, device_root: Path
) -> dict[str, object]:
    rows = parse_mapping(mapping_text)
    raw_logical_ids = visible_logical_ids(device_root)
    target_rows = {
        logical_id: row
        for logical_id, row in rows.items()
        if int(row["physical_id"]) in requested
    }
    devices = []
    for logical_id, row in sorted(target_rows.items()):
        device_node = device_root / f"davinci{logical_id}"
        if not device_node.exists():
            raise RuntimeError(f"mapped device node does not exist: {device_node}")
        devices.append({**row, "device_node": str(device_node)})

    actual = {int(item["physical_id"]) for item in devices}
    if actual != requested:
        raise RuntimeError(
            f"visible physical IDs {sorted(actual)} do not exactly match requested "
            f"{sorted(requested)}"
        )
    visible_env = os.environ.get("ASCEND_VISIBLE_DEVICES", "")
    visible_ids = {
        int(item.strip()) for item in visible_env.split(",") if item.strip()
    }
    expected_logical = set(target_rows)
    if visible_ids and visible_ids != expected_logical:
        raise RuntimeError(
            f"ASCEND_VISIBLE_DEVICES logical IDs {sorted(visible_ids)} do not match "
            f"target mapping {sorted(expected_logical)}"
        )
    process_visible_count = len(visible_ids) if visible_ids else len(expected_logical)
    if process_visible_count != len(requested):
        raise RuntimeError(
            f"process-visible device count {process_visible_count} != requested "
            f"count {len(requested)}"
        )

    return {
        "requested_physical_ids": sorted(requested),
        "visible_device_count": process_visible_count,
        "visible_logical_ids": sorted(expected_logical),
        "raw_device_nodes": sorted(raw_logical_ids),
        "devices": devices,
        "valid": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--physical-ids", required=True)
    parser.add_argument("--output", type=Path, default=Path("/tmp/vllm-lab/npu-mapping.json"))
    parser.add_argument("--mapping-file", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--device-root", type=Path, default=Path("/dev"), help=argparse.SUPPRESS)
    args = parser.parse_args()

    requested = {
        int(item.strip()) for item in args.physical_ids.split(",") if item.strip()
    }
    if not requested:
        raise SystemExit("--physical-ids must not be empty")
    result = validate(requested, read_mapping(args.mapping_file), args.device_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
