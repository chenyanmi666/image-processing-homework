#-*-coding:GBK -*-
import numpy as np
import gradio as gr

# ---------------------------------------------------------------------------
# Gradio 版本兼容层
# 本机 gradio 3.36.1 的 gr.Error 签名为 (message)，不接受 duration 参数，
# 而本文件 function_hw1~hw5 统一写作 gr.Error(msg, duration=5)，
# 会在空输入时抛出 TypeError，界面得不到友好提示。
# 这里把本模块内的 gr 名称指向一个轻量代理：只接管 Error 的构造，
# 支持 duration 的版本原样透传，不支持的版本退化为单参数构造；
# 其余属性（Blocks、Image 等）全部原样转发给真实 gradio。
# 因此 function_hw2~hw5 的业务代码无需任何改动，
# 也不会修改 gradio 模块本身（UI.py、web_demo.py 里的 gr 不受影响）。
# ---------------------------------------------------------------------------
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
    """RGB 转 HSI（课件 p66-p84 定义）。

    输入 rgb: float 数组，值域 [0,1]，形状 (H, W, 3)，通道顺序 R, G, B。
    输出 (H, W, 3)：H 单位为度、范围 [0,360)；S、I 范围 [0,1]。
      I = (R + G + B) / 3
      S = 1 - 3 * min(R,G,B) / (R + G + B)
      H = theta           (B <= G)
      H = 360 - theta     (B > G)
      theta = arccos{ [(R-G)+(R-B)] / (2*sqrt((R-G)^2 + (R-B)*(G-B))) } * 180/pi
    退化情况（纯黑 R+G+B=0、灰色 den=0）S 与 H 均取 0，避免除零。
    """
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
    """HSI 转 RGB（课件 p78 分段逆变换）。

    输入/输出值域均为 [0,1]，H 以度为单位（先取模到 [0,360)）。
    三段公式：
      0   <= H < 120 : B = I(1-S), R = I[1 + S*cosH / cos(60-H)],  G = 3I-(R+B)
      120 <= H < 240 : R = I(1-S), G = I[1 + S*cosH'/cos(60-H')], B = 3I-(R+G), H' = H-120
      240 <= H < 360 : G = I(1-S), B = I[1 + S*cosH'/cos(60-H')], R = 3I-(G+B), H' = H-240

    实现要点：每一段只对该段内的像素求值（布尔掩码索引），
    不再对全图套用三段公式后用 np.where 选择结果。
    这样可避免在无效分段上出现 cos(60-H') 趋近 0 而造成的除零/无穷大中间量。
    结果裁剪到 [0,1]；裁剪会改变实际 H/S/I，这是 RGB 立方体外的定义域限制。
    """
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
    """把传入的图像规整为 float RGB 数组。

    返回 shape (H, W, 3)、dtype float64、值域 [0,1] 的数组（通道顺序 R, G, B）。
    非法输入抛出 ValueError，消息中给出实际的 shape/dtype，
    避免调用方在后续索引、广播时遇到难以定位的异常。

    接受的输入：
      - 2 维灰度图，或 3 维 (H, W, 1) / (H, W, 3) / (H, W, 4)
      - 元素类型为 bool、整数或浮点（数值类型）
      - 浮点输入最大值不超过 1 时按 [0,1] 处理，超过 1 时按 0-255 量程处理
    """
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


# ---------------------------------------------------------------------------
# 作业1 进阶①：官方 OpenCV HLS 路径（对应作业要求的基本档：直接调用 cv2.cvtColor）
#
# 重要说明：OpenCV 的 COLOR_BGR2HLS 用的是 HLS 模型
#   L = (max + min) / 2、S = (max - min) / (max + min)（8 位图 H 折半为 [0,180]），
# 与课件 p72-p78 的 HSL(HSI)（L = (R+G+B)/3、S = 1 - 3*min(R,G,B)/(R+G+B)）
# **不是同一个数学模型**。本函数按作业原文的 BGR 语义调用：
#   RGB -> BGR -> cv2.COLOR_BGR2HLS。
# ---------------------------------------------------------------------------

def _hw1_require_cv2():
    """按需导入 OpenCV；缺失时给出可读提示，不影响其它模式。"""
    try:
        import cv2
    except ImportError as exc:  # pragma: no cover - 取决于运行环境
        raise gr.Error("未安装 OpenCV（cv2），无法使用官方 HLS 路径：%s" % (exc,), duration=5)
    return cv2


def _hw1_rgb_to_hls_opencv(rgb):
    """RGB(float, [0,1]) -> OpenCV HLS，返回 (H 度, S, L)，形状 (H, W, 3)。

    输入先量化成 8 位 BGR 再调用 cv2.COLOR_BGR2HLS；
    OpenCV 的 HLS 通道顺序是 H, L, S，这里统一整理为 (H, S, L)。
    该函数含 8 位量化，因此往返不是无损的，量化误差在对比实验中单独统计。
    """
    cv2 = _hw1_require_cv2()
    rgb_clip = np.clip(np.asarray(rgb, dtype=np.float64), 0.0, 1.0)
    bgr = np.ascontiguousarray(np.rint(rgb_clip * 255.0)[:, :, ::-1].astype(np.uint8))
    hls = cv2.cvtColor(bgr, cv2.COLOR_BGR2HLS)
    h = hls[:, :, 0].astype(np.float64) * (360.0 / 180.0)
    l = hls[:, :, 1].astype(np.float64) / 255.0
    s = hls[:, :, 2].astype(np.float64) / 255.0
    return np.dstack([h, s, l])


def _hw1_hls_opencv_to_rgb(hls):
    """OpenCV HLS((H 度, S, L)) -> RGB(float, [0,1])，经 8 位量化。"""
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
    """手写路径：在课件的 HSL(HSI) 空间分别调整色相/饱和度/明度，再逆变换回 RGB。"""
    hsi = _hw1_rgb_to_hsi(img_f)
    h_new = np.mod(hsi[:, :, 0] + float(h_slider) * 180.0, 360.0)       # 色相平移：[-1,1] 对应正负 180 度
    s_new = np.clip(hsi[:, :, 1] * (1.0 + float(s_slider)), 0.0, 1.0)   # 饱和度按比例缩放
    i_new = np.clip(hsi[:, :, 2] * (1.0 + float(l_slider)), 0.0, 1.0)   # 明度乘性模型 L' = L * (1 + l)
    return _hw1_hsi_to_rgb(np.dstack([h_new, s_new, i_new]))


def _hw1_adjust_in_hls_opencv(img_f, h_slider, s_slider, l_slider):
    """官方路径：在 OpenCV 的 HLS 空间做与手写路径**语义相同**的调整。

    语义对齐（便于对比实验）：色相平移 ±180 度、饱和度 ×(1+s)、亮度 ×(1+l)；
    但由于两个空间的 H/S/L 数学定义不同，结果不会逐一相等。
    """
    hls = _hw1_rgb_to_hls_opencv(img_f)
    h_new = np.mod(hls[:, :, 0] + float(h_slider) * 180.0, 360.0)
    s_new = np.clip(hls[:, :, 1] * (1.0 + float(s_slider)), 0.0, 1.0)
    l_new = np.clip(hls[:, :, 2] * (1.0 + float(l_slider)), 0.0, 1.0)
    return _hw1_hls_opencv_to_rgb(np.dstack([h_new, s_new, l_new]))


def _hw1_apply_vibrance(sat, amount):
    """进阶③：Photoshop 风格的自然饱和度（vibrance）。

    Photoshop 的"自然饱和度"优先提升**本来不鲜艳**的颜色，对已接近纯色的像素几乎不动
    （保护高饱和区域，避免溢出与假色）。这里用增益衰减模型实现：

        gain(S) = 1 + amount * (1 - S)^2 ，  S' = clip(S * gain, 0, 1)

      - S = 1（纯色）：gain = 1，完全不动；
      - S 越小增益越大，中间饱和度处提升最明显；
      - 灰色的 S 本身为 0，输出仍为 0（不会被染色）。

    amount ∈ [-1, 1]，0 为恒等；amount < 0 表示降低自然饱和度。
    """
    s = np.clip(np.asarray(sat, dtype=np.float64), 0.0, 1.0)
    gain = 1.0 + float(np.clip(amount, -1.0, 1.0)) * (1.0 - s) ** 2
    return np.clip(s * gain, 0.0, 1.0)
# ---------------------------------------------------------------------------
# 作业1 进阶②：Photoshop 风格的亮度 / 对比度（非线性、中灰锚定）
#
# Photoshop（CS3 以后）的"亮度/对比度"不是线性模型：
#   - 对比度是 S 形曲线：中灰 0.5 不动、黑白端点不动，正向变陡、负向把曲线压平；
#   - 亮度是非线性的：中灰附近变化大、黑白端点基本不动（不直接裁剪高光/阴影）。
# 本实现用 tanh 构造 S 曲线、用 gamma 构造亮度，端点与中灰的锚定可解析验证。
#
# 诚实声明：本机没有 Photoshop，**未做**与 PS 输出的逐像素比对，
# 因此该功能标注为"PS 风格"而不是"PS 复刻"；参数标定实验见
# _hw1_ps_fit_contrast_a，行为验证见 tests/test_hw1.py 的 TestPsStyleTone。
# ---------------------------------------------------------------------------
_HW1_PS_CONTRAST_A_MAX = 4.0


def _hw1_ps_contrast_a(contrast):
    """把 UI 的对比度滑杆 [-1,1] 映射成 S 曲线斜率参数 a ∈ [-4,4]。"""
    return float(contrast) * _HW1_PS_CONTRAST_A_MAX


def _hw1_ps_s_curve(x, a):
    """中灰锚定的 S 曲线：0->0、0.5->0.5、1->1，端点与中灰都不动。

    a > 0（增对比）：y = 0.5 + 0.5*tanh(a*(x-0.5))/tanh(a/2)，中灰斜率 = 0.5a/tanh(a/2) > 1；
    a < 0（减对比）：取**同强度正曲线的反函数**
        y = 0.5 + artanh((2x-1)*tanh(k/2))/k，k = |a|
      中灰斜率 = 2*tanh(k/2)/k < 1，即真正把曲线压平。

    注意：直接往上面那条公式里代入 a<0 是**错误的**——该式对 a 是偶函数
    （分子分母同时变号），会得到与 a>0 完全相同的曲线，使"减对比"变成"增对比"。
    """
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
    """S 曲线中灰处的斜率（解析式）：a>0 为 0.5a/tanh(a/2)，a<0 为 2*tanh(k/2)/k，两者互为倒数。"""
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
    """标定实验：最小二乘求 a，使 S 曲线最接近"同一中灰斜率"的线性斜坡。

    目标曲线 y_t(x) = clip(0.5 + (x - 0.5) * target_slope)，x 取 256 个灰度级；
    在 a ∈ [-4, 4] 上先粗扫再三分细化（a<0 对应减对比，中灰斜率 < 1）。
    返回 (a_fit, rms_error, max_error)，残差用于报告"S 曲线偏离线性的程度"。
    """
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
# ---------------------------------------------------------------------------
# 作业1 进阶①（实验部分）：手写 HSL(课件定义) vs 官方 cv2.COLOR_BGR2HLS
# ---------------------------------------------------------------------------

def _hw1_to_uint8(img_f):
    """float [0,1] -> uint8 [0,255]（四舍五入）。"""
    return np.clip(np.rint(np.asarray(img_f, dtype=np.float64) * 255.0), 0.0, 255.0).astype(np.uint8)


def _hw1_abs_diff(a_u8, b_u8):
    """逐像素绝对差；先提升到 int16，避免 uint8 相减回绕。"""
    return np.abs(a_u8.astype(np.int16) - b_u8.astype(np.int16))


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
    """进阶①：手写 HSL（课件 p72-p78）与官方 cv2.COLOR_BGR2HLS 的对比实验。

    同一组滑杆参数分别走两条路径，返回 (对比图, 统计文本)：
      对比图：原图 | 手写(课件定义) | 官方 cv2 HLS | 差异 ×5 放大
      统计文本：最终 RGB 输出层面的 MAE / 最大误差 / PSNR / 逐通道 MAE；
                换算到同一测量空间（cv2 HLS）后的 H/S/L 偏差；
                以及两条路径各自"原图 -> 空间 -> 原图"的量化往返误差。

    目的是把**数学模型差异**（两套 L/S 定义不同）与**8 位量化误差**分开报告，
    避免仅凭通道数值判定"谁更准确"。
    """
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
    h_diff = float(np.abs(m_hls[:, :, 0] - o_hls[:, :, 0]).mean())
    s_diff = float(np.abs(m_hls[:, :, 1] - o_hls[:, :, 1]).mean())
    l_diff = float(np.abs(m_hls[:, :, 2] - o_hls[:, :, 2]).mean())

    diff_vis = np.clip(_hw1_abs_diff(manual, official) * 5, 0, 255).astype(np.uint8)
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
        "| 同一空间(cv2 HLS)的 H 偏差 | %.3f 度 |" % h_diff,
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
    ]
    return figure, "\n".join(lines)

def function_hw1(input_image, mode, h_slider, s_slider, l_slider, brightness, contrast):
    if input_image is None:
        raise gr.Error('输入错误：在处理之前请先输入一张图像', duration=5)

    img_f = _hw1_as_float_rgb(input_image)

    if mode == "色相/饱和度":
        # 基础实现：手写转换，在课件定义的 HSL(HSI) 空间里分别调整 H / S / L
        out_f = _hw1_adjust_in_hsi(img_f, h_slider, s_slider, l_slider)
    elif mode == "色相/饱和度 (官方cv2 HLS)":
        # 基本实现：直接调用 cv2.COLOR_BGR2HLS，在 OpenCV 的 HLS（L=(max+min)/2）里调整
        out_f = _hw1_adjust_in_hls_opencv(img_f, h_slider, s_slider, l_slider)
    elif mode == "自然饱和度 (PS vibrance)":
        # 进阶③：PS 风格的自然饱和度（使用饱和度滑杆作为强度，忽略色相/明度滑杆）
        hsi = _hw1_rgb_to_hsi(img_f)
        s_new = _hw1_apply_vibrance(hsi[:, :, 1], s_slider)
        out_f = _hw1_hsi_to_rgb(np.dstack([hsi[:, :, 0], s_new, hsi[:, :, 2]]))
    elif mode == "亮度/对比度":
        # 自定义线性模型（不是 Photoshop 拟合），先对比度后亮度
        out_f = np.clip((img_f - 0.5) * (1.0 + float(contrast)) + 0.5 + float(brightness), 0.0, 1.0)
    elif mode == "亮度/对比度 (PS风格)":
        # 进阶②：PS 风格非线性模型（中灰锚定、端点不裁剪、S 形对比度 + gamma 亮度）
        out_f = _hw1_ps_brightness_contrast(img_f, brightness, contrast)
    else:
        raise gr.Error(
            "不支持的模式：%s（支持：色相/饱和度、"
            "色相/饱和度 (官方cv2 HLS)、自然饱和度 (PS vibrance)、"
            "亮度/对比度、亮度/对比度 (PS风格)）" % (mode,), duration=5)

    output_image = np.clip(np.rint(out_f * 255.0), 0.0, 255.0).astype(np.uint8)

    # 7 路输出中的通道分解图，均取自处理后的结果
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