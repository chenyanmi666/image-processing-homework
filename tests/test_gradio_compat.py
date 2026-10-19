"""gradio 3.x 兼容层 `gradio_compat` 的单元测试。

回答三个问题：
1. `install()` 是否安全（幂等、不覆盖真实的 4.x API）？
2. 3.x 下 `gr.ImageEditor(...)` 的输入契约是否与 gradio 4.x 一致
   （`{"background": ..., "layers": [...], "composite": ...}`）？
3. 模板 `UI.py` / `functions.py` 的既有写法
   （`bg_image["background"]`、`bg_image["layers"][0][:, :, 0]`）在 3.x 下是否依然成立？

运行：python tests/test_gradio_compat.py
"""
from __future__ import annotations

import base64
import io
import pathlib
import sys
import types
import unittest
from unittest import mock

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import gradio as gr  # noqa: E402

import gradio_compat as compat  # noqa: E402

INSTALLED_BY_US = compat.install()


def _data_url(array):
    """把 numpy 图编码为 gradio 前端使用的 data URL。"""
    buffer = io.BytesIO()
    Image.fromarray(np.asarray(array, dtype=np.uint8)).save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def _make_editor(**overrides):
    kwargs = {
        "sources": ["upload", "webcam", "clipboard"],
        "type": "numpy",
        "label": "背景图像",
        "brush": compat.Brush(default_size=4, colors=["#FF0000"], color_mode="fixed"),
        "eraser": False,
        "layers": False,
    }
    kwargs.update(overrides)
    return gr.ImageEditor(**kwargs)


def _four_dot_mask(size=64):
    """4 个互不相连的白块，模拟用户在图上点出的四个屏幕角点。"""
    mask = np.zeros((size, size, 3), dtype=np.uint8)
    for cy, cx in ((10, 10), (10, 50), (50, 10), (50, 50)):
        mask[cy - 3:cy + 3, cx - 3:cx + 3] = 255
    return mask


class InstallTests(unittest.TestCase):
    def test_installs_on_bare_module(self):
        module = types.SimpleNamespace()
        self.assertTrue(compat.install(module))
        self.assertIs(module.ImageEditor, compat.ImageEditor)
        self.assertIs(module.Brush, compat.Brush)

    def test_install_is_idempotent(self):
        module = types.SimpleNamespace()
        compat.install(module)
        self.assertFalse(compat.install(module))

    def test_does_not_override_existing_4x_api(self):
        sentinel = object()
        module = types.SimpleNamespace(ImageEditor=sentinel, Brush=sentinel)
        self.assertFalse(compat.install(module))
        self.assertIs(module.ImageEditor, sentinel)
        self.assertIs(module.Brush, sentinel)

    def test_real_gradio_exposes_both_names(self):
        self.assertTrue(hasattr(gr, "ImageEditor"))
        self.assertTrue(hasattr(gr, "Brush"))
        if INSTALLED_BY_US:
            self.assertIs(gr.ImageEditor, compat.ImageEditor)
        else:  # gradio >= 4：兼容层应让位给官方实现
            self.assertIsNot(gr.ImageEditor, compat.ImageEditor)


class ConstructionTests(unittest.TestCase):
    def test_accepts_4x_only_arguments(self):
        editor = _make_editor()
        self.assertEqual(editor.tool, "sketch")  # 3.x 中等价的编辑工具
        self.assertEqual(editor.type, "numpy")
        self.assertFalse(editor.four_x_eraser)
        self.assertFalse(editor.four_x_layers)
        self.assertEqual(editor.brush_radius, 4)  # Brush.default_size -> brush_radius

    def test_source_resolution(self):
        resolve = compat.ImageEditor._resolve_source
        self.assertEqual(resolve(None), "upload")
        self.assertEqual(resolve("webcam"), "webcam")
        self.assertEqual(resolve(["clipboard", "upload"]), "upload")
        self.assertEqual(resolve(["clipboard"]), "upload")  # 3.x 无 clipboard -> 回退

    def test_composite_color_taken_from_brush(self):
        self.assertEqual(_make_editor()._composite_color, (255, 0, 0))
        editor = _make_editor(brush=None)
        self.assertEqual(editor._composite_color, (255, 0, 0))

    def test_limitations_are_documented(self):
        self.assertIn("橡皮", compat.LIMITATIONS)
        self.assertIn("layers", compat.LIMITATIONS)

class PreprocessContractTests(unittest.TestCase):
    """shim 的输入契约必须与 gradio 4.x 的 ImageEditor 一致。"""

    def setUp(self):
        self.editor = _make_editor()
        self.image = np.zeros((64, 64, 3), dtype=np.uint8)
        self.image[..., 1] = 128
        self.mask = _four_dot_mask()
        self.value = self.editor.preprocess(
            {"image": _data_url(self.image), "mask": _data_url(self.mask)}
        )

    def test_returns_editor_value_keys(self):
        self.assertIsInstance(self.value, dict)
        self.assertEqual(set(self.value), {"background", "layers", "composite"})

    def test_background_round_trips_pixels(self):
        self.assertTrue(np.array_equal(self.value["background"], self.image))

    def test_mask_is_usable_like_template_code(self):
        # 模板 functions.py 的写法：mask_layer = bg_image["layers"][0][:, :, 0]
        layer = self.value["layers"][0][:, :, 0]
        self.assertTrue(np.array_equal(layer, self.mask[:, :, 0]))
        self.assertGreater(int(np.count_nonzero(layer)), 0)

    def test_composite_paints_brush_color(self):
        composite = self.value["composite"]
        selected = self.mask[:, :, 0] > 0
        self.assertEqual(int(composite[selected][0, 0]), 255)
        self.assertEqual(int(composite[selected][0, 1]), 0)
        self.assertTrue(np.array_equal(np.where(selected, 0, composite[..., 2]), self.image[..., 2]))

    def test_template_function_hw3_accepts_our_value(self):
        """把 shim 的输出直接喂给模板 function_hw3，验证其分割逻辑仍然成立。"""
        import cv2

        import functions

        foreground = np.full((16, 16, 3), 255, dtype=np.uint8)
        output = functions.function_hw3(self.value, foreground, "Nearest")
        self.assertTrue(np.array_equal(output, self.image))

        mask_layer = self.value["layers"][0][:, :, 0]
        _, binary = cv2.threshold(mask_layer, 127, 255, cv2.THRESH_BINARY)
        num_labels, _, stats, centroids = cv2.connectedComponentsWithStats(binary)
        self.assertEqual(num_labels - 1, 4)          # 4 个屏幕角点
        self.assertEqual(len(stats), 5)              # 4 个前景 + 1 个背景
        self.assertTrue(all(len(center) == 2 for center in centroids[1:]))

    def test_none_payload_returns_none(self):
        self.assertIsNone(self.editor.preprocess(None))

    def test_array_payload_falls_back_to_single_empty_layer(self):
        """3.x 只返回图（无 mask）时，仍要给出长度为 1 的 layers，避免取 [0] 越界。"""
        with mock.patch.object(gr.Image, "preprocess", return_value=self.image):
            value = self.editor.preprocess("ignored")
        self.assertEqual(len(value["layers"]), 1)
        self.assertEqual(value["layers"][0].dtype, np.uint8)
        self.assertEqual(int(np.count_nonzero(value["layers"][0])), 0)
        self.assertTrue(np.array_equal(value["composite"], self.image))

    def test_postprocess_accepts_numpy_and_dict(self):
        plain = self.editor.postprocess(self.image)
        self.assertTrue(isinstance(plain, str) and plain.startswith("data:image"))
        wrapped = self.editor.postprocess(self.value)
        self.assertTrue(isinstance(wrapped, str) and wrapped.startswith("data:image"))
        self.assertIsNone(self.editor.postprocess(None))


class UiBuildTests(unittest.TestCase):
    """模板 UI.py 与完整入口 web_demo.py 必须能在 gradio 3.x 下构建成功。"""

    def test_ui_hw3_demo_builds(self):
        import functions

        import UI

        self.assertIsNotNone(UI.create_demo_hw3(functions.function_hw3))

    def test_all_five_demos_build(self):
        import functions

        import UI

        factories = [UI.create_demo_hw1, UI.create_demo_hw2, UI.create_demo_hw3,
                     UI.create_demo_hw4, UI.create_demo_hw5]
        for index, factory in enumerate(factories, start=1):
            with self.subTest(hw=index):
                process = getattr(functions, "function_hw%d" % index)
                self.assertIsNotNone(factory(process))

    def test_web_demo_main_launches(self):
        import web_demo

        with mock.patch.object(gr.Blocks, "launch") as launch:
            web_demo.main()
        self.assertTrue(launch.called)
        self.assertEqual(launch.call_args.kwargs.get("server_port"), 8088)

if __name__ == "__main__":
    unittest.main(verbosity=2)
