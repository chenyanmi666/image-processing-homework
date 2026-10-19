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
OFFICIAL_HLS = "色相/饱和度 (官方cv2 HLS)"
VIBRANCE = "自然饱和度 (PS vibrance)"
BRIGHT_CONTRAST = "亮度/对比度"
PS_TONE = "亮度/对比度 (PS风格)"
SERVER_LOG = pathlib.Path(tempfile.gettempdir()) / "ui_smoke_hw1_server.log"


def build_demo():
    import gradio as gr
    from UI import create_demo_hw1
    from functions import function_hw1, function_hw1_compare

    with gr.Blocks() as demo:
        # 与 web_demo.py 相同的接线方式：第二个参数启用"对比实验"按钮
        create_demo_hw1(function_hw1, function_hw1_compare)
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


def _predict(url, png, mode, h, s, l, b, c, fn_index=0):
    payload = {"data": [_data_url(png), mode, h, s, l, b, c],
               "fn_index": fn_index, "session_hash": "ui-smoke"}
    req = urllib.request.Request(url + "run/predict",
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))["data"]


def _predict_compare(url, png, h, s, l, fn_index):
    payload = {"data": [_data_url(png), h, s, l],
               "fn_index": fn_index, "session_hash": "ui-smoke"}
    req = urllib.request.Request(url + "run/predict",
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))["data"]


def _fetch_config(url):
    with urllib.request.urlopen(url + "config", timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _find_compare_fn_index(config):
    """对比实验事件：4 个输入（图 + 色相/饱和度/明度），2 个输出（对比图 + 统计文本）。"""
    for index, dep in enumerate(config.get("dependencies", [])):
        if len(dep.get("inputs", [])) == 4 and len(dep.get("outputs", [])) == 2:
            return index
    return None


def _mode_choices(config):
    for comp in config.get("components", []):
        if comp.get("type") == "radio" and "模式" in str(comp.get("props", {}).get("label", "")):
            return list(comp["props"].get("choices", []))
    return []


def _port_is_free(port):
    """端口被占用时必须直接报错。

    否则冒烟脚本会连到**别人的/旧的**服务上，出现
    "旧界面也能通过部分断言"的假通过（阶段 I 实际踩过：8088 上是旧实例，
    模式列表只有 2 项、对比事件不存在，却仍打印了 5 个 PASS）。
    """
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def run_smoke(port):
    import numpy as np
    from PIL import Image

    if not _port_is_free(port):
        print("端口 %d 已被占用：请先关闭占用该端口的服务，或用 --port 指定其他端口。" % port)
        return 2

    url = "http://127.0.0.1:%d/" % port
    buf = io.BytesIO()
    arr = np.zeros((32, 32, 3), dtype=np.uint8)
    arr[:, :, 0] = 255
    Image.fromarray(arr).save(buf, format="PNG")
    png = buf.getvalue()

    def encode(pixel):
        b = io.BytesIO()
        Image.fromarray(np.full((32, 32, 3), 0, dtype=np.uint8) + np.array(pixel, np.uint8)).save(b, format="PNG")
        return b.getvalue()

    gray_png = encode((128, 128, 128))
    low_png = encode((190, 150, 140))

    checks = []

    def check(name, got, expected):
        ok = list(got) == list(expected)
        checks.append((name, ok, got, expected))
        print("[%s] %s: got=%s expect=%s" % ("PASS" if ok else "FAIL", name, got, expected))

    def check_between(name, got, lo, hi):
        ok = lo <= float(got) <= hi
        checks.append((name, ok, got, "%s..%s" % (lo, hi)))
        print("[%s] %s: got=%s expect=%s..%s" % ("PASS" if ok else "FAIL", name, got, lo, hi))

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

                # ---- 本次扩展：官方 cv2 HLS 模式、PS 风格、自然饱和度、对比实验 ----
                config = _fetch_config(url)
                choices = _mode_choices(config)
                print("mode choices:", choices)
                checks.append(("mode dropdown", list(choices) == [HUE_SAT, OFFICIAL_HLS, VIBRANCE,
                                                                  BRIGHT_CONTRAST, PS_TONE],
                               len(choices), 5))
                compare_index = _find_compare_fn_index(config)
                print("compare fn_index:", compare_index)
                checks.append(("compare event registered", compare_index is not None, compare_index, "is not None"))

                res = _predict(url, png, OFFICIAL_HLS, 0.0, 0.0, 0.0, 0.0, 0.0)
                official_identity = _decode(res[0])[0, 0].astype(int)
                # cv2 的 HLS 是 8 位量化：纯红 L=(255+0)/2=127.5 -> 128 (=0.50196)，
                # 逆变换 min = L*(1-S) = 1/255，所以真恒等会残留 1 个 LSB（(255,1,1)），
                # 这是官方库的量化误差，不是实现错误（手写路径为浮点往返，恒等为严格相等）。
                check_between("official HLS identity R", official_identity[0], 253, 255)
                check_between("official HLS identity G", official_identity[1], 0, 2)
                check_between("official HLS identity G-B 对称", abs(int(official_identity[1]) - int(official_identity[2])), 0, 1)
                check("official HLS hue +180", _decode(_predict(url, png, OFFICIAL_HLS, 1.0, 0, 0, 0, 0)[0])[0, 0],
                      (1, 255, 255))
                check("official HLS saturation -1",
                      _decode(_predict(url, png, OFFICIAL_HLS, 0, -1.0, 0, 0, 0)[0])[0, 0], (128, 128, 128))

                gray_out = _decode(_predict(url, gray_png, PS_TONE, 0, 0, 0, 0.5, 0)[0])[0, 0]
                check_between("PS tone gray brightness +0.5", gray_out[0], 175, 185)
                ps_ref = _decode(_predict(url, gray_png, PS_TONE, 0, 0, 0, 0.0, 0)[0])[0, 0]
                check("PS tone identity", ps_ref, (128, 128, 128))
                dark_out = _decode(_predict(url, gray_png, PS_TONE, 0, 0, 0, 0.0, 1.0)[0])[0, 0]
                check_between("PS tone contrast +1 darkens mid gray", dark_out[0], 118, 132)

                vibe0 = _decode(_predict(url, low_png, VIBRANCE, 0, 0.0, 0, 0, 0)[0])[0, 0].astype(int)
                vibe1 = _decode(_predict(url, low_png, VIBRANCE, 0, 1.0, 0, 0, 0)[0])[0, 0].astype(int)
                check("vibrance amount 0 identity", vibe0, (190, 150, 140))
                check_between("vibrance spread grows",
                              int(vibe1.max() - vibe1.min()) - int(vibe0.max() - vibe0.min()), 1, 255)
                check("vibrance keeps gray", _decode(_predict(url, gray_png, VIBRANCE, 0, 1.0, 0, 0, 0)[0])[0, 0],
                      (128, 128, 128))

                if compare_index is not None:
                    res = _predict_compare(url, png, 0.0, 0.5, 0.0, compare_index)
                    figure = _decode(res[0])
                    print("compare figure shape:", figure.shape)
                    checks.append(("compare figure is 4 panels", figure.shape == (32, 4 * 32 + 3 * 4, 3),
                                   figure.shape, (32, 4 * 32 + 3 * 4, 3)))
                    report = res[1] if isinstance(res[1], str) else json.dumps(res[1], ensure_ascii=False)
                    for token in ("MAE", "PSNR", "cv2", "量化"):
                        checks.append(("compare report contains %s" % token, token in report, token in report, True))
                        print("[%s] compare report contains %r" % ("PASS" if token in report else "FAIL", token))
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
