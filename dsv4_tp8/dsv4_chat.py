#!/usr/bin/env python3
"""
DeepSeek-V4-Flash-0731 多轮对话客户端。

特点：
1. 调用 OpenAI 兼容的 /v1/chat/completions 接口。
2. 对话历史持久化到本地 JSON 文件。
3. 支持继续旧会话、创建新会话、切换会话。
4. 不依赖 openai、requests 等第三方 Python 包。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = os.environ.get(
    "DSV4_BASE_URL",
    "http://127.0.0.1:8900/v1",
)

DEFAULT_MODEL = os.environ.get(
    "DSV4_MODEL",
    "DeepSeek-V4-Flash-0731-w8a8",
)

DEFAULT_HISTORY_DIR = Path(
    os.environ.get(
        "DSV4_HISTORY_DIR",
        str(Path.home() / ".dsv4_chat"),
    )
)

DEFAULT_SYSTEM_PROMPT = (
    "你是一个严谨、专业的人工智能助手。"
    "请优先使用中文回答，并在不确定时明确说明。"
)


class ChatError(RuntimeError):
    """聊天接口调用失败。"""


class PortForwardError(RuntimeError):
    """Kubernetes 端口转发未能就绪。"""


def safe_session_name(name: str) -> str:
    """将会话名转换为安全文件名。"""
    allowed = []

    for char in name.strip():
        if char.isalnum() or char in {"-", "_", "."}:
            allowed.append(char)
        else:
            allowed.append("_")

    result = "".join(allowed).strip("._")

    if not result:
        raise ValueError("会话名不能为空。")

    return result


def session_path(history_dir: Path, session_name: str) -> Path:
    return history_dir / f"{safe_session_name(session_name)}.json"


def create_session_name() -> str:
    return datetime.now().strftime("chat-%Y%m%d-%H%M%S")


def create_new_history(
    session_name: str,
    system_prompt: str,
) -> dict[str, Any]:
    return {
        "session_name": session_name,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            }
        ],
    }


def save_history(
    history_dir: Path,
    history: dict[str, Any],
) -> None:
    history_dir.mkdir(parents=True, exist_ok=True)

    history["updated_at"] = datetime.now().isoformat(timespec="seconds")

    path = session_path(
        history_dir,
        str(history["session_name"]),
    )

    temporary_path = path.with_suffix(".json.tmp")

    temporary_path.write_text(
        json.dumps(
            history,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    temporary_path.replace(path)


def load_history(
    history_dir: Path,
    session_name: str,
) -> dict[str, Any]:
    path = session_path(history_dir, session_name)

    if not path.exists():
        raise FileNotFoundError(f"会话不存在：{session_name}")

    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data.get("messages"), list):
        raise ValueError(f"会话文件格式错误：{path}")

    return data


def list_sessions(history_dir: Path) -> list[dict[str, str]]:
    if not history_dir.exists():
        return []

    sessions: list[dict[str, str]] = []

    for path in history_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))

            sessions.append(
                {
                    "session_name": str(
                        data.get("session_name", path.stem)
                    ),
                    "updated_at": str(
                        data.get("updated_at", "")
                    ),
                    "message_count": str(
                        len(data.get("messages", []))
                    ),
                }
            )
        except (OSError, ValueError, TypeError):
            continue

    sessions.sort(
        key=lambda item: item["updated_at"],
        reverse=True,
    )

    return sessions


def latest_session_name(history_dir: Path) -> str | None:
    sessions = list_sessions(history_dir)

    if not sessions:
        return None

    return sessions[0]["session_name"]


def post_json(
    url: str,
    payload: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer EMPTY",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            response_body = response.read().decode("utf-8")

    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise ChatError(
            f"HTTP {exc.code}: {error_body}"
        ) from exc

    except urllib.error.URLError as exc:
        raise ChatError(
            f"无法连接模型服务：{exc}"
        ) from exc

    try:
        result = json.loads(response_body)

    except json.JSONDecodeError as exc:
        raise ChatError(
            f"服务返回的不是合法 JSON：{response_body[:1000]}"
        ) from exc

    return result


def get_json(url: str, timeout: int) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise ChatError(f"服务预检失败：{exc}") from exc


def check_service(base_url: str, timeout: int) -> None:
    health_url = base_url.rstrip("/").removesuffix("/v1") + "/health"
    try:
        with urllib.request.urlopen(health_url, timeout=timeout) as response:
            if response.status != 200:
                raise ChatError(f"服务健康检查返回 HTTP {response.status}")
    except urllib.error.URLError as exc:
        raise ChatError(f"无法连接模型服务：{exc}") from exc


def start_port_forward(
    namespace: str,
    service: str,
    local_port: int,
    timeout: int,
) -> subprocess.Popen[str]:
    kubectl = shutil.which("kubectl")
    if not kubectl:
        raise PortForwardError("未找到 kubectl，无法创建端口转发。")

    process = subprocess.Popen(
        [
            kubectl,
            "-n",
            namespace,
            "port-forward",
            f"service/{service}",
            f"{local_port}:8900",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    base_url = f"http://127.0.0.1:{local_port}/v1"
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise PortForwardError(
                "kubectl port-forward 已退出：" + output.strip()
            )
        try:
            check_service(base_url, timeout=2)
            return process
        except ChatError:
            time.sleep(0.5)

    process.terminate()
    process.wait(timeout=10)
    raise PortForwardError("等待 kubectl port-forward 或 vLLM 健康检查超时。")


def stop_port_forward(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def request_completion(
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    timeout: int,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    result = post_json(
        url=url,
        payload=payload,
        timeout=timeout,
    )

    try:
        content = result["choices"][0]["message"]["content"]

    except (KeyError, IndexError, TypeError) as exc:
        raise ChatError(
            "无法从响应中提取模型回答："
            + json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        ) from exc

    if not isinstance(content, str):
        content = str(content)

    return content


def request_streaming_completion(
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    timeout: int,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer EMPTY",
        },
        method="POST",
    )
    chunks: list[str] = []

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                payload_text = line[5:].strip()
                if payload_text == "[DONE]":
                    break
                event = json.loads(payload_text)
                delta = event.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content")
                if isinstance(content, str) and content:
                    chunks.append(content)
                    print(content, end="", flush=True)
    except urllib.error.HTTPError as exc:
        raise ChatError(
            f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')}"
        ) from exc
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise ChatError(f"流式请求失败：{exc}") from exc

    answer = "".join(chunks)
    if not answer:
        raise ChatError("流式响应未包含 assistant content。")
    return answer


def print_sessions(
    history_dir: Path,
    current_session: str | None = None,
) -> None:
    sessions = list_sessions(history_dir)

    if not sessions:
        print("当前没有已保存的会话。")
        return

    print("\n已有会话：")

    for item in sessions:
        marker = "*" if item["session_name"] == current_session else " "

        print(
            f"{marker} {item['session_name']}"
            f"  更新时间={item['updated_at']}"
            f"  消息数={item['message_count']}"
        )

    print()


def show_help() -> None:
    print(
        """
可用命令：

  /help
      查看命令帮助。

  /new
      创建一个新的空白会话。

  /new 会话名
      使用指定名称创建新会话。

  /list
      查看所有已保存会话。

  /switch 会话名
      切换到指定历史会话。

  /clear
      清空当前会话，只保留 system prompt。

  /history
      显示当前会话历史。

  /info
      显示当前配置。

  /exit
      保存当前会话并退出。
"""
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DeepSeek-V4 多轮持久化聊天客户端"
    )

    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"OpenAI 兼容接口地址，默认：{DEFAULT_BASE_URL}",
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"模型名称，默认：{DEFAULT_MODEL}",
    )

    parser.add_argument(
        "--history-dir",
        type=Path,
        default=DEFAULT_HISTORY_DIR,
        help=f"历史记录目录，默认：{DEFAULT_HISTORY_DIR}",
    )

    parser.add_argument(
        "--session",
        help="加载或创建指定名称的会话",
    )

    parser.add_argument(
        "--new",
        action="store_true",
        help="创建一个新会话，而不是恢复最近会话",
    )

    parser.add_argument(
        "--system-prompt",
        default=DEFAULT_SYSTEM_PROMPT,
        help="新会话使用的 system prompt",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="采样温度，默认 0.7",
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=2048,
        help="每轮最大输出 token 数，默认 2048",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="HTTP 超时时间，单位秒，默认 1800",
    )

    parser.add_argument(
        "--stream",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="流式输出回答，默认启用；使用 --no-stream 关闭",
    )

    parser.add_argument(
        "--port-forward",
        action="store_true",
        help="自动创建到 ds/dsv4-vllm 的本机端口转发",
    )

    parser.add_argument(
        "--namespace",
        default="ds",
        help="端口转发使用的 Kubernetes namespace，默认 ds",
    )

    parser.add_argument(
        "--service",
        default="dsv4-vllm",
        help="端口转发使用的 Kubernetes Service，默认 dsv4-vllm",
    )

    parser.add_argument(
        "--local-port",
        type=int,
        default=8900,
        help="自动端口转发的本机端口，默认 8900",
    )

    return parser.parse_args()


def initialize_history(
    args: argparse.Namespace,
) -> dict[str, Any]:
    args.history_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    if args.new:
        name = args.session or create_session_name()

        history = create_new_history(
            name,
            args.system_prompt,
        )

        save_history(args.history_dir, history)
        return history

    if args.session:
        path = session_path(
            args.history_dir,
            args.session,
        )

        if path.exists():
            return load_history(
                args.history_dir,
                args.session,
            )

        history = create_new_history(
            args.session,
            args.system_prompt,
        )

        save_history(args.history_dir, history)
        return history

    latest = latest_session_name(args.history_dir)

    if latest:
        return load_history(
            args.history_dir,
            latest,
        )

    name = create_session_name()

    history = create_new_history(
        name,
        args.system_prompt,
    )

    save_history(args.history_dir, history)
    return history


def run_chat(args: argparse.Namespace) -> int:

    try:
        history = initialize_history(args)

    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            f"加载历史记录失败：{exc}",
            file=sys.stderr,
        )
        return 1

    print("=" * 72)
    print("DeepSeek-V4-Flash-0731 多轮对话客户端")
    print(f"服务地址：{args.base_url}")
    print(f"模型名称：{args.model}")
    print(f"当前会话：{history['session_name']}")
    print(f"历史目录：{args.history_dir}")
    print(f"流式输出：{'开启' if args.stream else '关闭'}")
    print("输入 /help 查看命令。")
    print("=" * 72)

    while True:
        try:
            user_input = input("\n你：").strip()

        except EOFError:
            print("\n检测到 EOF，正在保存并退出。")
            save_history(args.history_dir, history)
            return 0

        except KeyboardInterrupt:
            print("\n再次按 Ctrl+C 不会丢失历史，当前会话已保存。")
            save_history(args.history_dir, history)
            continue

        if not user_input:
            continue

        if user_input == "/exit":
            save_history(args.history_dir, history)
            print("会话已保存。")
            return 0

        if user_input == "/help":
            show_help()
            continue

        if user_input == "/list":
            print_sessions(
                args.history_dir,
                str(history["session_name"]),
            )
            continue

        if user_input == "/info":
            print(f"当前会话：{history['session_name']}")
            print(f"消息数量：{len(history['messages'])}")
            print(f"服务地址：{args.base_url}")
            print(f"模型名称：{args.model}")
            print(f"temperature：{args.temperature}")
            print(f"max_tokens：{args.max_tokens}")
            print(f"历史文件：{session_path(args.history_dir, history['session_name'])}")
            continue

        if user_input == "/history":
            print()

            for index, message in enumerate(
                history["messages"],
                start=1,
            ):
                print(
                    f"[{index}] {message.get('role', 'unknown')}:"
                )
                print(message.get("content", ""))
                print()

            continue

        if user_input.startswith("/new"):
            parts = user_input.split(maxsplit=1)

            name = (
                parts[1].strip()
                if len(parts) == 2
                else create_session_name()
            )

            try:
                save_history(args.history_dir, history)

                history = create_new_history(
                    safe_session_name(name),
                    args.system_prompt,
                )

                save_history(args.history_dir, history)

                print(
                    f"已创建新会话：{history['session_name']}"
                )

            except (OSError, ValueError) as exc:
                print(f"创建新会话失败：{exc}")

            continue

        if user_input.startswith("/switch "):
            name = user_input.split(
                maxsplit=1,
            )[1].strip()

            try:
                save_history(args.history_dir, history)

                history = load_history(
                    args.history_dir,
                    name,
                )

                print(
                    f"已切换到会话：{history['session_name']}"
                )

            except (
                OSError,
                ValueError,
                json.JSONDecodeError,
            ) as exc:
                print(f"切换会话失败：{exc}")

            continue

        if user_input == "/clear":
            current_name = str(history["session_name"])

            history = create_new_history(
                current_name,
                args.system_prompt,
            )

            save_history(args.history_dir, history)

            print("当前会话历史已清空。")
            continue

        history["messages"].append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        # 在请求前先保存用户输入，避免调用过程中终端断开导致问题丢失。
        save_history(args.history_dir, history)

        try:
            if args.stream:
                print("\nDeepSeek：", end="", flush=True)
                answer = request_streaming_completion(
                    base_url=args.base_url,
                    model=args.model,
                    messages=history["messages"],
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                    timeout=args.timeout,
                )
                print()
            else:
                answer = request_completion(
                    base_url=args.base_url,
                    model=args.model,
                    messages=history["messages"],
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                    timeout=args.timeout,
                )

        except ChatError as exc:
            print(f"\n请求失败：{exc}")

            # 请求失败时删除尚未获得回复的最后一条 user 消息，
            # 避免下次恢复时出现不完整的一问无答。
            if (
                history["messages"]
                and history["messages"][-1].get("role") == "user"
            ):
                history["messages"].pop()

            save_history(args.history_dir, history)
            continue

        if not args.stream:
            print(f"\nDeepSeek：{answer}")

        history["messages"].append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        save_history(args.history_dir, history)


def main() -> int:
    args = parse_args()
    port_forward: subprocess.Popen[str] | None = None

    try:
        if args.port_forward:
            args.base_url = f"http://127.0.0.1:{args.local_port}/v1"
            print(
                f"正在创建端口转发：{args.namespace}/{args.service} "
                f"-> 127.0.0.1:{args.local_port}"
            )
            port_forward = start_port_forward(
                namespace=args.namespace,
                service=args.service,
                local_port=args.local_port,
                timeout=min(args.timeout, 60),
            )

        check_service(args.base_url, timeout=min(args.timeout, 10))
        return run_chat(args)

    except (ChatError, PortForwardError) as exc:
        print(f"启动客户端失败：{exc}", file=sys.stderr)
        return 2

    finally:
        if port_forward is not None:
            stop_port_forward(port_forward)


if __name__ == "__main__":
    raise SystemExit(main())
