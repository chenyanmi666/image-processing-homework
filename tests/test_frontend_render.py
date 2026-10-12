"""前端真实渲染测试（headless 浏览器）。

背景：`GET /` 返回 200、`/config` 内容正常，**都不等于浏览器渲染成功**。
阶段 H 的实例：`gradio_compat.ImageEditor` 的子类名让 `/config` 出现
`type: "imageeditor"`，而 gradio 3.x 前端 `component_map` 里只有 `image`，
于是前端渲染中断、整页停在 "Loading..." —— 服务端日志、HTTP 状态全部正常。

本脚本用本机 Edge/Chrome 的 **headless 模式真正执行页面 JS**，抓“渲染后的 DOM”，断言：
  1. 5 个作业页签文案真实出现在渲染结果里（剥离内嵌 script/config 后仍存在）；
  2. 渲染结果中不再出现 Gradio 的 "Loading..." 遮罩，且容器不是空的；
  3. 组件节点已生成（`data-testid="image"`、`component-N`、"输入图像"等）；
  4. `/config` 中所有带 `tool` 的组件 `type` 均为 `image`
     （回归防护：禁止再回退成前端不认识的名字）。

用法（仓库根目录）：
    python tests/test_frontend_render.py                 # 默认端口 8091（避开手动服务 8088）
    python tests/test_frontend_render.py --port 8092

若本机没有 Edge/Chrome，脚本输出 SKIP 并提示改由人工在浏览器验收（不算失败）。
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
NATIVE_PORT = 8088
PORT = 8091
URL = "http://127.0.0.1:%d/" % PORT
BOOTSTRAP = (
    "import sys, gradio as gr, web_demo;"
    " _orig = gr.Blocks.launch;"
    " gr.Blocks.launch = lambda self, *a, **k: _orig(self, *a, **dict(k, server_port=int(sys.argv[1])));"
    " web_demo.main()"
)
SERVER_LOG = pathlib.Path(tempfile.gettempdir()) / "test_frontend_render.log"
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/usr/bin/microsoft-edge",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]
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


def find_browser():
    for path in BROWSERS:
        if pathlib.Path(path).is_file():
            return path
    return None


def dump_dom(exe, url, workdir, timeout=150):
    """在无头浏览器中打开 url 并抓取**执行 JS 之后**的 DOM。"""
    profile = pathlib.Path(workdir) / "profile"
    dom_path = pathlib.Path(workdir) / "dom.html"
    command = [exe, "--headless=new", "--disable-gpu", "--no-first-run",
               "--no-default-browser-check", "--disable-extensions",
               "--user-data-dir=%s" % profile,
               "--virtual-time-budget=20000", "--dump-dom", url]
    with open(dom_path, "wb") as out:
        proc = subprocess.run(command, stdout=out, stderr=subprocess.DEVNULL, timeout=timeout)
    html = dom_path.read_bytes().decode("utf-8", "ignore")
    return html, "rc=%s bytes=%d" % (proc.returncode, len(html))


def strip_scripts(html):
    """剥离 <script>/<style> 与标签，只留下真正渲染出来的可见文本。

    必须剥离：index.html 内嵌的 window.gradio_config 含全部页签文案，
    不剥离就无法区分“配置里有”与“渲染出来了”。
    """
    cleaned = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", cleaned)
    return re.sub(r"\s+", " ", text).strip()


def main():
    global PORT, URL
    parser = argparse.ArgumentParser(description="前端真实渲染测试（无头浏览器）")
    parser.add_argument("--port", type=int, default=PORT,
                        help="服务端口；默认 %d，避免与手动服务 8088 冲突" % PORT)
    args = parser.parse_args()
    PORT = args.port
    URL = "http://127.0.0.1:%d/" % PORT
    if not _port_is_free():
        print("端口 %d 已被占用：请先关闭占用该端口的服务，或用 --port 指定其他端口。" % PORT)
        return 2

    exe = find_browser()
    if exe is None:
        print("SKIP：本机未找到 Edge/Chrome，无法在无头浏览器中验证真实渲染。")
        print("      请人工执行 `python web_demo.py` 并打开 %s 验收五个页签。" % URL)
        return 0
    print("浏览器：%s" % exe)

    checks = []

    def check(name, passed, detail=""):
        checks.append((name, passed))
        print("[%s] %s%s" % ("PASS" if passed else "FAIL", name,
                             (" -> " + detail) if detail else ""))

    workdir = tempfile.mkdtemp(prefix="frontend_render_")
    with open(SERVER_LOG, "w", encoding="utf-8", errors="replace") as log:
        if PORT == NATIVE_PORT:
            command = [sys.executable, str(ROOT / "web_demo.py")]
            print("启动方式：python web_demo.py（原生，端口 %d）" % PORT)
        else:
            command = [sys.executable, "-c", BOOTSTRAP, str(PORT)]
            print("启动方式：python -c <bootstrap>（调用真实 web_demo.main()，端口 %d）" % PORT)
        proc = subprocess.Popen(command, cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT)
        try:
            ready = False
            for _ in range(120):
                if proc.poll() is not None:
                    print("web_demo.py 提前退出 rc=%s（日志：%s）" % (proc.returncode, SERVER_LOG))
                    break
                try:
                    _get("", timeout=3)
                    ready = True
                    break
                except Exception:
                    time.sleep(1)
            check("服务可访问", ready)

            if ready:
                # 回归防护：编辑器组件在前端必须是 gradio 认识的名字
                try:
                    _, cbody = _get("config", timeout=10)
                    config = json.loads(cbody.decode("utf-8"))
                    editors = [c.get("type") for c in config.get("components", [])
                               if (c.get("props") or {}).get("tool")]
                    check("/config 编辑器组件 type 全为 image",
                          bool(editors) and set(editors) == {"image"},
                          "types=%s" % sorted(set(editors)))
                except Exception as exc:
                    check("/config 编辑器组件 type 全为 image", False,
                          "%s: %s" % (type(exc).__name__, exc))

                # 真正的渲染验证：必须执行页面 JS 之后再看 DOM
                try:
                    html, note = dump_dom(exe, URL, workdir)
                    if len(html) < 1000:  # 无头浏览器偶发空输出，重试一次
                        html, note = dump_dom(exe, URL, workdir)
                    text = strip_scripts(html)
                    check("抓到渲染后的 DOM", len(html) >= 1000, note)
                    check("剥离内嵌 config 后仍见页面标题", "图像处理网页演示工具" in text)
                    for tab in TABS:
                        check("渲染结果含页签：%s" % tab, tab in text)
                    check("不再停留 Loading 遮罩", "Loading..." not in text,
                          "可见文本长度=%d" % len(text))
                    check("作业1 页签内容已渲染",
                          all(word in text for word in
                              ("输入图像", "输出图像", "模式", "色相", "饱和度", "明度")))
                    check("图像组件节点已生成", 'data-testid="image"' in html)
                    check("渲染节点 component-N 已生成", "component-" in html)
                except Exception as exc:
                    check("前端真实渲染", False, "%s: %s" % (type(exc).__name__, exc))
        finally:
            try:
                proc.terminate()
                proc.wait(timeout=20)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            shutil.rmtree(workdir, ignore_errors=True)

    failed = [name for name, ok in checks if not ok]
    print("前端渲染测试：%d/%d PASS" % (len(checks) - len(failed), len(checks)))
    if failed:
        print("失败项：%s" % ", ".join(failed))
        print("服务端日志：%s" % SERVER_LOG)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
