#-*-coding:GBK -*-
import numpy as np
import gradio as gr

# 兼容旧版 Gradio 的 Error 参数。
_gr_module = gr


class _GradioCompat:
    @staticmethod
    def Error(message="Error raised.", duration=None, **kwargs):
        try:
            return _gr_module.Error(message, duration=duration, **kwargs)
        except TypeError:
            return _gr_module.Error(message)

    def __getattr__(self, name):
        return getattr(_gr_module, name)


gr = _GradioCompat()


def _hw1_rgb_to_hsi(rgb):
    """RGB [0,1] 转课件 HSI；H 为角度，S、I 为 [0,1]。"""
    r = rgb[:, :, 0]
    g = rgb[:, :, 1]
    b = rgb[:, :, 2]

    i = (r + g + b) / 3.0

    total = r + g + b
    min_rgb = np.minimum(np.minimum(r, g), b)
    safe_total = np.where(total > 0.0, total, 1.0)
    s = np.where(total > 0.0, 1.0 - 3.0 * min_rgb / safe_total, 0.0)
    s = np.clip(s, 0.0, 1.0)

    num = 0.5 * ((r - g) + (r - b))
    den = np.sqrt((r - g) ** 2 + (r - b) * (g - b))
    cos_theta = np.where(den > 1e-12, num / np.where(den > 1e-12, den, 1.0), 0.0)
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    theta = np.degrees(np.arccos(cos_theta))

    h = np.where(b <= g, theta, 360.0 - theta)
    h = np.where(den > 1e-12, h, 0.0)
    h = np.mod(h, 360.0)

    return np.dstack([h, s, i])


def _hw1_hsi_to_rgb(hsi):
    """按三个 120 度扇区将 HSI 转为 RGB，超出色域的结果裁剪。"""
    h = np.mod(np.asarray(hsi[:, :, 0], dtype=np.float64), 360.0)
    s = np.clip(np.asarray(hsi[:, :, 1], dtype=np.float64), 0.0, 1.0)
    i = np.clip(np.asarray(hsi[:, :, 2], dtype=np.float64), 0.0, 1.0)

    r = np.empty_like(i)
    g = np.empty_like(i)
    b = np.empty_like(i)

    seg1 = (h >= 0.0) & (h < 120.0)
    seg2 = (h >= 120.0) & (h < 240.0)
    seg3 = (h >= 240.0) & (h < 360.0)

    if seg1.any():
        hh = h[seg1]
        ss = s[seg1]
        ii = i[seg1]
        bb = ii * (1.0 - ss)
        rr = ii * (1.0 + ss * np.cos(np.radians(hh)) / np.cos(np.radians(60.0 - hh)))
        gg = 3.0 * ii - (rr + bb)
        r[seg1] = rr
        g[seg1] = gg
        b[seg1] = bb

    if seg2.any():
        hh = h[seg2] - 120.0
        ss = s[seg2]
        ii = i[seg2]
        rr = ii * (1.0 - ss)
        gg = ii * (1.0 + ss * np.cos(np.radians(hh)) / np.cos(np.radians(60.0 - hh)))
        bb = 3.0 * ii - (rr + gg)
        r[seg2] = rr
        g[seg2] = gg
        b[seg2] = bb

    if seg3.any():
        hh = h[seg3] - 240.0
        ss = s[seg3]
        ii = i[seg3]
        gg = ii * (1.0 - ss)
        bb = ii * (1.0 + ss * np.cos(np.radians(hh)) / np.cos(np.radians(60.0 - hh)))
        rr = 3.0 * ii - (gg + bb)
        r[seg3] = rr
        g[seg3] = gg
        b[seg3] = bb

    rest = ~(seg1 | seg2 | seg3)
    if rest.any():
        r[rest] = i[rest]
        g[rest] = i[rest]
        b[rest] = i[rest]

    return np.clip(np.dstack([r, g, b]), 0.0, 1.0)


def _hw1_as_float_rgb(input_image):
    """将灰度、RGB 或 RGBA 输入转换为 [0,1] 的浮点 RGB。"""
    if input_image is None:
        raise ValueError("输入图像为空（None）")

    try:
        img = np.asarray(input_image)
    except Exception as exc:
        raise ValueError("无法把输入转换为图像数组：%s" % (exc,))

    if img.dtype.kind not in ("b", "u", "i", "f"):
        raise ValueError(
            "图像数组元素类型不支持：dtype=%s（需要 bool、整数或浮点类型）" % (img.dtype,))

    if img.ndim == 2:
        img = np.dstack([img] * 3)
    elif img.ndim == 3:
        if img.shape[2] == 1:
            img = np.repeat(img, 3, axis=2)
        elif img.shape[2] == 4:
            img = img[:, :, :3]
        elif img.shape[2] != 3:
            raise ValueError(
                "图像通道数不支持：shape=%s（需要 1、3 或 4 通道）" % (img.shape,))
    else:
        raise ValueError(
            "图像维度不支持：ndim=%d shape=%s（需要 2 维灰度图或 3 维彩色图）"
            % (img.ndim, img.shape))

    if img.shape[0] == 0 or img.shape[1] == 0:
        raise ValueError("图像尺寸无效：shape=%s" % (img.shape,))

    if img.dtype.kind == "b":
        return img.astype(np.float64)

    if img.dtype.kind == "f":
        out = img.astype(np.float64)
        if out.max() > 1.0:
            out = out / 255.0
        return np.clip(out, 0.0, 1.0)

    return np.clip(img.astype(np.float64), 0.0, 255.0) / 255.0


def _hw1_require_cv2():
    """按需导入 OpenCV，缺失时提示用户。"""
    try:
        import cv2
    except ImportError as exc:  # pragma: no cover - 取决于运行环境
        raise gr.Error("未安装 OpenCV（cv2），无法使用官方 HLS 路径：%s" % (exc,), duration=5)
    return cv2


def _hw1_rgb_to_hls_opencv(rgb):
    """RGB 转 OpenCV HLS，返回顺序统一为 H（度）、S、L。"""
    cv2 = _hw1_require_cv2()
    rgb_clip = np.clip(np.asarray(rgb, dtype=np.float64), 0.0, 1.0)
    bgr = np.ascontiguousarray(np.rint(rgb_clip * 255.0)[:, :, ::-1].astype(np.uint8))
    hls = cv2.cvtColor(bgr, cv2.COLOR_BGR2HLS)
    h = hls[:, :, 0].astype(np.float64) * (360.0 / 180.0)
    l = hls[:, :, 1].astype(np.float64) / 255.0
    s = hls[:, :, 2].astype(np.float64) / 255.0
    return np.dstack([h, s, l])


def _hw1_hls_opencv_to_rgb(hls):
    """H（度）、S、L 转为 RGB；OpenCV 路径使用 8 位量化。"""
    cv2 = _hw1_require_cv2()
    h = np.mod(np.asarray(hls[:, :, 0], dtype=np.float64), 360.0)
    s = np.clip(np.asarray(hls[:, :, 1], dtype=np.float64), 0.0, 1.0)
    l = np.clip(np.asarray(hls[:, :, 2], dtype=np.float64), 0.0, 1.0)
    packed = np.dstack([np.mod(np.rint(h / 360.0 * 180.0), 180.0),
                        np.rint(l * 255.0), np.rint(s * 255.0)])
    packed = np.ascontiguousarray(np.clip(packed, 0.0, 255.0).astype(np.uint8))
    bgr = cv2.cvtColor(packed, cv2.COLOR_HLS2BGR)
    return np.clip(bgr[:, :, ::-1].astype(np.float64) / 255.0, 0.0, 1.0)


def _hw1_adjust_in_hsi(img_f, h_slider, s_slider, l_slider):
    """在课件 HSI 空间调整色相、饱和度和明度。"""
    hsi = _hw1_rgb_to_hsi(img_f)
    h_new = np.mod(hsi[:, :, 0] + float(h_slider) * 180.0, 360.0)       # 色相平移：[-1,1] 对应正负 180 度
    s_new = np.clip(hsi[:, :, 1] * (1.0 + float(s_slider)), 0.0, 1.0)   # 饱和度按比例缩放
    i_new = np.clip(hsi[:, :, 2] * (1.0 + float(l_slider)), 0.0, 1.0)   # 明度乘性模型 L' = L * (1 + l)
    return _hw1_hsi_to_rgb(np.dstack([h_new, s_new, i_new]))


def _hw1_adjust_in_hls_opencv(img_f, h_slider, s_slider, l_slider):
    """在 OpenCV HLS 空间应用相同的滑杆参数。"""
    hls = _hw1_rgb_to_hls_opencv(img_f)
    h_new = np.mod(hls[:, :, 0] + float(h_slider) * 180.0, 360.0)
    s_new = np.clip(hls[:, :, 1] * (1.0 + float(s_slider)), 0.0, 1.0)
    l_new = np.clip(hls[:, :, 2] * (1.0 + float(l_slider)), 0.0, 1.0)
    return _hw1_hls_opencv_to_rgb(np.dstack([h_new, s_new, l_new]))


def _hw1_apply_vibrance(sat, amount):
    """自然饱和度近似：S' = S * [1 + amount * (1-S)^2]。"""
    s = np.clip(np.asarray(sat, dtype=np.float64), 0.0, 1.0)
    gain = 1.0 + float(np.clip(amount, -1.0, 1.0)) * (1.0 - s) ** 2
    return np.clip(s * gain, 0.0, 1.0)
_HW1_PS_CONTRAST_A_MAX = 4.0


def _hw1_ps_contrast_a(contrast):
    """把 UI 的对比度滑杆 [-1,1] 映射成 S 曲线斜率参数 a ∈ [-4,4]。"""
    return float(contrast) * _HW1_PS_CONTRAST_A_MAX


def _hw1_ps_s_curve(x, a):
    """正对比度使用 tanh 曲线，负对比度使用其反函数；固定黑白与中灰。"""
    x = np.clip(np.asarray(x, dtype=np.float64), 0.0, 1.0)
    a = float(a)
    if abs(a) < 1e-9:
        return x.copy()
    if a > 0:
        return 0.5 + 0.5 * np.tanh(a * (x - 0.5)) / np.tanh(a * 0.5)
    k = -a
    scaled = np.clip((2.0 * x - 1.0) * np.tanh(k * 0.5), -0.999999, 0.999999)
    return 0.5 + np.arctanh(scaled) / k


def _hw1_ps_mid_slope(contrast):
    """计算对比度曲线在中灰处的斜率。"""
    a = _hw1_ps_contrast_a(contrast)
    if abs(a) < 1e-9:
        return 1.0
    if a > 0:
        return 0.5 * a / float(np.tanh(a * 0.5))
    k = -a
    return 2.0 * float(np.tanh(k * 0.5)) / k


def _hw1_ps_brightness_contrast(img_f, brightness, contrast):
    """PS 风格：先按 S 曲线调整对比度，再做 gamma 亮度（端点不动、不裁剪）。"""
    x = _hw1_ps_s_curve(img_f, _hw1_ps_contrast_a(contrast))
    gamma = 2.0 ** (-2.0 * float(brightness))
    return np.clip(np.power(np.clip(x, 0.0, 1.0), gamma), 0.0, 1.0)


def _hw1_ps_fit_contrast_a(target_slope, samples=256, coarse=401, refine=40):
    """用最小二乘标定自定义线性目标的曲线参数，返回参数及误差。"""
    x = np.linspace(0.0, 1.0, int(samples))
    y_t = np.clip(0.5 + (x - 0.5) * float(target_slope), 0.0, 1.0)

    def residual(a):
        d = _hw1_ps_s_curve(x, a) - y_t
        return float(np.sqrt(np.mean(d ** 2))), float(np.max(np.abs(d)))

    lo, hi = -_HW1_PS_CONTRAST_A_MAX, _HW1_PS_CONTRAST_A_MAX
    grid = np.linspace(lo, hi, int(coarse))
    rms = np.array([residual(a)[0] for a in grid])
    best = float(grid[int(np.argmin(rms))])
    step = (hi - lo) / max(int(coarse) - 1, 1)
    lo_b, hi_b = max(lo, best - step), min(hi, best + step)
    for _ in range(int(refine)):
        m1 = lo_b + (hi_b - lo_b) / 3.0
        m2 = hi_b - (hi_b - lo_b) / 3.0
        if residual(m1)[0] <= residual(m2)[0]:
            hi_b = m2
        else:
            lo_b = m1
    a_fit = 0.5 * (lo_b + hi_b)
    rms_err, max_err = residual(a_fit)
    return a_fit, rms_err, max_err

def _hw1_to_uint8(img_f):
    """float [0,1] -> uint8 [0,255]（四舍五入）。"""
    return np.clip(np.rint(np.asarray(img_f, dtype=np.float64) * 255.0), 0.0, 255.0).astype(np.uint8)


def _hw1_abs_diff(a_u8, b_u8):
    """逐像素绝对差；先提升到 int16，避免 uint8 相减回绕。"""
    return np.abs(a_u8.astype(np.int16) - b_u8.astype(np.int16))


_HW1_HUE_MEANINGFUL_S_MIN = 0.10


def _hw1_hue_angle_delta(h1_deg, h2_deg):
    """计算周期为 360 度的最短角距离，结果为 [0,180]。"""
    delta = np.abs(np.mod(np.asarray(h1_deg, dtype=np.float64), 360.0)
                   - np.mod(np.asarray(h2_deg, dtype=np.float64), 360.0))
    return np.minimum(delta, 360.0 - delta)


def _hw1_difference_vis(a_u8, b_u8, gain=5):
    """用 int32 放大绝对差，避免溢出，再裁剪为 uint8。"""
    scaled = _hw1_abs_diff(a_u8, b_u8).astype(np.int32) * int(gain)
    return np.clip(scaled, 0, 255).astype(np.uint8)


def _hw1_error_stats(a_u8, b_u8):
    """两张 uint8 图的误差统计：MAE、最大绝对误差、PSNR(dB)、逐通道 MAE。"""
    diff = _hw1_abs_diff(a_u8, b_u8).astype(np.float64)
    mae = float(diff.mean()) if diff.size else 0.0
    max_err = float(diff.max()) if diff.size else 0.0
    mse = float((diff ** 2).mean()) if diff.size else 0.0
    psnr = float("inf") if mse <= 0.0 else 10.0 * np.log10(255.0 ** 2 / mse)
    channel_mae = ([float(diff[:, :, c].mean()) for c in range(diff.shape[2])]
                   if diff.ndim == 3 else [mae])
    return {"mae": mae, "max": max_err, "psnr": psnr, "channel_mae": channel_mae}


def _hw1_side_by_side(panels, gap=4, gap_value=255):
    """把若干同尺寸的 (H,W) / (H,W,3) uint8 图横向拼接，中间用白色分隔条隔开。"""
    prepared = []
    for panel in panels:
        p = np.asarray(panel)
        if p.ndim == 2:
            p = np.dstack([p] * 3)
        prepared.append(p.astype(np.uint8))
    height = max(p.shape[0] for p in prepared)
    strips = []
    for index, p in enumerate(prepared):
        if p.shape[0] < height:  # 高度不同时底部补白，保证可拼接
            pad = np.full((height - p.shape[0], p.shape[1], 3), gap_value, dtype=np.uint8)
            p = np.vstack([p, pad])
        if index:
            strips.append(np.full((height, gap, 3), gap_value, dtype=np.uint8))
        strips.append(p)
    return np.hstack(strips)
def function_hw1_compare(input_image, h_slider, s_slider, l_slider):
    """返回两条路径的四联对比图及误差统计，分别报告模型差异和量化误差。"""
    if input_image is None:
        raise gr.Error('输入错误：在处理之前请先输入一张图像', duration=5)

    img_f = _hw1_as_float_rgb(input_image)
    img_u8 = _hw1_to_uint8(img_f)
    manual = _hw1_to_uint8(_hw1_adjust_in_hsi(img_f, h_slider, s_slider, l_slider))
    official = _hw1_to_uint8(_hw1_adjust_in_hls_opencv(img_f, h_slider, s_slider, l_slider))

    stats = _hw1_error_stats(manual, official)
    rt_manual = _hw1_error_stats(img_u8, _hw1_to_uint8(_hw1_adjust_in_hsi(img_f, 0.0, 0.0, 0.0)))
    rt_official = _hw1_error_stats(img_u8, _hw1_to_uint8(_hw1_adjust_in_hls_opencv(img_f, 0.0, 0.0, 0.0)))

    m_hls = _hw1_rgb_to_hls_opencv(manual.astype(np.float64) / 255.0)
    o_hls = _hw1_rgb_to_hls_opencv(official.astype(np.float64) / 255.0)
    h_delta = _hw1_hue_angle_delta(m_hls[:, :, 0], o_hls[:, :, 0])
    h_diff = float(h_delta.mean())
    h_diff_max = float(h_delta.max())
    sat_meaningful = np.minimum(m_hls[:, :, 1], o_hls[:, :, 1]) >= _HW1_HUE_MEANINGFUL_S_MIN
    h_diff_colored = (float(h_delta[sat_meaningful].mean())
                      if bool(sat_meaningful.any()) else float("nan"))
    colored_share = float(sat_meaningful.mean()) * 100.0
    s_diff = float(np.abs(m_hls[:, :, 1] - o_hls[:, :, 1]).mean())
    l_diff = float(np.abs(m_hls[:, :, 2] - o_hls[:, :, 2]).mean())

    diff_vis = _hw1_difference_vis(manual, official)
    figure = _hw1_side_by_side([img_u8, manual, official, diff_vis])

    psnr_text = ("inf（两路径完全一致）" if stats["psnr"] == float("inf")
                 else "%.2f dB" % stats["psnr"])
    lines = [
        "### 进阶① 对比实验：手写 HSL（课件 p72-p78） vs 官方 cv2.COLOR_BGR2HLS",
        "",
        "对比图顺序：**原图 | 手写(课件定义) | 官方 cv2 HLS | 差异 ×5**",
        "",
        "参数：色相 %+.2f×180°、饱和度 ×(1%+.2f)、亮度 ×(1%+.2f)"
        % (float(h_slider), float(s_slider), float(l_slider)),
        "",
        "| 指标 | 数值 |",
        "| --- | --- |",
        "| 两路径输出 RGB 的 MAE | %.3f / 255 |" % stats["mae"],
        "| 最大绝对误差 | %d / 255 |" % int(round(stats["max"])),
        "| PSNR | %s |" % psnr_text,
        "| 逐通道 MAE (R/G/B) | %.3f / %.3f / %.3f |" % tuple(stats["channel_mae"][:3]),
        "| 同一空间(cv2 HLS)的 H 平均角距离（最短圆弧，<=180°） | %.3f 度 |" % h_diff,
        "| 同一空间(cv2 HLS)的 H 最大角距离 | %.3f 度 |" % h_diff_max,
        "| 其中双方饱和度均 >= 0.10 的像素：H 平均角距离 | %.3f 度（占 %.1f%% 像素）"
        % (h_diff_colored, colored_share),
        "| 同一空间(cv2 HLS)的 S / L 偏差 | %.4f / %.4f |" % (s_diff, l_diff),
        "| 手写路径量化往返 MAE / 最大误差 | %.3f / %d |"
        % (rt_manual["mae"], int(round(rt_manual["max"]))),
        "| 官方路径量化往返 MAE / 最大误差 | %.3f / %d |"
        % (rt_official["mae"], int(round(rt_official["max"]))),
        "",
        "**模型差异 ≠ 实现错误**：课件的 HSL(HSI) 定义 L=(R+G+B)/3、S=1-3·min(R,G,B)/(R+G+B)；"
        "OpenCV 的 HLS 定义 L=(max+min)/2、S=(max-min)/(max+min)。两者的 L/S 数值本来就不可直接互比，"
        "所以这里比较的是**最终 RGB 输出**（用户真正看到的结果）与**换算到同一空间后的 H/S/L**；"
        "量化往返误差单独列出，用于把 8 位量化误差与数学模型差异分开。",
        "",
        "**色相按圆周统计**：H 是角度量（周期 360°），表中 H 偏差取**最短圆弧角距离**"
        "（359° 与 1° 记作 2°，而不是 358°；上限 180°），直接相减 abs(H1-H2) 是错误口径。",
        "",
        "**低饱和度像素的解释局限**：当饱和度 S 趋近 0（灰、近灰、极暗像素）时色相在数值上"
        "不稳定，官方路径的 8 位量化或极小的 RGB 差异都可能让 H 在大范围内跳动。因此表中另给"
        "出双方饱和度均 >= 0.10 的像素这一口径；它减少但不能完全消除该局限。H 偏差只能在"
        "两路输出 RGB 换算回同一空间后比较，不能用于判定哪一方实现更准确。",
    ]
    return figure, "\n".join(lines)

def function_hw1(input_image, mode, h_slider, s_slider, l_slider, brightness, contrast):
    if input_image is None:
        raise gr.Error('输入错误：在处理之前请先输入一张图像', duration=5)

    img_f = _hw1_as_float_rgb(input_image)

    if mode == "色相/饱和度":
        out_f = _hw1_adjust_in_hsi(img_f, h_slider, s_slider, l_slider)
    elif mode == "色相/饱和度 (官方cv2 HLS)":
        out_f = _hw1_adjust_in_hls_opencv(img_f, h_slider, s_slider, l_slider)
    elif mode == "自然饱和度 (PS vibrance)":
        hsi = _hw1_rgb_to_hsi(img_f)
        s_new = _hw1_apply_vibrance(hsi[:, :, 1], s_slider)
        out_f = _hw1_hsi_to_rgb(np.dstack([hsi[:, :, 0], s_new, hsi[:, :, 2]]))
    elif mode == "亮度/对比度":
        out_f = np.clip((img_f - 0.5) * (1.0 + float(contrast)) + 0.5 + float(brightness), 0.0, 1.0)
    elif mode == "亮度/对比度 (PS风格)":
        out_f = _hw1_ps_brightness_contrast(img_f, brightness, contrast)
    else:
        raise gr.Error(
            "不支持的模式：%s（支持：色相/饱和度、"
            "色相/饱和度 (官方cv2 HLS)、自然饱和度 (PS vibrance)、"
            "亮度/对比度、亮度/对比度 (PS风格)）" % (mode,), duration=5)

    output_image = np.clip(np.rint(out_f * 255.0), 0.0, 255.0).astype(np.uint8)

    out_hsi = _hw1_rgb_to_hsi(output_image.astype(np.float64) / 255.0)
    r_channel = output_image[:, :, 0]
    g_channel = output_image[:, :, 1]
    b_channel = output_image[:, :, 2]
    h_channel = np.clip(np.rint(out_hsi[:, :, 0] / 360.0 * 255.0), 0.0, 255.0).astype(np.uint8)
    s_channel = np.clip(np.rint(out_hsi[:, :, 1] * 255.0), 0.0, 255.0).astype(np.uint8)
    l_channel = np.clip(np.rint(out_hsi[:, :, 2] * 255.0), 0.0, 255.0).astype(np.uint8)

    return output_image, r_channel, g_channel, b_channel, h_channel, s_channel, l_channel


def function_hw2(input_image):
    if input_image is None:
        raise gr.Error('输入错误：在处理之前请先输入一张图像', duration=5)    
    output_image = input_image
    # 请补充作业2的图像处理代码
    return output_image

def function_hw3(bg_image, fg_image, mode):
    if bg_image["background"]is None:
        raise gr.Error('输入错误：在处理之前请先输入一张背景图像', duration=5)  
    if fg_image is None:
        raise gr.Error('输入错误：在处理之前请先输入一张前景图像', duration=5)     
    background = bg_image["background"]
    mask_layer = bg_image["layers"][0][:, :, 0]
    import cv2
    _, binary = cv2.threshold(mask_layer, 127, 255, cv2.THRESH_BINARY)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
    centers = [tuple(centroids[i]) for i in range(1, num_labels)]
    if len(centers) != 4:
        raise gr.Error("输入错误：请提供屏幕的四个顶点位置!")
    
    output_image = background
    # 请补充作业3的图像处理代码
    return output_image

def function_hw4(input_image):
    if input_image is None:
        raise gr.Error('输入错误：在处理之前请先输入一张图像', duration=5)
    output_image = input_image
    # 请补充作业4的图像处理代码
    return output_image

def function_hw5(input_image):
    if input_image is None:
        raise gr.Error('输入错误：在处理之前请先输入一张图像', duration=5)
    output_image = input_image
    # 请补充作业5的图像处理代码
    return output_image