# -*- coding: utf-8 -*-
"""为 Gradio 3.x 提供模板需要的 ImageEditor 和 Brush；已有官方组件时不替换。"""
from __future__ import annotations

import gradio as gr
import numpy as np

__all__ = ["LIMITATIONS", "Brush", "ImageEditor", "install"]

LIMITATIONS = (
    "gradio 3.x 兼容实现与原版 ImageEditor 的差异："
    "(1) 无真正的图层，编辑结果以 mask 形式给出，layers 恒为长度 1 的列表；"
    "(2) 画笔颜色固定（mask 图），Brush.colors / color_mode 被忽略；"
    "(3) 橡皮无法禁用，eraser=False 被忽略；"
    "(4) composite 由 mask 区域填充 Brush.colors[0]（默认红色）得到，是近似值。"
)


class Brush:
    """``gr.Brush`` 的最小替身；仅 ``default_size`` 会映射到 3.x 的 ``brush_radius``。"""

    def __init__(self, default_size=1, colors=None, color_mode="fixed", **kwargs):
        self.default_size = default_size
        self.colors = list(colors) if colors else []
        self.color_mode = color_mode
        self.extra = dict(kwargs)


class ImageEditor(gr.Image):
    """用 Gradio 3.x 的 sketch 组件适配 ImageEditor 的字典输入。"""

    _VALID_SOURCES = ("upload", "webcam", "canvas")
    _DEFAULT_COLOR = (255, 0, 0)

    @classmethod
    def get_block_name(cls):
        """使用前端内置 image 类型渲染。"""
        return "image"

    def __init__(
        self,
        value=None,
        *,
        sources=None,
        source=None,
        layers=None,
        brush=None,
        eraser=None,
        crop_size=None,
        transforms=None,
        image_mode="RGB",
        type="numpy",
        mirror_webcam=None,
        show_download_button=None,
        **kwargs,
    ):
        # 4.x 独有参数：3.x 无对应能力，显式记录后忽略（不静默丢失语义）
        self.four_x_layers = layers
        self.four_x_eraser = eraser
        self.four_x_crop_size = crop_size
        self.four_x_transforms = transforms
        self.four_x_show_download_button = show_download_button
        if brush is not None and kwargs.get("brush_radius") is None:
            kwargs["brush_radius"] = getattr(brush, "default_size", None)
        self._composite_color = self._color_from(brush)
        super().__init__(
            value=value,
            source=source or self._resolve_source(sources),
            tool="sketch",
            type=type,
            image_mode=image_mode,
            **kwargs,
        )

    @classmethod
    def _resolve_source(cls, sources):
        """把 4.x 的 ``sources`` 列表收敛为 3.x 的单值 ``source``。"""
        if not sources:
            return "upload"
        if isinstance(sources, str):
            sources = [sources]
        for candidate in sources:
            if candidate in cls._VALID_SOURCES:
                return candidate
        return "upload"

    @classmethod
    def _color_from(cls, brush):
        colors = getattr(brush, "colors", None) or []
        if colors:
            first = colors[0]
            if isinstance(first, str) and first.startswith("#") and len(first) == 7:
                return tuple(int(first[i:i + 2], 16) for i in (1, 3, 5))
        return cls._DEFAULT_COLOR

    @staticmethod
    def _mask_to_bool(mask):
        arr = np.asarray(mask)
        gray = arr[:, :, 0] if arr.ndim == 3 else arr
        return gray > 127

    def _composite(self, image, mask):
        """按 mask 区域填充画笔色，近似 4.x 的 composite。"""
        if mask is None or not isinstance(image, np.ndarray):
            return image
        out = np.array(image, copy=True)
        selected = self._mask_to_bool(mask)
        if out.ndim == 3:
            out[selected] = self._composite_color[: out.shape[2]]
        elif out.ndim == 2:
            out[selected] = self._composite_color[0]
        return out

    def preprocess(self, payload):
        raw = super().preprocess(payload)
        if raw is None:
            return None
        if isinstance(raw, dict):
            image, mask = raw.get("image"), raw.get("mask")
        else:  # 兜底：3.x 在 source="canvas" 等情形只返回图
            image, mask = raw, None
        if mask is None and isinstance(image, np.ndarray):
            # 保证 layers[0] 始终存在，与 4.x 的"至少一层"行为一致
            shape = image.shape[:2] + ((image.shape[2],) if image.ndim == 3 else ())
            mask = np.zeros(shape, dtype=np.uint8)
        return {
            "background": image,
            "layers": [] if mask is None else [mask],
            "composite": self._composite(image, mask),
        }

    def postprocess(self, y):
        if isinstance(y, dict):  # 容忍直接回填 4.x 风格字典
            y = y.get("background") if y.get("background") is not None else y.get("composite")
        return super().postprocess(y)


def install(module=None):
    """把 3.x 兼容实现注入 gradio；gradio>=4 时不做任何事。返回是否发生了注入。"""
    target = module if module is not None else gr
    if hasattr(target, "ImageEditor") and hasattr(target, "Brush"):
        return False
    if not hasattr(target, "Brush"):
        target.Brush = Brush
    if not hasattr(target, "ImageEditor"):
        target.ImageEditor = ImageEditor
    return True
