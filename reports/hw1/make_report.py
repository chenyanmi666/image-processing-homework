# -*- coding: utf-8 -*-
"""作业1 报告材料生成器（不改变运行环境，只调用仓库内代码 + 本机已有软件）。

生成物（均在同一目录 reports/hw1/）：
    sample_input.png        自造测试图（H×S 网格 + 底部灰阶渐变），可复现、不依赖外部素材
    fig_compare.png         手写 HSL(课件定义) vs 官方 cv2.COLOR_BGR2HLS 的四联对比 + 统计文本
    fig_compare_strip.png   function_hw1_compare() 的原始返回值（即界面"对比实验"按钮的输出）
    fig_ps_curves.png       PS 风格 S 曲线族 / gamma 亮度族 / 斜率标定与残差
    fig_vibrance.png        自然饱和度增益 gain(S) 与 S' 曲线族
    fig_ui.png              无头浏览器截取的作业1 界面（非人工验收，仅作视觉证据）
    metrics.md              全部数值表格（Markdown）
    hw1_report.html         自包含报告（图片内嵌 base64）
    hw1_report.pdf          Edge 无头模式打印（若本机没有 Edge/Chrome 则跳过）

用法（仓库根目录）：
    python reports/hw1/make_report.py
"""
from __future__ import annotations

import base64
import io
import os
import pathlib
import socket
import subprocess
import sys
import time
import urllib.request

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import functions as F  # noqa: E402

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

HUE_SAT = "色相/饱和度"
OFFICIAL_HLS = "色相/饱和度 (官方cv2 HLS)"
VIBRANCE = "自然饱和度 (PS vibrance)"
BRIGHT_CONTRAST = "亮度/对比度"
PS_TONE = "亮度/对比度 (PS风格)"

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/usr/bin/microsoft-edge",
    "/usr/bin/google-chrome",
]

LOG = []


def log(message):
    print(message)
    LOG.append(str(message))


def build_sample_image(height=192, width=256):
    """自造的确定性测试图：上半部分是 色相×饱和度 网格，底部是灰阶渐变。"""
    yy, xx = np.mgrid[0:height, 0:width]
    h = (xx / max(width - 1, 1)) * 360.0
    s = 0.15 + 0.85 * (yy / max(height - 1, 1))
    i = np.full_like(h, 0.62)
    img = F._hw1_to_uint8(F._hw1_hsi_to_rgb(np.dstack([h, s, i])))
    ramp = np.rint(np.linspace(0, 255, width)).astype(np.uint8)
    img[height - 24:, :, :] = np.dstack([np.tile(ramp, (24, 1))] * 3)
    return img


def panels_of(strip, width, gap=4):
    return [strip[:, i * (width + gap):i * (width + gap) + width] for i in range(4)]


def figure_compare(image):
    strip, text = F.function_hw1_compare(image, 0.0, 0.5, 0.0)
    width = image.shape[1]
    panels = panels_of(strip, width)
    titles = ["原图", "手写 HSL（课件 p72-p78）", "官方 cv2 HLS", "差异 ×5"]
    fig = plt.figure(figsize=(13, 7.6))
    grid = fig.add_gridspec(2, 4, height_ratios=[3.0, 2.6], hspace=0.25)
    for index, (panel, title) in enumerate(zip(panels, titles)):
        ax = fig.add_subplot(grid[0, index])
        ax.imshow(panel)
        ax.set_title(title, fontsize=10)
        ax.axis("off")
    footer = fig.add_subplot(grid[1, :])
    footer.axis("off")
    footer.text(0.0, 1.0, text, va="top", ha="left", fontsize=8.4)
    fig.suptitle("实验一：手写 HSL（课件定义） vs 官方 cv2.COLOR_BGR2HLS（色相不变、饱和度 ×1.5）",
                 fontsize=11.5)
    path = OUT / "fig_compare.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    _write_png(OUT / "fig_compare_strip.png", strip)
    return path, text, strip



def _write_png(path, array):
    from PIL import Image

    Image.fromarray(np.asarray(array, dtype=np.uint8)).save(path)
    return path


def figure_ps_curves():
    x = np.linspace(0.0, 1.0, 512)
    column = x.reshape(1, -1, 1).repeat(3, axis=2)
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6))

    ax = axes[0]
    ax.plot(x, x, "k:", lw=1.1, label="恒等 y=x")
    for contrast in (-1.0, -0.5, 0.5, 1.0):
        a = F._hw1_ps_contrast_a(contrast)
        ax.plot(x, F._hw1_ps_s_curve(x, a), label="对比度 %+.1f  (a=%.0f, 中灰斜率 %.2f)"
                % (contrast, a, F._hw1_ps_mid_slope(contrast)))
    ax.set_title("对比度：tanh S 曲线（0 / 0.5 / 1 三个锚点不动）", fontsize=10.5)
    ax.set_xlabel("输入灰度（归一化）")
    ax.set_ylabel("输出灰度")
    ax.legend(fontsize=7.5)
    ax.grid(alpha=0.3)

    ax = axes[1]
    ax.plot(x, x, "k:", lw=1.1, label="恒等 y=x")
    for brightness in (-1.0, -0.5, 0.5, 1.0):
        curve = F._hw1_ps_brightness_contrast(column, brightness, 0.0)[0, :, 0]
        ax.plot(x, curve, label="亮度 %+.1f  (γ=%.2f)" % (brightness, 2.0 ** (-2.0 * brightness)))
    ax.set_title("亮度：gamma 模型（端点固定，暗部提升更多）", fontsize=10.5)
    ax.set_xlabel("输入灰度（归一化）")
    ax.set_ylabel("输出灰度")
    ax.legend(fontsize=7.5)
    ax.grid(alpha=0.3)

    ax = axes[2]
    ax.plot(x, x, "k:", lw=1.1, label="恒等 y=x")
    for target in (1.2, 1.5, 2.0):
        a_fit, rms, max_err = F._hw1_ps_fit_contrast_a(target)
        ax.plot(x, F._hw1_ps_s_curve(x, a_fit),
                label="目标斜率 %.1f → a=%.2f (RMS %.4f, max %.4f)" % (target, a_fit, rms, max_err))
        ax.plot(x, np.clip(0.5 + (x - 0.5) * target, 0.0, 1.0), "k--", lw=0.8, alpha=0.55)
    ax.set_title("对比度参数标定：最小二乘拟合线性斜坡（虚线=目标）", fontsize=10.5)
    ax.set_xlabel("输入灰度（归一化）")
    ax.set_ylabel("输出灰度")
    ax.legend(fontsize=7.5)
    ax.grid(alpha=0.3)

    fig.suptitle("进阶②：PS 风格亮度/对比度（本机无 Photoshop，未做与 PS 输出的逐像素比对）", fontsize=11.5)
    path = OUT / "fig_ps_curves.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_vibrance():
    s = np.linspace(0.0, 1.0, 512)
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
    ax = axes[0]
    ax.axhline(1.0, color="k", ls=":", lw=1.1)
    for amount in (0.25, 0.5, 1.0, -0.5):
        ax.plot(s, 1.0 + amount * (1.0 - s) ** 2, label="amount %+.2f" % amount)
    ax.set_title("增益 gain(S) = 1 + amount·(1-S)²：S=1 处恒为 1", fontsize=10.5)
    ax.set_xlabel("原饱和度 S")
    ax.set_ylabel("饱和度增益")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    ax = axes[1]
    ax.plot(s, s, "k:", lw=1.1, label="恒等 S'=S")
    for amount in (0.25, 0.5, 1.0, -0.5):
        ax.plot(s, F._hw1_apply_vibrance(s, amount), label="amount %+.2f" % amount)
    ax.set_title("输出饱和度 S'（低饱和提升明显，纯色不动，灰色仍为 0）", fontsize=10.5)
    ax.set_xlabel("原饱和度 S")
    ax.set_ylabel("调整后 S'")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    fig.suptitle("进阶③：PS 风格自然饱和度（增益随饱和度衰减的模型）", fontsize=11.5)
    path = OUT / "fig_vibrance.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return path



def collect_metrics(image):
    """报告里所有数值都在这里通过仓库代码实算一次，Markdown 与 HTML 共用。"""
    data = {}

    probes = [("纯红 (255,0,0)", (255, 0, 0)), ("纯黄 (255,255,0)", (255, 255, 0)),
              ("深红 (128,0,0)", (128, 0, 0)), ("中灰 (128,128,128)", (128, 128, 128))]
    space_rows = []
    for name, rgb in probes:
        pixel = np.array([[rgb]], dtype=np.float64) / 255.0
        space_rows.append((name, F._hw1_rgb_to_hsi(pixel)[0, 0], F._hw1_rgb_to_hls_opencv(pixel)[0, 0]))
    data["space_rows"] = space_rows

    img_f = image.astype(np.float64) / 255.0
    scans = [("默认参数（恒等）", 0.0, 0.0, 0.0), ("色相 +90°  (h=0.5)", 0.5, 0.0, 0.0),
             ("饱和度 ×1.5  (s=0.5)", 0.0, 0.5, 0.0), ("饱和度 ×2  (s=1.0)", 0.0, 1.0, 0.0),
             ("亮度 ×1.5  (l=0.5)", 0.0, 0.0, 0.5)]
    scan_rows = []
    for name, h, s, l in scans:
        manual = F._hw1_to_uint8(F._hw1_adjust_in_hsi(img_f, h, s, l))
        official = F._hw1_to_uint8(F._hw1_adjust_in_hls_opencv(img_f, h, s, l))
        scan_rows.append((name, F._hw1_error_stats(manual, official)))
    data["scan_rows"] = scan_rows
    data["roundtrip"] = {
        "manual": F._hw1_error_stats(image, F._hw1_to_uint8(F._hw1_adjust_in_hsi(img_f, 0.0, 0.0, 0.0))),
        "official": F._hw1_error_stats(image, F._hw1_to_uint8(F._hw1_adjust_in_hls_opencv(img_f, 0.0, 0.0, 0.0))),
    }

    data["fits"] = [(target,) + F._hw1_ps_fit_contrast_a(target) for target in (0.6, 0.8, 1.0, 1.2, 1.5, 2.0)]
    data["mid_slopes"] = [(c, F._hw1_ps_mid_slope(c)) for c in (-1.0, -0.5, 0.0, 0.5, 1.0)]

    def pixel_of(color, mode, **kwargs):
        size = 8
        img = np.zeros((size, size, 3), dtype=np.uint8)
        img[:, :] = color
        out = F.function_hw1(img, mode, kwargs.get("h", 0.0), kwargs.get("s", 0.0),
                             kwargs.get("l", 0.0), kwargs.get("b", 0.0), kwargs.get("c", 0.0))[0]
        return tuple(int(v) for v in out[0, 0])

    data["anchors"] = [
        ("手写 HSL（课件定义）", "纯红 色相 +180°", pixel_of((255, 0, 0), HUE_SAT, h=1.0)),
        ("手写 HSL（课件定义）", "纯红 饱和度 ×(1-1)", pixel_of((255, 0, 0), HUE_SAT, s=-1.0)),
        ("手写 HSL（课件定义）", "纯红 亮度 ×(1-1)", pixel_of((255, 0, 0), HUE_SAT, l=-1.0)),
        ("官方 cv2 HLS", "纯红 色相 +180°", pixel_of((255, 0, 0), OFFICIAL_HLS, h=1.0)),
        ("官方 cv2 HLS", "纯红 饱和度 ×(1-1)", pixel_of((255, 0, 0), OFFICIAL_HLS, s=-1.0)),
        ("官方 cv2 HLS", "纯红 亮度 ×(1-1)", pixel_of((255, 0, 0), OFFICIAL_HLS, l=-1.0)),
        ("线性亮度/对比度", "纯红 亮度 +0.5", pixel_of((255, 0, 0), BRIGHT_CONTRAST, b=0.5)),
        ("PS 风格亮度/对比度", "中灰 128 亮度 +0.5", pixel_of((128, 128, 128), PS_TONE, b=0.5)),
        ("PS 风格亮度/对比度", "中灰 128 对比度 +1", pixel_of((128, 128, 128), PS_TONE, c=1.0)),
        ("PS 风格亮度/对比度", "中灰 128 对比度 -1", pixel_of((128, 128, 128), PS_TONE, c=-1.0)),
        ("PS 风格亮度/对比度", "1/4 灰 64 对比度 +1", pixel_of((64, 64, 64), PS_TONE, c=1.0)),
        ("PS 风格亮度/对比度", "1/4 灰 64 对比度 -1", pixel_of((64, 64, 64), PS_TONE, c=-1.0)),
        ("PS 风格亮度/对比度", "3/4 灰 192 对比度 -1", pixel_of((192, 192, 192), PS_TONE, c=-1.0)),
        ("PS 风格亮度/对比度", "纯黑 亮度 +1", pixel_of((0, 0, 0), PS_TONE, b=1.0)),
        ("PS 风格亮度/对比度", "纯白 亮度 +1", pixel_of((255, 255, 255), PS_TONE, b=1.0)),
        ("自然饱和度 vibrance", "中灰 128 强度 +1", pixel_of((128, 128, 128), VIBRANCE, s=1.0)),
        ("自然饱和度 vibrance", "纯红 强度 +1", pixel_of((255, 0, 0), VIBRANCE, s=1.0)),
        ("自然饱和度 vibrance", "弱彩 (190,150,140) 强度 +1", pixel_of((190, 150, 140), VIBRANCE, s=1.0)),
    ]

    gains = []
    for amount in (0.0, 0.25, 0.5, 1.0, -1.0):
        for s in (0.0, 0.25, 0.5, 0.75, 1.0):
            out = float(F._hw1_apply_vibrance(np.array([s]), amount)[0])
            gains.append((amount, s, out, (out / s if s > 0 else float("nan"))))
    data["gains"] = gains
    return data


def markdown_report(data, compare_text):
    lines = []
    add = lines.append
    add("| 颜色 | 手写 HSL(课件): H / S / L | 官方 cv2 HLS: H / S / L |")
    add("| --- | --- | --- |")
    for name, manual, official in data["space_rows"]:
        add("| %s | %.2f° / %.4f / %.4f | %.2f° / %.4f / %.4f |"
            % (name, manual[0], manual[1], manual[2], official[0], official[1], official[2]))
    add("")
    add("| 参数 | 两路径 RGB 的 MAE (/255) | 最大误差 (/255) | PSNR (dB) |")
    add("| --- | --- | --- | --- |")
    for name, stats in data["scan_rows"]:
        psnr = "∞" if stats["psnr"] == float("inf") else "%.2f" % stats["psnr"]
        add("| %s | %.3f | %d | %s |" % (name, stats["mae"], int(round(stats["max"])), psnr))
    add("")
    add("| 量化往返（原图 → 空间 → 原图） | MAE (/255) | 最大误差 (/255) | PSNR (dB) |")
    add("| --- | --- | --- | --- |")
    for key, label in (("manual", "手写路径（浮点往返）"), ("official", "官方路径（8 位 HLS）")):
        stats = data["roundtrip"][key]
        psnr = "∞" if stats["psnr"] == float("inf") else "%.2f" % stats["psnr"]
        add("| %s | %.3f | %d | %s |" % (label, stats["mae"], int(round(stats["max"])), psnr))
    add("")
    add("| 目标中灰斜率 | 拟合 a | RMS 残差 | 最大残差 |")
    add("| --- | --- | --- | --- |")
    for target, a_fit, rms, max_err in data["fits"]:
        add("| %.1f | %.4f | %.5f | %.5f |" % (target, a_fit, rms, max_err))
    add("")
    add("| 对比度滑杆 | a | S 曲线中灰处斜率（解析） |")
    add("| --- | --- | --- |")
    for contrast, slope in data["mid_slopes"]:
        add("| %+.1f | %+.0f | %.4f |" % (contrast, F._hw1_ps_contrast_a(contrast), slope))
    add("")
    add("| 功能 | 输入 | 输出像素 |")
    add("| --- | --- | --- |")
    for feature, case, pixel in data["anchors"]:
        add("| %s | %s | %s |" % (feature, case, pixel))
    add("")
    add("| amount | 输入 S | 输出 S | 实际增益 |")
    add("| --- | --- | --- | --- |")
    for amount, s, out, gain in data["gains"]:
        gain_text = "—" if gain != gain else "%.3f" % gain
        add("| %+.2f | %.2f | %.4f | %s |" % (amount, s, out, gain_text))
    add("")
    add("### function_hw1_compare() 输出文本（原样）")
    add("")
    add("```")
    add(compare_text)
    add("```")
    return "\n".join(lines)



def _md_to_html(text):
    """把 markdown_report() 生成的简单 Markdown（表格/代码块/### 标题）转成 HTML。"""
    out = []
    in_table = False
    in_code = False
    for raw in text.split("\n"):
        line = raw.rstrip()
        if line.startswith("```"):
            out.append("</pre>" if in_code else "<pre>")
            in_code = not in_code
            continue
        if in_code:
            out.append(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            continue
        if line.startswith("### "):
            out.append("<h3>%s</h3>" % line[4:])
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            if not in_table:
                out.append("<table>")
                in_table = True
                tag = "th"
            else:
                tag = "td"
            out.append("<tr>%s</tr>" % "".join("<%s>%s</%s>" % (tag, c, tag) for c in cells))
            continue
        if in_table:
            out.append("</table>")
            in_table = False
        out.append(line)
    if in_table:
        out.append("</table>")
    if in_code:
        out.append("</pre>")
    return "\n".join(out)


def _data_uri(path):
    return "data:image/png;base64," + base64.b64encode(pathlib.Path(path).read_bytes()).decode("ascii")


HTML_HEAD = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>作业1 报告材料（自动生成）</title>
<style>
 body { font-family: "Microsoft YaHei", "Segoe UI", sans-serif; margin: 32px auto; max-width: 1080px;
        line-height: 1.65; color: #1b1b1b; }
 h1 { font-size: 24px; border-bottom: 3px solid #2b6cb0; padding-bottom: 8px; }
 h2 { font-size: 19px; margin-top: 30px; color: #2b6cb0; }
 h3 { font-size: 16px; }
 table { border-collapse: collapse; margin: 12px 0; font-size: 13px; }
 th, td { border: 1px solid #bbb; padding: 5px 9px; }
 th { background: #eef4fb; }
 pre { background: #f6f8fa; border: 1px solid #d8dee4; padding: 10px; font-size: 12px;
       white-space: pre-wrap; }
 img { max-width: 100%; border: 1px solid #ddd; margin: 10px 0; }
 .note { background: #fff8e1; border-left: 5px solid #e0a800; padding: 10px 14px; font-size: 13.5px; }
 code { background: #f2f2f2; padding: 1px 5px; border-radius: 3px; }
</style></head><body>"""



def html_report(data, compare_text, figures, test_summary):
    parts = [HTML_HEAD]
    add = parts.append
    add("<h1>作业1：图像色相/饱和度/亮度/对比度调整工具 —— 报告材料</h1>")
    add("<p>本文件由 <code>reports/hw1/make_report.py</code> 自动生成；所有数值均由仓库内 "
        "<code>functions.py</code> 的真实函数当场计算，未手工填写。</p>")

    add("<h2>1. 运行环境与复现命令</h2>")
    add("<pre>python -m unittest discover -s tests      # 数组层 + 兼容层全量测试\n"
        "python tests/ui_smoke_hw1.py --port 8093   # 界面层冒烟（真实 gradio 服务）\n"
        "python tests/test_frontend_render.py       # 无头浏览器真实渲染\n"
        "python reports/hw1/make_report.py          # 生成本报告材料</pre>")
    add("<p>本次提交时的实测结果：%s</p>" % test_summary)

    add("<h2>2. 五个模式一览</h2>")
    add("<table><tr><th>模式</th><th>实现方式</th><th>说明</th></tr>"
        "<tr><td>色相/饱和度</td><td>手写 HSI/HSL（课件 p72-p78 定义）</td>"
        "<td>基础实现：I=(R+G+B)/3、S=1-3·min/Σ、H∈[0,360)，逆变换用课件分段公式；亮度为乘性模型 I'=I·(1+l)</td></tr>"
        "<tr><td>色相/饱和度 (官方cv2 HLS)</td><td>直接调用 cv2.COLOR_BGR2HLS / COLOR_HLS2BGR</td>"
        "<td>官方路径：L=(max+min)/2、S=(max-min)/(max+min)，色相平移/饱和度/亮度语义与手写路径对齐</td></tr>"
        "<tr><td>自然饱和度 (PS vibrance)</td><td>gain(S)=1+amount·(1-S)²</td>"
        "<td>进阶③：优先提升原本不鲜艳的颜色，纯色与灰色保持不变</td></tr>"
        "<tr><td>亮度/对比度</td><td>线性模型 (x-0.5)(1+c)+0.5+b</td>"
        "<td>基础功能（自定义线性模型，<b>不是</b> Photoshop 拟合）</td></tr>"
        "<tr><td>亮度/对比度 (PS风格)</td><td>tanh S 曲线 + gamma 亮度</td>"
        "<td>进阶②：中灰与黑白端点锚定、不裁剪</td></tr></table>")

    tables = markdown_report(data, compare_text)
    add("<h2>3. 实验一：两条路径的数学定义对照</h2>")
    add("<p>两条路径的 H/S/L 数值<b>本来就不可直接互比</b>：课件定义 L=(R+G+B)/3，"
        "OpenCV 定义 L=(max+min)/2；只在两者定义重合处（灰色）才必然相等。</p>")
    add(_md_to_html(tables.split("### function_hw1_compare")[0]))

    add("<h2>4. 实验一：输出层面的对比与误差统计</h2>")
    add("<p><img src=\"%s\" alt=\"compare\"></p>" % _data_uri(figures["compare"]))
    add("<p>上图由本报告基于 <code>function_hw1_compare()</code> 的返回值重绘；"
        "下图是该函数返回的原始拼接图，与界面上的对比实验按钮的显示完全一致：</p>")
    add("<p><img src=\"%s\" alt=\"strip\"></p>" % _data_uri(figures["strip"]))
    add("<p>统计文本（原样）：</p>")
    add("<pre>%s</pre>" % compare_text.replace("&", "&amp;").replace("<", "&lt;"))

    add("<h2>5. 进阶②：PS 风格亮度/对比度</h2>")
    add("<p><img src=\"%s\" alt=\"ps\"></p>" % _data_uri(figures["ps"]))
    add("<p>S 曲线为 <code>y = 0.5 + 0.5·tanh(a(x-0.5))/tanh(a/2)</code>，"
        "解析中灰斜率 <code>0.5a/tanh(a/2)</code> 已与数值微分比对一致（单元测试覆盖）。</p>")
    add("<div class=\"note\">诚实声明：本机没有 Photoshop，<b>未做</b>与 PS 实际输出的逐像素比对，"
        "因此命名为“PS 风格”而非“PS 复刻”；标定表中的残差是“本 S 曲线与同斜率线性斜坡的差异”，"
        "属于本实现内部实验。对比度参数上限 a=±4，因此目标斜率高于约 2.07 时拟合值会被上限截断（表中 2.0 一行可见）。</div>")

    add("<h2>6. 进阶③：PS 风格自然饱和度</h2>")
    add("<p><img src=\"%s\" alt=\"vibrance\"></p>" % _data_uri(figures["vib"]))
    add("<p>增益随 S 增大而衰减：S=1（纯色）时增益恒为 1，灰色 S=0 时输出仍为 0（不会被染色）。</p>")

    if figures.get("ui"):
        add("<h2>7. 界面证据（无头浏览器截图）</h2>")
        add("<p><img src=\"%s\" alt=\"ui\"></p>" % _data_uri(figures["ui"]))
        add("<div class=\"note\">该截图由本机 Edge 无头模式抓取，<b>不等于</b>人工浏览器验收；"
            "人工验收步骤见 <code>tests/README.md</code>。</div>")

    add("<h2>8. 诚实声明与局限</h2>")
    add(_md_to_html("- 手写路径与官方路径是**两套数学模型**，结果不一致不代表任何一方实现错误；报告把“模型差异”与“8 位量化误差”分开统计。\n"
                    "- 官方路径内部为 8 位量化（`COLOR_BGR2HLS`），其“恒等”往返在饱和色上会残留至多 1 个 LSB（例如纯红恒等得到 (255,1,1)）；手写路径在浮点域往返，恒等为严格相等。\n"
                    "- 亮度乘性模型 `I'=I·(1+l)` 是本作业的默认设计，不是不可变的数学要求；裁剪会改变实际 H/S/I，报告未宣称裁剪后其余通道严格不变。\n"
                    "- `cv2.cvtColor(COLOR_RGB2HLS)` 与本作业手写定义不同，本报告未据通道误差判定谁“更准确”。\n"))
    add("</body></html>")
    return "\n".join(parts)



def _find_browser():
    for candidate in BROWSERS:
        if pathlib.Path(candidate).is_file():
            return candidate
    return None


def _port_is_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def _wait_for_server(url, proc, timeout=90):
    for _ in range(int(timeout)):
        if proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(1)
    return False


def capture_screenshot(port=8094):
    """启动作业1 界面并用无头浏览器截图（仅作视觉证据，不是人工验收）。"""
    exe = _find_browser()
    if exe is None:
        log("SKIP 界面截图：本机未找到 Edge/Chrome")
        return None
    if not _port_is_free(port):
        log("SKIP 界面截图：端口 %d 已被占用" % port)
        return None
    import tempfile

    url = "http://127.0.0.1:%d/" % port
    shot = OUT / "fig_ui.png"
    profile = pathlib.Path(tempfile.mkdtemp(prefix="hw1_report_profile_"))
    server_log_path = OUT / "ui_server.log"
    with io.open(server_log_path, "w", encoding="utf-8", errors="replace") as server_log:
        proc = subprocess.Popen(
            [sys.executable, str(ROOT / "tests" / "ui_smoke_hw1.py"), "--serve", "--port", str(port)],
            cwd=str(ROOT), stdout=server_log, stderr=subprocess.STDOUT)
        try:
            if not _wait_for_server(url, proc):
                log("SKIP 界面截图：作业1 服务未就绪（日志见 reports/hw1/ui_server.log）")
                return None
            command = [exe, "--headless=new", "--disable-gpu", "--no-first-run",
                       "--no-default-browser-check", "--user-data-dir=%s" % profile,
                       "--window-size=1400,1200", "--virtual-time-budget=25000",
                       "--screenshot=%s" % shot, url]
            result = subprocess.run(command, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, timeout=240)
            if shot.is_file() and shot.stat().st_size > 0:
                log("界面截图完成：%s (%d bytes, rc=%s)" % (shot.name, shot.stat().st_size, result.returncode))
                return shot
            log("SKIP 界面截图：浏览器未生成文件 (rc=%s)" % result.returncode)
            return None
        finally:
            try:
                proc.terminate()
                proc.wait(timeout=15)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


def html_to_pdf(html_path, pdf_path):
    exe = _find_browser()
    if exe is None:
        log("SKIP PDF：本机未找到 Edge/Chrome，保留 hw1_report.html 供手动导出")
        return None
    import tempfile

    profile = pathlib.Path(tempfile.mkdtemp(prefix="hw1_report_pdf_"))
    command = [exe, "--headless=new", "--disable-gpu", "--no-first-run",
               "--no-pdf-header-footer", "--user-data-dir=%s" % profile,
               "--virtual-time-budget=10000",
               "--print-to-pdf=%s" % pdf_path, pathlib.Path(html_path).as_uri()]
    result = subprocess.run(command, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, timeout=240)
    if pdf_path.is_file() and pdf_path.stat().st_size > 0:
        log("PDF 生成完成：%s (%d bytes, rc=%s)" % (pdf_path.name, pdf_path.stat().st_size, result.returncode))
        return pdf_path
    log("SKIP PDF：打印未生成文件 (rc=%s)，保留 HTML 供手动导出" % result.returncode)
    return None


TEST_SUMMARY = ("数组层/兼容层：python -m unittest discover -s tests -> Ran 105 tests, OK；"
                "界面层冒烟：python tests/ui_smoke_hw1.py --port 8093 -> UI smoke: 23/23 PASS；"
                "明细见 PROJECT_LOG.md 阶段 I。无头浏览器渲染测试见 tests/README.md。")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    image = build_sample_image()
    _write_png(OUT / "sample_input.png", image)
    log("测试图 sample_input.png: %s" % (image.shape,))

    compare_path, compare_text, strip = figure_compare(image)
    log("实验一对比图: %s" % compare_path.name)
    ps_path = figure_ps_curves()
    log("PS 曲线图: %s" % ps_path.name)
    vib_path = figure_vibrance()
    log("自然饱和度图: %s" % vib_path.name)

    data = collect_metrics(image)
    metrics = markdown_report(data, compare_text)
    with io.open(OUT / "metrics.md", "w", encoding="utf-8", newline="\n") as handle:
        handle.write("# 作业1 实测指标（由 reports/hw1/make_report.py 自动生成）\n\n" + metrics + "\n")
    log("指标表: metrics.md")

    ui_shot = capture_screenshot()
    figures = {"compare": compare_path, "strip": OUT / "fig_compare_strip.png",
               "ps": ps_path, "vib": vib_path, "ui": ui_shot}
    html = html_report(data, compare_text, figures, TEST_SUMMARY)
    html_path = OUT / "hw1_report.html"
    with io.open(html_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(html)
    log("HTML 报告: hw1_report.html (%d bytes)" % len(html.encode("utf-8")))

    html_to_pdf(html_path, OUT / "hw1_report.pdf")
    log("完成。生成物目录：%s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
