#-*-coding:GBK -*-
import numpy as np
import gradio as gr


def _hw1_rgb_to_hsi(rgb):
    """RGB -> HSI（课件 p66-p84 定义）。

    输入 rgb: float 数组，值域 [0,1]，形状 (H, W, 3)，通道顺序 R,G,B。
    输出 (H, W, 3)：H 单位度、范围 [0,360)；S、I 范围 [0,1]。
      I = (R + G + B) / 3
      S = 1 - 3 * min(R,G,B) / (R + G + B)
      H = theta                (B <= G)
      H = 360 - theta          (B > G)
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
    """HSI -> RGB（课件 p78 分段逆变换）。

    输入/输出值域均为 [0,1]（H 以度为单位，范围 [0,360)）。
    三段公式：
      0   <= H < 120 : B = I(1-S), R = I[1 + S*cosH / cos(60-H)],  G = 3I-(R+B)
      120 <= H < 240 : R = I(1-S), G = I[1 + S*cosH'/cos(60-H')], B = 3I-(R+G), H' = H-120
      240 <= H < 360 : G = I(1-S), B = I[1 + S*cosH'/cos(60-H')], R = 3I-(G+B), H' = H-240
    结果裁剪到 [0,1]；裁剪会改变实际 H/S/I，这属于 RGB 立方体外的定义域限制。
    """
    h = np.mod(hsi[:, :, 0], 360.0)
    s = np.clip(hsi[:, :, 1], 0.0, 1.0)
    i = np.clip(hsi[:, :, 2], 0.0, 1.0)

    r = np.zeros_like(i)
    g = np.zeros_like(i)
    b = np.zeros_like(i)

    def _ratio(deg):
        """S * cos(deg) / cos(60 - deg)，分段内该式恒有定义。"""
        return s * np.cos(np.radians(deg)) / np.cos(np.radians(60.0 - deg))

    seg1 = (h >= 0.0) & (h < 120.0)
    b1 = i * (1.0 - s)
    r1 = i * (1.0 + _ratio(h))
    g1 = 3.0 * i - (r1 + b1)

    h2 = h - 120.0
    seg2 = (h >= 120.0) & (h < 240.0)
    r2 = i * (1.0 - s)
    g2 = i * (1.0 + _ratio(h2))
    b2 = 3.0 * i - (r2 + g2)

    h3 = h - 240.0
    seg3 = (h >= 240.0) & (h < 360.0)
    g3 = i * (1.0 - s)
    b3 = i * (1.0 + _ratio(h3))
    r3 = 3.0 * i - (g3 + b3)

    r = np.where(seg1, r1, np.where(seg2, r2, np.where(seg3, r3, i)))
    g = np.where(seg1, g1, np.where(seg2, g2, np.where(seg3, g3, i)))
    b = np.where(seg1, b1, np.where(seg2, b2, np.where(seg3, b3, i)))

    return np.clip(np.dstack([r, g, b]), 0.0, 1.0)


def _hw1_as_float_rgb(input_image):
    """把 Gradio 输入规整为 float RGB 数组 [0,1]，形状 (H, W, 3)。"""
    img = np.asarray(input_image)
    if img.ndim == 2:
        img = np.dstack([img] * 3)
    elif img.ndim == 3 and img.shape[2] == 4:
        img = img[:, :, :3]
    if img.dtype != np.uint8:
        img = np.clip(np.rint(img.astype(np.float64)), 0.0, 255.0).astype(np.uint8)
    return img.astype(np.float64) / 255.0


def function_hw1(input_image, mode, h_slider, s_slider, l_slider, brightness, contrast):
    if input_image is None:
        raise gr.Error('输入错误：在处理之前请先输入一张图像', duration=5)

    img_f = _hw1_as_float_rgb(input_image)

    if mode == "色相/饱和度":
        # 统一转到 HSI，在 H/S/I 三个分量上独立调整，再逆变换回 RGB
        hsi = _hw1_rgb_to_hsi(img_f)
        h_new = np.mod(hsi[:, :, 0] + float(h_slider) * 180.0, 360.0)   # 色相平移，[-1,1] -> ±180 度
        s_new = np.clip(hsi[:, :, 1] * (1.0 + float(s_slider)), 0.0, 1.0)  # 饱和度按比例缩放
        i_new = np.clip(hsi[:, :, 2] * (1.0 + float(l_slider)), 0.0, 1.0)  # 明度乘性模型 I' = I * (1 + l)
        out_f = _hw1_hsi_to_rgb(np.dstack([h_new, s_new, i_new]))
    else:
        # 亮度/对比度：自定义线性模型（不是 Photoshop 拟合），先对比度后亮度
        out_f = (img_f - 0.5) * (1.0 + float(contrast)) + 0.5 + float(brightness)
        out_f = np.clip(out_f, 0.0, 1.0)

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