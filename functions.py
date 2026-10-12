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


def function_hw1(input_image, mode, h_slider, s_slider, l_slider, brightness, contrast):
    if input_image is None:
        raise gr.Error('输入错误：在处理之前请先输入一张图像', duration=5)

    img_f = _hw1_as_float_rgb(input_image)

    if mode == "色相/饱和度":
        # 统一转到 HSI，在 H/S/I 三个分量上独立调整，再逆变换回 RGB
        hsi = _hw1_rgb_to_hsi(img_f)
        h_new = np.mod(hsi[:, :, 0] + float(h_slider) * 180.0, 360.0)       # 色相平移，[-1,1] 对应正负 180 度
        s_new = np.clip(hsi[:, :, 1] * (1.0 + float(s_slider)), 0.0, 1.0)   # 饱和度按比例缩放
        i_new = np.clip(hsi[:, :, 2] * (1.0 + float(l_slider)), 0.0, 1.0)   # 明度乘性模型 I' = I * (1 + l)
        out_f = _hw1_hsi_to_rgb(np.dstack([h_new, s_new, i_new]))
    elif mode == "亮度/对比度":
        # 自定义线性模型（不是 Photoshop 拟合），先对比度后亮度
        out_f = (img_f - 0.5) * (1.0 + float(contrast)) + 0.5 + float(brightness)
        out_f = np.clip(out_f, 0.0, 1.0)
    else:
        raise gr.Error(
            "不支持的模式：%s（仅支持 '色相/饱和度' 与 '亮度/对比度'）" % (mode,), duration=5)

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