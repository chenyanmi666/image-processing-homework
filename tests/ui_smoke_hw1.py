"""作业1（function_hw1）的 Gradio 界面层冒烟测试。

用法（在仓库根目录执行）：
    python tests/ui_smoke_hw1.py                 # 自动冒烟：启动 -> 请求 -> 断言 -> 关闭
    python tests/ui_smoke_hw1.py --serve         # 只启动服务，供人工在浏览器中测试
    python tests/ui_smoke_hw1.py --port 8089     # 换端口

说明：本脚本只注册作业1 的界面。原因是本机 gradio 3.36.1 没有 gr.ImageEditor，
而原模板 UI.py 的 create_demo_hw3 使用了该组件（gradio 4.x 才有），
导致完整 web_demo.py 在本机启动即 AttributeError。
本脚本未修改 UI.py / web_demo.py，结论见 PROJECT_LOG.md 阶段 F。
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HUE_SAT = "色相/饱和度"
BRIGHT_CONTRAST = "亮度/对比度"
SERVER_LOG = pathlib.Path(tempfile.gettempdir()) / "ui_smoke_hw1_server.log"


def build_demo():
    import gradio as gr
    from UI import create_demo_hw1
    from functions import function_hw1

    with gr.Blocks() as demo:
        create_demo_hw1(function_hw1)
    return demo


def serve(port):
    print("serving http://127.0.0.1:%d/  (Ctrl+C 结束)" % port)
    build_demo().launch(server_port=port)


def _data_url(png_bytes):
    return "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")


def _decode(item):
    import numpy as np
    from PIL import Image

    raw = item.get("data") or item.get("name") or item.get("url") if isinstance(item, dict) else item
    if isinstance(raw, str) and raw.startswith("data:"):
        raw = base64.b64decode(raw.split(",", 1)[1])
    if isinstance(raw, (bytes, bytearray)):
        return np.array(Image.open(io.BytesIO(raw)).convert("RGB"))
    if isinstance(raw, str) and os.path.exists(raw):
        return np.array(Image.open(raw).convert("RGB"))
    raise RuntimeError("无法解析返回的图像：%r" % (type(item),))


def _predict(url, png, mode, h, s, l, b, c):
    payload = {"data": [_data_url(png), mode, h, s, l, b, c],
               "fn_index": 0, "session_hash": "ui-smoke"}
    req = urllib.request.Request(url + "run/predict",
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))["data"]


def run_smoke(port):
    import numpy as np
    from PIL import Image

    url = "http://127.0.0.1:%d/" % port
    buf = io.BytesIO()
    arr = np.zeros((32, 32, 3), dtype=np.uint8)
    arr[:, :, 0] = 255
    Image.fromarray(arr).save(buf, format="PNG")
    png = buf.getvalue()

    checks = []

    def check(name, got, expected):
        ok = list(got) == list(expected)
        checks.append((name, ok, got, expected))
        print("[%s] %s: got=%s expect=%s" % ("PASS" if ok else "FAIL", name, got, expected))

    with io.open(SERVER_LOG, "w", encoding="utf-8", errors="replace") as fh:
        proc = subprocess.Popen(
            [sys.executable, str(pathlib.Path(__file__).resolve()), "--serve", "--port", str(port)],
            cwd=str(ROOT), stdout=fh, stderr=subprocess.STDOUT)
        try:
            ready = False
            for _ in range(90):
                if proc.poll() is not None:
                    print("服务提前退出 rc=%s，日志见 %s" % (proc.returncode, SERVER_LOG))
                    break
                try:
                    with urllib.request.urlopen(url, timeout=3) as resp:
                        body = resp.read().decode("utf-8", "ignore")
                        print("HTTP %s, %d bytes" % (resp.status, len(body)))
                        for key in ("作业一", "色相/饱和度", "亮度/对比度"):
                            print("  page contains %r: %s" % (key, key in body))
                        ready = resp.status == 200
                        break
                except Exception:
                    time.sleep(1)

            if ready:
                print("input pixel:", arr[0, 0].tolist())
                res = _predict(url, png, HUE_SAT, 0.0, 0.0, 0.0, 0.0, 0.0)
                print("identity outputs:", len(res))
                check("identity", _decode(res[0])[0, 0], (255, 0, 0))
                check("brightness +0.5", _decode(_predict(url, png, BRIGHT_CONTRAST, 0, 0, 0, 0.5, 0)[0])[0, 0], (255, 128, 128))
                check("hue +180", _decode(_predict(url, png, HUE_SAT, 1.0, 0, 0, 0, 0)[0])[0, 0], (0, 128, 128))
                res = _predict(url, png, HUE_SAT, 0.0, -1.0, 0.0, 0.0, 0.0)
                check("saturation -1", _decode(res[0])[0, 0], (85, 85, 85))
                check("R channel view", _decode(res[1])[0, 0], (85, 85, 85))
        finally:
            try:
                proc.terminate()
                proc.wait(timeout=15)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    if not checks:
        print("界面冒烟未执行（服务未就绪）")
        return 1
    failed = [c for c in checks if not c[1]]
    print("UI smoke: %d/%d PASS" % (len(checks) - len(failed), len(checks)))
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description="作业1 界面层冒烟 / 手动测试入口")
    parser.add_argument("--serve", action="store_true", help="只启动服务供人工测试")
    parser.add_argument("--port", type=int, default=8088)
    args = parser.parse_args()
    if args.serve:
        serve(args.port)
        return 0
    return run_smoke(args.port)


if __name__ == "__main__":
    sys.exit(main())
