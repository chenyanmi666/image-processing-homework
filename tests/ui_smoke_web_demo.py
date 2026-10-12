"""完整程序（`web_demo.py`，5 个作业页签）的启动冒烟测试。

用法（仓库根目录）：
    python tests/ui_smoke_web_demo.py                 # 端口 8088，与手动运行完全一致
    python tests/ui_smoke_web_demo.py --port 8090     # 8088 被占用时换个端口

做四件事：
1. 以子进程方式执行 `python web_demo.py`（与用户手动运行完全一致）；
2. 轮询 `GET /`，要求 HTTP 200；
3. 读取 `GET /config`，断言 5 个作业页签都存在，且作业3 的编辑器
   已被 gradio_compat 换成 3.x 可用的 `sketch` 工具；
4. 关闭服务并打印服务端日志位置。

注意：`web_demo.py` 固定使用 8088 端口；请先关闭手动启动的同一服务。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
NATIVE_PORT = 8088
PORT = NATIVE_PORT
URL = "http://127.0.0.1:%d/" % PORT
BOOTSTRAP = (
    "import sys, gradio as gr, web_demo;"
    " _orig = gr.Blocks.launch;"
    " gr.Blocks.launch = lambda self, *a, **k: _orig(self, *a, **dict(k, server_port=int(sys.argv[1])));"
    " web_demo.main()"
)
SERVER_LOG = pathlib.Path(tempfile.gettempdir()) / "ui_smoke_web_demo.log"
TABS = [
    "作业1: 图像色相/饱和度/亮度/对比度调整工具",
    "作业2: 基于GAN的图像生成编辑工具",
    "作业3: 替换屏幕内容工具",
    "作业4: 图像去噪工具",
    "作业5: 图像提亮工具",
]


def _port_is_free():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", PORT)) != 0


def _get(path, timeout=5):
    with urllib.request.urlopen(URL + path.lstrip("/"), timeout=timeout) as response:
        return response.status, response.read()


def main():
    parser = argparse.ArgumentParser(description="完整 web_demo.py 启动冒烟测试")
    parser.add_argument("--port", type=int, default=NATIVE_PORT,
                        help="服务端口；非 %d 时用 -c 包装脚本启动（仅替换端口）" % NATIVE_PORT)
    args = parser.parse_args()
    global PORT, URL
    PORT = args.port
    URL = "http://127.0.0.1:%d/" % PORT
    if not _port_is_free():
        print("端口 %d 已被占用：请先关闭占用该端口的服务，或用 --port 指定其他端口。" % PORT)
        return 2

    checks = []

    def check(name, passed, detail=""):
        checks.append((name, passed))
        print("[%s] %s%s" % ("PASS" if passed else "FAIL", name, (" -> " + detail) if detail else ""))

    with open(SERVER_LOG, "w", encoding="utf-8", errors="replace") as log:
        if PORT == NATIVE_PORT:
            command = [sys.executable, str(ROOT / "web_demo.py")]
            print("启动方式：python web_demo.py（原生，端口 %d）" % PORT)
        else:
            command = [sys.executable, "-c", BOOTSTRAP, str(PORT)]
            print("启动方式：python -c <bootstrap>（调用真实 web_demo.main()，端口 %d）" % PORT)
        proc = subprocess.Popen(command, cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT)
        try:
            status, body = None, b""
            for _ in range(120):
                if proc.poll() is not None:
                    print("web_demo.py 提前退出 rc=%s（日志：%s）" % (proc.returncode, SERVER_LOG))
                    break
                try:
                    status, body = _get("", timeout=3)
                    break
                except Exception:
                    time.sleep(1)

            check("web_demo.py 进程存活", proc.poll() is None)
            if status is not None:
                check("GET / 返回 200", status == 200, "status=%s" % status)
                html = body.decode("utf-8", "ignore")
                check("页面含 5 个作业文案", all(("作业%s" % n) in html for n in "12345"),
                      "%d bytes" % len(body))

                try:
                    cstatus, cbody = _get("config", timeout=10)
                    config = json.loads(cbody.decode("utf-8"))
                    labels = [(c.get("props") or {}).get("label") for c in config.get("components", [])]
                    for tab in TABS:
                        check("页签存在：%s" % tab, tab in labels)
                    tools = [(c.get("props") or {}).get("tool") for c in config.get("components", [])
                             if (c.get("props") or {}).get("tool")]
                    check("作业3 编辑器退化为 sketch 工具", tools.count("sketch") >= 1,
                          "tools=%s" % sorted(set(tools)))
                    check("/config 状态 200", cstatus == 200)
                except Exception as exc:
                    check("读取 /config", False, "%s: %s" % (type(exc).__name__, exc))
        finally:
            try:
                proc.terminate()
                proc.wait(timeout=20)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    failed = [name for name, ok in checks if not ok]
    print("UI smoke (full app): %d/%d PASS" % (len(checks) - len(failed), len(checks)))
    if failed:
        print("失败项：%s" % ", ".join(failed))
        print("服务端日志：%s" % SERVER_LOG)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
