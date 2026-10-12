"""作业1 function_hw1 的数组层回归测试。

运行方式（在仓库根目录执行，任选其一）：
    python tests/test_hw1.py
    python -m unittest discover -s tests -v
    python -m pytest tests/test_hw1.py -v      （本机未安装 pytest 也可用前两条）

依赖：numpy（必需）、unittest（Python 标准库）。
未安装 gradio 时会注入最小替身，因此本套测试不需要启动网页即可运行。
注意：数组层通过不等于界面测试通过，界面仍需人工在浏览器中验证。
"""
from __future__ import annotations

import pathlib
import sys
import time
import types
import unittest
import warnings

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:  # 允许在没有 gradio 的环境中运行数组层测试
    import gradio  # noqa: F401
except Exception:  # pragma: no cover - 取决于本机是否安装 gradio
    _stub = types.ModuleType("gradio")

    class _StubError(Exception):
        def __init__(self, message="Error raised.", duration=None, **kwargs):
            super().__init__(message)

    _stub.Error = _StubError
    sys.modules.setdefault("gradio", _stub)

import functions as F  # noqa: E402

HUE_SAT = "色相/饱和度"
BRIGHT_CONTRAST = "亮度/对比度"


def hw1(img, mode=HUE_SAT, h=0.0, s=0.0, l=0.0, b=0.0, c=0.0):
    """按 UI.py 的参数顺序调用 function_hw1。"""
    return F.function_hw1(img, mode, h, s, l, b, c)


def solid(color, size=16):
    img = np.zeros((size, size, 3), dtype=np.uint8)
    img[:, :] = color
    return img


def gradient_image(h=32, w=32):
    """构造一张同时含有多种色相/饱和度的测试图。"""
    yy, xx = np.mgrid[0:h, 0:w]
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:, :, 0] = xx * 255 // max(w - 1, 1)
    img[:, :, 1] = yy * 255 // max(h - 1, 1)
    img[:, :, 2] = (xx + yy) * 255 // max(h + w - 2, 1)
    return img


def legacy_hsi_to_rgb(hsi):
    """旧实现：对全图套用三段公式，再用 np.where 选择（仅用于回归比对）。"""
    h = np.mod(hsi[:, :, 0], 360.0)
    s = np.clip(hsi[:, :, 1], 0.0, 1.0)
    i = np.clip(hsi[:, :, 2], 0.0, 1.0)

    def ratio(deg):
        return s * np.cos(np.radians(deg)) / np.cos(np.radians(60.0 - deg))

    seg1 = (h >= 0.0) & (h < 120.0)
    seg2 = (h >= 120.0) & (h < 240.0)

    b_r = i * (1.0 - s)
    r_r = i * (1.0 + ratio(h))
    g_r = 3.0 * i - (r_r + b_r)

    r_g = i * (1.0 - s)
    g_g = i * (1.0 + ratio(h - 120.0))
    b_g = 3.0 * i - (r_g + g_g)

    g_b = i * (1.0 - s)
    b_b = i * (1.0 + ratio(h - 240.0))
    r_b = 3.0 * i - (g_b + b_b)

    r = np.where(seg1, r_r, np.where(seg2, r_g, r_b))
    g = np.where(seg1, g_r, np.where(seg2, g_g, g_b))
    b = np.where(seg1, b_r, np.where(seg2, b_g, b_b))
    return np.clip(np.dstack([r, g, b]), 0.0, 1.0)


class TestContract(unittest.TestCase):
    """接口契约：7 路输出、形状、dtype、通道一致性。"""

    def test_returns_seven_outputs_with_expected_shapes_and_dtypes(self):
        img = gradient_image()
        outs = hw1(img)
        self.assertEqual(len(outs), 7)
        self.assertEqual(outs[0].shape, img.shape)       # 结果图与原图同形状
        for arr in outs[1:]:
            self.assertEqual(arr.shape, img.shape[:2])   # R/G/B/H/S/I 分解图为 2 维
        for arr in outs:
            self.assertEqual(arr.dtype, np.uint8)

    def test_channel_views_match_output_channels(self):
        img = gradient_image()
        out, r, g, b, _, _, _ = hw1(img, HUE_SAT, h=0.3, s=0.4, l=0.2)
        for got, idx in ((r, 0), (g, 1), (b, 2)):
            self.assertTrue(np.array_equal(got, out[:, :, idx]))

    def test_h_channel_is_hue_scaled_to_0_255(self):
        img = solid((255, 0, 0))                      # 纯红 -> H = 0
        _, _, _, _, h_ch, s_ch, i_ch = hw1(img)
        self.assertEqual(int(h_ch[0, 0]), 0)
        self.assertEqual(int(s_ch[0, 0]), 255)        # 纯红 S = 1
        self.assertAlmostEqual(int(i_ch[0, 0]), 85, delta=1)   # I = 1/3


class TestIdentity(unittest.TestCase):
    """默认参数应逐像素复制原图（真恒等，不依赖短路分支）。"""

    def test_default_sliders_are_identity_in_hue_sat_mode(self):
        img = gradient_image(24, 24)
        out, *_ = hw1(img, HUE_SAT, 0.0, 0.0, 0.0, 0.0, 0.0)
        self.assertEqual(int(np.abs(out.astype(int) - img.astype(int)).max()), 0)

    def test_default_sliders_are_identity_in_brightness_contrast_mode(self):
        img = gradient_image(24, 24)
        out, *_ = hw1(img, BRIGHT_CONTRAST, 0.0, 0.0, 0.0, 0.0, 0.0)
        self.assertEqual(int(np.abs(out.astype(int) - img.astype(int)).max()), 0)


class TestHueSaturation(unittest.TestCase):

    def test_roundtrip_float_is_near_exact(self):
        img = gradient_image().astype(np.float64) / 255.0
        hsi = F._hw1_rgb_to_hsi(img)
        back = F._hw1_hsi_to_rgb(hsi)
        self.assertLess(float(np.abs(back - img).max()), 1e-10)

    def test_roundtrip_uint8_is_exact(self):
        img = gradient_image(48, 48)
        hsi = F._hw1_rgb_to_hsi(img.astype(np.float64) / 255.0)
        back = np.rint(F._hw1_hsi_to_rgb(hsi) * 255.0).astype(np.uint8)
        self.assertEqual(int(np.abs(back.astype(int) - img.astype(int)).max()), 0)

    def test_hue_shift_180_turns_red_into_cyan(self):
        out, *_ = hw1(solid((255, 0, 0)), HUE_SAT, h=1.0)
        self.assertTrue(np.array_equal(out[0, 0], np.array([0, 128, 128], dtype=np.uint8)))

    def test_hue_shift_60_turns_red_into_yellow(self):
        out, *_ = hw1(solid((255, 0, 0)), HUE_SAT, h=1.0 / 3.0)
        self.assertTrue(np.array_equal(out[0, 0], np.array([128, 128, 0], dtype=np.uint8)))

    def test_hue_is_periodic_360(self):
        img = gradient_image(16, 16)
        a, *_ = hw1(img, HUE_SAT, h=1.0)               # +180 度
        b, *_ = hw1(img, HUE_SAT, h=-1.0)              # -180 度，与 +180 度相差 360 度
        self.assertEqual(int(np.abs(a.astype(int) - b.astype(int)).max()), 0)

    def test_saturation_minus_one_gives_gray(self):
        out, *_ = hw1(gradient_image(16, 16), HUE_SAT, s=-1.0)
        self.assertTrue(np.array_equal(out[:, :, 0], out[:, :, 1]))
        self.assertTrue(np.array_equal(out[:, :, 1], out[:, :, 2]))

    def test_saturation_increases_mean_saturation(self):
        img = gradient_image(24, 24)
        means = []
        for s in (-0.5, 0.0, 0.5, 1.0):
            out, *_ = hw1(img, HUE_SAT, s=s)
            hsi = F._hw1_rgb_to_hsi(out.astype(np.float64) / 255.0)
            means.append(float(hsi[:, :, 1].mean()))
        self.assertEqual(means, sorted(means))
        self.assertGreater(means[-1], means[0])

    def test_lightness_scales_intensity_multiplicatively(self):
        img = solid((100, 100, 140))     # 低饱和度，放大明度后不会触及 RGB 立方体边界
        base = F._hw1_rgb_to_hsi(img.astype(np.float64) / 255.0)[0, 0, 2]
        out, *_ = hw1(img, HUE_SAT, l=0.5)
        got = F._hw1_rgb_to_hsi(out.astype(np.float64) / 255.0)[0, 0, 2]
        self.assertAlmostEqual(got / base, 1.5, delta=0.02)

    def test_lightness_minus_one_gives_black(self):
        out, *_ = hw1(solid((200, 100, 50)), HUE_SAT, l=-1.0)
        self.assertEqual(int(out.max()), 0)


class TestBrightnessContrast(unittest.TestCase):

    def test_brightness_is_linear(self):
        img = solid((100, 120, 140))
        out, *_ = hw1(img, BRIGHT_CONTRAST, b=0.2)
        expect = np.clip(np.rint((img.astype(np.float64) / 255.0 + 0.2) * 255.0), 0, 255)
        self.assertTrue(np.array_equal(out.astype(np.float64), expect))

    def test_contrast_minus_one_gives_128_gray(self):
        out, *_ = hw1(gradient_image(16, 16), BRIGHT_CONTRAST, c=-1.0)
        self.assertTrue(np.array_equal(out, np.full(out.shape, 128, dtype=np.uint8)))

    def test_contrast_is_applied_before_brightness(self):
        img = solid((100, 120, 140))
        out, *_ = hw1(img, BRIGHT_CONTRAST, b=0.1, c=0.5)
        base = img.astype(np.float64) / 255.0
        expect = np.clip(np.rint(((base - 0.5) * 1.5 + 0.5 + 0.1) * 255.0), 0, 255)
        self.assertTrue(np.array_equal(out.astype(np.float64), expect))

    def test_brightness_and_contrast_do_not_change_hue(self):
        img = solid((255, 0, 0))
        out, *_ = hw1(img, BRIGHT_CONTRAST, b=0.0, c=-0.5)
        self.assertLess(int(out[0, 0, 1]), int(out[0, 0, 0]))   # 仍以红色为主导


class TestInverseSegments(unittest.TestCase):
    """HSI 逆变换的分段实现：与旧实现等价，但不对无效分段求值。"""

    def test_matches_legacy_reference_on_full_hue_sweep(self):
        hue = np.linspace(0.0, 360.0, 721)[:-1]
        sat = np.tile(np.array([0.0, 0.25, 0.5, 0.75, 1.0]), 144)
        val = np.tile(np.array([0.0, 0.1, 0.5, 0.9, 1.0]), 144)
        hsi = np.dstack([hue, sat, val]).astype(np.float64)
        new = F._hw1_hsi_to_rgb(hsi)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")          # 旧实现会产生除零/溢出警告
            old = legacy_hsi_to_rgb(hsi)
        self.assertTrue(np.array_equal(new, old), "分段实现与旧实现结果不一致")

    def test_only_matching_segment_is_evaluated(self):
        """探针验证：旧实现会对全图计算三段，新实现只计算命中段。"""
        for hue, expected_seg in ((60.0, 1), (180.0, 2), (300.0, 3)):
            seen = []
            original_cos = np.cos

            def spy(x, _seen=seen, _cos=original_cos):
                _seen.append(np.ravel(np.asarray(x, dtype=np.float64)).copy())
                return _cos(x)

            np.cos = spy
            try:
                F._hw1_hsi_to_rgb(
                    np.array([[[hue, 1.0, 0.5]]], dtype=np.float64))
            finally:
                np.cos = original_cos

            angles = np.concatenate(seen)
            self.assertGreater(angles.size, 0, "未捕获到 cos 调用，探针失效")
            self.assertTrue(
                np.all((angles >= 0.0) & (angles < 120.0)),
                "hue=%s（第 %d 段）时对无效分段求值，角度=%s"
                % (hue, expected_seg, np.unique(angles)))

    def test_no_runtime_warnings_on_full_hue_sweep(self):
        hue = np.linspace(0.0, 360.0, 721)[:-1]
        hsi = np.dstack([hue, np.full_like(hue, 1.0), np.full_like(hue, 0.5)])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            F._hw1_hsi_to_rgb(hsi)
        runtime = [w for w in caught if issubclass(w.category, RuntimeWarning)]
        self.assertEqual([str(w.message) for w in runtime], [])

    def test_outputs_stay_finite_and_in_range(self):
        hue = np.linspace(0.0, 360.0, 721)[:-1]
        hsi = np.dstack([hue, np.full_like(hue, 1.0), np.full_like(hue, 1.0)])
        out = F._hw1_hsi_to_rgb(hsi)
        self.assertTrue(np.isfinite(out).all())
        self.assertGreaterEqual(float(out.min()), 0.0)
        self.assertLessEqual(float(out.max()), 1.0)

    def test_single_segment_images(self):
        """整幅图落在同一分段时也应全部被填充（掩码分支覆盖）。"""
        for hue in (30.0, 150.0, 270.0):
            hsi = np.full((8, 8, 3), 0.0)
            hsi[:, :, 0] = hue
            hsi[:, :, 1] = 0.5
            hsi[:, :, 2] = 0.5
            out = F._hw1_hsi_to_rgb(hsi)
            self.assertTrue(np.isfinite(out).all())
            self.assertGreater(float(out.std()), 0.0, "hue=%s 时整幅图未被填充" % hue)

    def test_segment_boundary_hues(self):
        """分段边界（含 0/120/240 与 360 附近）必须被正确填充。"""
        for hue in (0.0, 120.0, 240.0, 359.999999):
            hsi = np.array([[[hue, 1.0, 1.0]]], dtype=np.float64)
            out = F._hw1_hsi_to_rgb(hsi)
            self.assertTrue(np.isfinite(out).all(), "hue=%s 输出非有限值" % hue)
            self.assertGreaterEqual(float(out.min()), 0.0)
            self.assertLessEqual(float(out.max()), 1.0)
            self.assertGreater(float(out.max()), 0.0, "hue=%s 未被填充" % hue)

    def test_hue_outside_range_is_wrapped(self):
        a = F._hw1_hsi_to_rgb(np.array([[[150.0, 0.5, 0.5]]]))
        b = F._hw1_hsi_to_rgb(np.array([[[510.0, 0.5, 0.5]]]))
        c = F._hw1_hsi_to_rgb(np.array([[[-210.0, 0.5, 0.5]]]))
        self.assertTrue(np.array_equal(a, b))
        self.assertTrue(np.array_equal(a, c))


class TestInputValidation(unittest.TestCase):
    """非法输入必须给出明确的 ValueError，而不是后续索引异常。"""

    def assertRejects(self, bad, keyword=None):
        with self.assertRaises(ValueError) as ctx:
            F._hw1_as_float_rgb(bad)
        if keyword:
            self.assertIn(keyword, str(ctx.exception))

    def test_none_is_rejected(self):
        self.assertRejects(None, "None")

    def test_one_dimensional_array_is_rejected(self):
        self.assertRejects(np.zeros(12, dtype=np.uint8), "ndim=1")

    def test_four_dimensional_array_is_rejected(self):
        self.assertRejects(np.zeros((2, 2, 2, 3), dtype=np.uint8), "ndim=4")

    def test_wrong_channel_count_is_rejected(self):
        self.assertRejects(np.zeros((4, 4, 2), dtype=np.uint8), "通道数")
        self.assertRejects(np.zeros((4, 4, 5), dtype=np.uint8), "通道数")

    def test_non_numeric_dtype_is_rejected(self):
        self.assertRejects(np.array([["a", "b"], ["c", "d"]]), "dtype")

    def test_object_dtype_is_rejected(self):
        self.assertRejects(np.array([[1, 2], [3, 4]], dtype=object), "dtype")

    def test_empty_array_is_rejected(self):
        self.assertRejects(np.zeros((0, 0, 3), dtype=np.uint8), "尺寸")

    def test_error_message_reports_actual_shape_or_dtype(self):
        with self.assertRaises(ValueError) as ctx:
            F._hw1_as_float_rgb(np.zeros((5, 6, 7), dtype=np.uint8))
        msg = str(ctx.exception)
        self.assertIn("5", msg)
        self.assertIn("6", msg)

    def test_two_dimensional_gray_is_accepted(self):
        gray = np.arange(16, dtype=np.uint8).reshape(4, 4) * 16
        out = F._hw1_as_float_rgb(gray)
        self.assertEqual(out.shape, (4, 4, 3))
        self.assertEqual(out.dtype, np.float64)
        self.assertTrue(np.array_equal(out[:, :, 0], out[:, :, 1]))

    def test_single_channel_and_rgba_are_accepted(self):
        one = F._hw1_as_float_rgb(np.full((4, 4, 1), 200, dtype=np.uint8))
        self.assertEqual(one.shape, (4, 4, 3))
        rgba = np.zeros((4, 4, 4), dtype=np.uint8)
        rgba[:, :, 0] = 255
        rgba[:, :, 3] = 128
        out = F._hw1_as_float_rgb(rgba)
        self.assertEqual(out.shape, (4, 4, 3))
        self.assertEqual(float(out[:, :, 0].max()), 1.0)     # alpha 通道被丢弃

    def test_float_input_scales_by_255_when_above_one(self):
        out = F._hw1_as_float_rgb(np.full((2, 2, 3), 255.0))
        self.assertTrue(np.allclose(out, 1.0))

    def test_float_input_in_unit_range_is_kept(self):
        out = F._hw1_as_float_rgb(np.full((2, 2, 3), 0.5))
        self.assertTrue(np.allclose(out, 0.5))

    def test_bool_input_is_accepted(self):
        out = F._hw1_as_float_rgb(np.ones((2, 2, 3), dtype=bool))
        self.assertTrue(np.allclose(out, 1.0))

    def test_function_hw1_propagates_validation_error(self):
        with self.assertRaises(ValueError):
            hw1(np.zeros((4, 4, 2), dtype=np.uint8))


class TestModeBranch(unittest.TestCase):
    """mode 必须显式分支，未知模式不得静默按亮度/对比度处理。"""

    def test_unknown_mode_raises(self):
        img = gradient_image(8, 8)
        with self.assertRaises(Exception) as ctx:
            hw1(img, "不存在的模式", b=0.5)
        self.assertIn("不支持的模式", str(ctx.exception))

    def test_none_mode_raises(self):
        img = gradient_image(8, 8)
        with self.assertRaises(Exception):
            hw1(img, None, b=0.5)

    def test_brightness_contrast_mode_ignores_hue_sliders(self):
        img = gradient_image(16, 16)
        a, *_ = hw1(img, BRIGHT_CONTRAST, h=1.0, s=1.0, l=1.0)
        b, *_ = hw1(img, BRIGHT_CONTRAST, h=0.0, s=0.0, l=0.0)
        self.assertTrue(np.array_equal(a, b))

    def test_both_known_modes_return_uint8(self):
        img = gradient_image(8, 8)
        for mode in (HUE_SAT, BRIGHT_CONTRAST):
            out, *_ = hw1(img, mode, 0.2, 0.2, 0.2, 0.2, 0.2)
            self.assertEqual(out.dtype, np.uint8)


class TestEdgeAndPerformance(unittest.TestCase):

    def test_extreme_images_are_handled(self):
        for color in ((0, 0, 0), (255, 255, 255), (128, 128, 128), (255, 0, 0)):
            for mode in (HUE_SAT, BRIGHT_CONTRAST):
                for h in (-1.0, 0.0, 1.0):
                    out, *_ = hw1(solid(color, 8), mode, h=h, s=h, l=h, b=h, c=h)
                    self.assertTrue(np.isfinite(out.astype(np.float64)).all())

    def test_single_pixel_image(self):
        out, *_ = hw1(solid((10, 200, 30), 1), HUE_SAT, h=0.25)
        self.assertEqual(out.shape, (1, 1, 3))

    def test_512_image_is_fast_enough(self):
        img = gradient_image(512, 512)
        start = time.time()
        hw1(img, HUE_SAT, h=0.2, s=0.3, l=0.1)
        elapsed = time.time() - start
        print("  512x512 elapsed: %.3f s" % elapsed)
        self.assertLess(elapsed, 5.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
