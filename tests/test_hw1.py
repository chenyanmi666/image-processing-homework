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
import re
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
OFFICIAL_HLS = "色相/饱和度 (官方cv2 HLS)"
VIBRANCE = "自然饱和度 (PS vibrance)"
BRIGHT_CONTRAST = "亮度/对比度"
PS_TONE = "亮度/对比度 (PS风格)"
ALL_MODES = (HUE_SAT, OFFICIAL_HLS, VIBRANCE, BRIGHT_CONTRAST, PS_TONE)


def require_cv2(case):
    """官方路径依赖 OpenCV；缺失时跳过而不是失败（并留下可见提示）。"""
    try:
        import cv2
    except ImportError:
        case.skipTest("本机未安装 OpenCV(cv2)，跳过官方 HLS 路径测试")
    else:
        return cv2


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


class TestOfficialCv2HlsPath(unittest.TestCase):
    """基本信息（60 分档）：直接调用 cv2.COLOR_BGR2HLS 的官方路径。

    课件定义与 OpenCV 定义是**两套不同的数学模型**：
      课件(p72-p78)：L = (R+G+B)/3,  S = 1 - 3*min/(R+G+B)
      OpenCV HLS   ：L = (max+min)/2, S = (max-min)/(max+min)
    因此这里既验证官方路径自身的行为，也固定"两者数值本来就不同"这一事实。
    """

    def test_all_five_modes_return_seven_uint8_outputs(self):
        img = gradient_image(8, 12)
        for mode in ALL_MODES:
            with self.subTest(mode=mode):
                outs = hw1(img, mode, 0.2, 0.3, 0.1, 0.2, 0.3)
                self.assertEqual(len(outs), 7)
                out, r, g, b, h, s, l = outs
                self.assertEqual(out.shape, (8, 12, 3))
                for ch in (r, g, b, h, s, l):
                    self.assertEqual(ch.shape, (8, 12))
                for arr in outs:
                    self.assertEqual(arr.dtype, np.uint8)

    def test_official_space_uses_max_min_definition(self):
        require_cv2(self)
        red = F._hw1_rgb_to_hls_opencv(np.array([[[1.0, 0.0, 0.0]]]))
        self.assertAlmostEqual(float(red[0, 0, 2]), 128.0 / 255.0, places=3)   # L=(255+0)/2
        self.assertAlmostEqual(float(red[0, 0, 1]), 1.0, places=3)             # S=(max-min)/(max+min)
        self.assertAlmostEqual(float(red[0, 0, 0]), 0.0, places=3)             # H=0

    def test_manual_space_uses_mean_definition_and_differs(self):
        require_cv2(self)
        red_f = np.array([[[1.0, 0.0, 0.0]]])
        manual = F._hw1_rgb_to_hsi(red_f)
        official = F._hw1_rgb_to_hls_opencv(red_f)
        self.assertAlmostEqual(float(manual[0, 0, 2]), 1.0 / 3.0, places=3)    # L=(R+G+B)/3
        self.assertGreater(abs(float(manual[0, 0, 2] - official[0, 0, 2])), 0.15,
                           "两套 L 定义必须给出不同数值，否则说明实现退化成了同一个模型")

    def test_gray_agrees_because_two_models_coincide(self):
        require_cv2(self)
        gray_f = np.full((1, 1, 3), 128.0 / 255.0)
        self.assertAlmostEqual(float(F._hw1_rgb_to_hsi(gray_f)[0, 0, 2]),
                               float(F._hw1_rgb_to_hls_opencv(gray_f)[0, 0, 2]), places=3)

    def test_official_identity_is_within_one_quantization_level(self):
        require_cv2(self)
        img = gradient_image(32, 32)
        out, *_ = hw1(img, OFFICIAL_HLS)
        stats = F._hw1_error_stats(img, out)
        self.assertLessEqual(stats["max"], 1.0, "默认参数的官方路径往返误差应只有 8 位量化(<=1 LSB)")
        self.assertLess(stats["mae"], 0.5)

    def test_manual_identity_is_exact(self):
        img = gradient_image(32, 32)
        out, *_ = hw1(img, HUE_SAT)
        self.assertTrue(np.array_equal(out, img), "手写路径在浮点域往返，默认参数必须逐像素相等")

    def test_official_hue_180_turns_red_into_cyan(self):
        require_cv2(self)
        out, *_ = hw1(solid((255, 0, 0)), OFFICIAL_HLS, h=1.0)
        r, g, b = (int(v) for v in out[0, 0])
        self.assertLess(r, 8)
        self.assertGreater(g, 247)
        self.assertGreater(b, 247)

    def test_official_hue_is_periodic_over_360(self):
        require_cv2(self)
        img = gradient_image(8, 8)
        plus, *_ = hw1(img, OFFICIAL_HLS, h=1.0)
        minus, *_ = hw1(img, OFFICIAL_HLS, h=-1.0)
        self.assertTrue(np.array_equal(plus, minus))

    def test_official_saturation_minus_one_gives_gray(self):
        require_cv2(self)
        out, *_ = hw1(solid((255, 0, 0)), OFFICIAL_HLS, s=-1.0)
        pixel = out[0, 0].astype(np.int32)
        self.assertLessEqual(int(pixel.max() - pixel.min()), 1)
        self.assertLess(abs(int(pixel.mean()) - 128), 3)

    def test_official_lightness_minus_one_gives_black(self):
        require_cv2(self)
        out, *_ = hw1(solid((255, 0, 0)), OFFICIAL_HLS, l=-1.0)
        self.assertEqual(int(out.max()), 0)

    def test_official_saturation_is_monotone(self):
        require_cv2(self)
        img = solid((200, 120, 120), 8)
        spreads = []
        for s in (-0.5, 0.0, 0.5, 1.0):
            out, *_ = hw1(img, OFFICIAL_HLS, s=s)
            pixel = out[0, 0].astype(np.int32)
            spreads.append(int(pixel.max() - pixel.min()))
        self.assertEqual(spreads, sorted(spreads))
        self.assertLess(spreads[0], spreads[-1])


class TestVibrance(unittest.TestCase):
    """进阶③：PS 风格自然饱和度 gain(S) = 1 + amount*(1-S)^2。"""

    def test_zero_amount_is_identity(self):
        sat = np.linspace(0.0, 1.0, 32).reshape(1, -1)
        self.assertTrue(np.array_equal(F._hw1_apply_vibrance(sat, 0.0), sat))

    def test_gain_decreases_with_saturation(self):
        sat = np.array([[[0.2, 0.5, 0.8, 1.0]]])
        gains = [float(v) for v in (F._hw1_apply_vibrance(sat, 1.0) / sat)[0, 0]]
        self.assertEqual(gains, sorted(gains, reverse=True), "低饱和像素必须获得更大增益")
        self.assertGreater(gains[0], 1.5)
        self.assertAlmostEqual(gains[-1], 1.0, places=6, msg="纯色不能被改动")

    def test_gain_is_bounded_by_amount(self):
        sat = np.array([[[0.1, 0.3, 0.6, 0.9]]])
        for amount in (0.25, 0.5, 1.0):
            gains = F._hw1_apply_vibrance(sat, amount) / sat
            self.assertLessEqual(float(gains.max()), 1.0 + amount + 1e-9)

    def test_gray_and_pure_color_are_untouched(self):
        for color in ((128, 128, 128), (255, 0, 0), (255, 255, 255)):
            with self.subTest(color=color):
                out, *_ = hw1(solid(color, 8), VIBRANCE, s=1.0)
                self.assertTrue(np.array_equal(out, solid(color, 8)),
                                "%s 的 S 已在边界，自然饱和度不得改变它" % (color,))

    def test_negative_amount_reduces_colourfulness(self):
        img = solid((200, 120, 120), 8)
        base = hw1(img, VIBRANCE, s=0.0)[0][0, 0].astype(np.int32)
        down = hw1(img, VIBRANCE, s=-1.0)[0][0, 0].astype(np.int32)
        self.assertLess(int(down.max() - down.min()), int(base.max() - base.min()))

    def test_output_is_monotone_in_amount(self):
        img = solid((190, 150, 140), 8)
        spreads = []
        for amount in (-1.0, -0.5, 0.0, 0.5, 1.0):
            pixel = hw1(img, VIBRANCE, s=amount)[0][0, 0].astype(np.int32)
            spreads.append(int(pixel.max() - pixel.min()))
        self.assertEqual(spreads, sorted(spreads))

    def test_mode_ignores_hue_and_lightness_sliders(self):
        img = gradient_image(12, 12)
        a, *_ = hw1(img, VIBRANCE, h=1.0, s=0.6, l=1.0)
        b, *_ = hw1(img, VIBRANCE, h=-1.0, s=0.6, l=-1.0)
        self.assertTrue(np.array_equal(a, b))

    def test_differs_from_plain_saturation_scaling(self):
        img = solid((190, 150, 140), 8)
        vibe, *_ = hw1(img, VIBRANCE, s=0.5)
        plain, *_ = hw1(img, HUE_SAT, s=0.5)
        self.assertFalse(np.array_equal(vibe, plain),
                         "自然饱和度不能等同于整体饱和度线性缩放，否则不算独立进阶功能")

    def test_channel_maps_match_result(self):
        img = gradient_image(8, 8)
        out, r, g, b, h, s, l = hw1(img, VIBRANCE, s=0.4)
        self.assertTrue(np.array_equal(r, out[:, :, 0]))
        expected_l = np.clip(np.rint(
            F._hw1_rgb_to_hsi(out.astype(np.float64) / 255.0)[:, :, 2] * 255.0), 0, 255).astype(np.uint8)
        self.assertTrue(np.array_equal(l, expected_l))


class TestPsStyleTone(unittest.TestCase):
    """进阶②：PS 风格亮度/对比度（tanh S 曲线 + gamma 亮度，端点与中灰锚定）。

    诚实声明：本机没有 Photoshop，**未做**与 PS 实际输出的逐像素比对，
    因此这里验证的是本实现自洽的数学性质（锚点、单调性、解析斜率、标定残差），
    而不是"与 PS 一致"。
    """

    def test_zero_parameters_are_identity(self):
        img = gradient_image(16, 16)
        out, *_ = hw1(img, PS_TONE, b=0.0, c=0.0)
        self.assertTrue(np.array_equal(out, img))

    def test_black_and_white_endpoints_are_fixed(self):
        for brightness, contrast in ((0.7, 0.8), (-0.7, -0.8), (1.0, 1.0)):
            with self.subTest(brightness=brightness, contrast=contrast):
                black, *_ = hw1(solid((0, 0, 0), 4), PS_TONE, b=brightness, c=contrast)
                white, *_ = hw1(solid((255, 255, 255), 4), PS_TONE, b=brightness, c=contrast)
                self.assertEqual(int(black.max()), 0, "黑色端点必须保持为 0")
                self.assertEqual(int(white.min()), 255, "白色端点必须保持为 255")

    def test_mid_gray_is_anchored(self):
        gray = solid((128, 128, 128), 4)
        for contrast in (-1.0, 0.0, 1.0):
            out, *_ = hw1(gray, PS_TONE, b=0.0, c=contrast)
            self.assertLessEqual(abs(int(out[0, 0, 0]) - 128), 2)

    def test_contrast_steepens_mid_slope_and_matches_numeric_derivative(self):
        h = 1e-6
        for contrast in (-1.0, -0.5, 0.0, 0.5, 1.0):
            a = F._hw1_ps_contrast_a(contrast)
            numeric = float(F._hw1_ps_s_curve(np.array([0.5 + h]), a)[0]
                            - F._hw1_ps_s_curve(np.array([0.5 - h]), a)[0]) / (2 * h)
            self.assertAlmostEqual(numeric, F._hw1_ps_mid_slope(contrast), places=4)
        self.assertAlmostEqual(F._hw1_ps_mid_slope(0.0), 1.0, places=9)
        self.assertGreater(F._hw1_ps_mid_slope(1.0), F._hw1_ps_mid_slope(0.5))
        self.assertGreater(F._hw1_ps_mid_slope(0.5), F._hw1_ps_mid_slope(0.0))
        self.assertLess(F._hw1_ps_mid_slope(-0.5), 1.0)
        self.assertLess(F._hw1_ps_mid_slope(-1.0), F._hw1_ps_mid_slope(-0.5))

    def test_negative_contrast_is_not_a_copy_of_positive_contrast(self):
        """回归防护：s 曲线公式对 a 是偶函数，直接代入 a<0 会与 a>0 完全相同。"""
        x = np.linspace(0.0, 1.0, 33)
        positive = F._hw1_ps_s_curve(x, 4.0)
        negative = F._hw1_ps_s_curve(x, -4.0)
        self.assertFalse(np.allclose(positive, negative), "减对比必须真的把曲线压平")
        self.assertTrue(np.allclose(F._hw1_ps_s_curve(x, 4.0), 2.0 * 0.5 - F._hw1_ps_s_curve(1.0 - x, 4.0)))

    def test_negative_contrast_compresses_towards_mid_gray(self):
        quarter, *_ = hw1(solid((64, 64, 64), 4), PS_TONE, c=-1.0)
        three_quarters, *_ = hw1(solid((192, 192, 192), 4), PS_TONE, c=-1.0)
        self.assertGreater(int(quarter[0, 0, 0]), 64, "减对比应把暗部拉向中灰")
        self.assertLess(int(three_quarters[0, 0, 0]), 192, "减对比应把亮部拉向中灰")
        mid, *_ = hw1(solid((128, 128, 128), 4), PS_TONE, c=-1.0)
        self.assertLessEqual(abs(int(mid[0, 0, 0]) - 128), 2)

    def test_calibration_residual_grows_with_target_slope(self):
        residuals = []
        for target in (1.2, 1.5, 2.0):
            a_fit, rms, max_err = F._hw1_ps_fit_contrast_a(target)
            self.assertLessEqual(a_fit, 4.0 + 1e-9, "斜率参数必须落在设计上限内")
            self.assertLessEqual(rms, max_err)
            residuals.append(rms)
        self.assertEqual(residuals, sorted(residuals))
        a_zero, rms_zero, _ = F._hw1_ps_fit_contrast_a(1.0)
        self.assertAlmostEqual(a_zero, 0.0, places=6)
        self.assertAlmostEqual(rms_zero, 0.0, places=9)

    def test_calibration_handles_target_slopes_below_one(self):
        a_fit, rms, max_err = F._hw1_ps_fit_contrast_a(0.8)
        self.assertLess(a_fit, 0.0, "目标中灰斜率小于 1 时必须拟合出负的 a（减对比）")
        self.assertLessEqual(rms, 0.05)
        self.assertLessEqual(max_err, 0.11)
        a_flat, _, _ = F._hw1_ps_fit_contrast_a(0.6)
        self.assertAlmostEqual(a_flat, -4.0, places=6, msg="低于可达下限的目标斜率应停在上限 a=-4")


    def test_full_contrast_does_not_clip_midtones(self):
        quarter, *_ = hw1(solid((64, 64, 64), 4), PS_TONE, c=1.0)
        three_quarters, *_ = hw1(solid((192, 192, 192), 4), PS_TONE, c=1.0)
        self.assertGreater(int(quarter.min()), 0, "S 曲线不应把 1/4 灰压到纯黑")
        self.assertLess(int(three_quarters.max()), 255, "S 曲线不应把 3/4 灰顶到纯白")
        self.assertLess(int(quarter[0, 0, 0]), 64)
        self.assertGreater(int(three_quarters[0, 0, 0]), 192)

    def test_brightness_is_gamma_and_monotone(self):
        values = []
        for brightness in (-1.0, -0.5, 0.0, 0.5, 1.0):
            out, *_ = hw1(solid((64, 64, 64), 4), PS_TONE, b=brightness, c=0.0)
            values.append(int(out[0, 0, 0]))
        self.assertEqual(values, sorted(values), "亮度必须单调")
        x = np.linspace(0.0, 1.0, 64).reshape(1, -1, 1)
        x = np.repeat(x, 3, axis=2)
        gamma = 2.0 ** (-2.0 * 0.5)
        self.assertTrue(np.allclose(F._hw1_ps_brightness_contrast(x, 0.5, 0.0), x ** gamma))

    def test_brightness_lifts_shadows_more_than_highlights(self):
        dark, *_ = hw1(solid((64, 64, 64), 4), PS_TONE, b=1.0)
        bright, *_ = hw1(solid((224, 224, 224), 4), PS_TONE, b=1.0)
        self.assertGreater(int(dark[0, 0, 0]) - 64, int(bright[0, 0, 0]) - 224)

    def test_calibration_residual_grows_with_target_slope(self):
        residuals = []
        for target in (1.2, 1.5, 2.0):
            a_fit, rms, max_err = F._hw1_ps_fit_contrast_a(target)
            self.assertLessEqual(a_fit, 4.0 + 1e-9, "斜率参数必须落在设计上限内")
            self.assertLessEqual(rms, max_err)
            residuals.append(rms)
        self.assertEqual(residuals, sorted(residuals))
        a_zero, rms_zero, _ = F._hw1_ps_fit_contrast_a(1.0)
        self.assertAlmostEqual(a_zero, 0.0, places=6)
        self.assertAlmostEqual(rms_zero, 0.0, places=9)

    def test_differs_from_linear_model(self):
        img = gradient_image(32, 32)
        ps_out, *_ = hw1(img, PS_TONE, b=0.3, c=0.5)
        linear, *_ = hw1(img, BRIGHT_CONTRAST, b=0.3, c=0.5)
        stats = F._hw1_error_stats(linear, ps_out)
        self.assertGreater(stats["mae"], 10.0, "PS 风格必须与线性模型有实质差异，否则是重复实现")

    def test_ignores_hue_sliders(self):
        img = gradient_image(12, 12)
        a, *_ = hw1(img, PS_TONE, h=1.0, s=1.0, l=1.0, b=0.2, c=0.4)
        b, *_ = hw1(img, PS_TONE, h=-1.0, s=-1.0, l=-1.0, b=0.2, c=0.4)
        self.assertTrue(np.array_equal(a, b))


class TestCompareExperiment(unittest.TestCase):
    """进阶①：手写 HSL(课件定义) vs 官方 cv2 HLS 的对比实验与误差统计。"""

    def test_error_stats_does_not_wrap_around(self):
        a = np.zeros((2, 2, 3), dtype=np.uint8)
        b = np.full((2, 2, 3), 255, dtype=np.uint8)
        self.assertEqual(int(F._hw1_abs_diff(a, b).max()), 255)
        stats = F._hw1_error_stats(a, b)
        self.assertAlmostEqual(stats["mae"], 255.0)
        self.assertLessEqual(stats["psnr"], 0.1, "误差全为 255 时 PSNR 应为 0 dB（下限）")

    def test_error_stats_of_identical_images_is_zero_mae_and_infinite_psnr(self):
        img = gradient_image(8, 8)
        stats = F._hw1_error_stats(img, img)
        self.assertEqual(stats["mae"], 0.0)
        self.assertEqual(stats["max"], 0.0)
        self.assertEqual(stats["psnr"], float("inf"))

    def test_side_by_side_geometry_and_padding(self):
        a = np.full((4, 4, 3), 10, dtype=np.uint8)
        b = np.full((6, 4, 3), 20, dtype=np.uint8)
        joined = F._hw1_side_by_side([a, b], gap=2)
        self.assertEqual(joined.shape, (6, 4 + 2 + 4, 3))
        self.assertTrue(np.all(joined[4:, 0:4] == 255), "较矮的图底部应补白")

    def test_hue_angle_delta_is_circular(self):
        """色相差必须是圆周最短弧：359° 与 1° 相差 2°，不是 358°。"""
        self.assertAlmostEqual(float(F._hw1_hue_angle_delta(359.0, 1.0)), 2.0, places=9)
        self.assertAlmostEqual(float(F._hw1_hue_angle_delta(1.0, 359.0)), 2.0, places=9)
        self.assertAlmostEqual(float(F._hw1_hue_angle_delta(0.0, 359.0)), 1.0, places=9)
        self.assertAlmostEqual(float(F._hw1_hue_angle_delta(0.0, 180.0)), 180.0, places=9)
        self.assertAlmostEqual(float(F._hw1_hue_angle_delta(350.0, 10.0)), 20.0, places=9)
        self.assertAlmostEqual(float(F._hw1_hue_angle_delta(90.0, 270.0)), 180.0, places=9)
        # 跨 0/360 的数组形式必须逐像素取最短弧
        delta = F._hw1_hue_angle_delta(np.array([359.0, 0.0, 10.0]),
                                       np.array([1.0, 180.0, 350.0]))
        self.assertTrue(np.allclose(delta, [2.0, 180.0, 20.0]))

    def test_hue_angle_delta_is_symmetric_and_bounded(self):
        rng = np.random.default_rng(20241012)
        a = rng.uniform(0.0, 360.0, 256)
        b = rng.uniform(0.0, 360.0, 256)
        delta = F._hw1_hue_angle_delta(a, b)
        self.assertTrue(np.allclose(delta, F._hw1_hue_angle_delta(b, a)), "角距离必须对称")
        self.assertGreaterEqual(float(delta.min()), 0.0)
        self.assertLessEqual(float(delta.max()), 180.0, "最短弧角距离不可能超过 180°")
        naive = np.abs(np.mod(a, 360.0) - np.mod(b, 360.0))
        self.assertTrue(np.allclose(delta, np.minimum(naive, 360.0 - naive)))
        # 直接相减的口径在跨界时会高估，最短弧必须 <= 直接相减
        self.assertLessEqual(float(delta.mean()), float(naive.mean()) + 1e-9)

    def test_compare_report_hue_distance_is_circular(self):
        """集成检查：报告中 H 一行的数值必须等于按最短弧重算的结果。"""
        require_cv2(self)
        img = gradient_image(24, 32)
        h_slider, s_slider, l_slider = 0.0, 0.5, 0.0
        _, text = F.function_hw1_compare(img, h_slider, s_slider, l_slider)
        img_f = img.astype(np.float64) / 255.0
        manual = F._hw1_to_uint8(F._hw1_adjust_in_hsi(img_f, h_slider, s_slider, l_slider))
        official = F._hw1_to_uint8(F._hw1_adjust_in_hls_opencv(img_f, h_slider, s_slider, l_slider))
        m_hls = F._hw1_rgb_to_hls_opencv(manual.astype(np.float64) / 255.0)
        o_hls = F._hw1_rgb_to_hls_opencv(official.astype(np.float64) / 255.0)
        expected = F._hw1_hue_angle_delta(m_hls[:, :, 0], o_hls[:, :, 0])
        match = re.search(r"H 平均角距离[^|]*\|\s*([0-9.]+)\s*度", text)
        self.assertIsNotNone(match, "报告应给出按最短弧统计的 H 平均角距离")
        self.assertAlmostEqual(float(match.group(1)), float(expected.mean()), delta=0.001)
        for token in ("最短圆弧", "最大角距离", "双方饱和度", "直接相减"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_difference_visualisation_does_not_wrap_around(self):
        """差异图 ×5 放大必须在更宽的整数类型里做，否则 uint8 会按 256 取模回绕。"""
        black = np.zeros((2, 2, 3), dtype=np.uint8)
        white = np.full((2, 2, 3), 255, dtype=np.uint8)
        raw = F._hw1_abs_diff(black, white)
        self.assertEqual(int(raw.max()), 255)
        self.assertEqual(int(raw.astype(np.int32).max() * 5), 1275,
                         "255*5 的中间值应保存在 int16/int32 中，不能已被回绕")
        vis = F._hw1_difference_vis(black, white)
        self.assertEqual(vis.dtype, np.uint8)
        self.assertTrue(np.all(vis == 255), "最大差异应饱和到 255")
        # 60*5=300：若在 uint8 上乘会回绕成 44，这里必须是饱和后的 255
        sixty = np.full((2, 2, 3), 60, dtype=np.uint8)
        self.assertTrue(np.all(F._hw1_difference_vis(black, sixty) == 255))
        # 小差异不应被裁剪
        tiny = np.full((2, 2, 3), 3, dtype=np.uint8)
        self.assertTrue(np.all(F._hw1_difference_vis(black, tiny) == 15))

    def test_compare_figure_difference_panel_uses_the_same_scaling(self):
        """对比图第 4 块面板必须就是 _hw1_difference_vis 的结果（无回绕）。"""
        require_cv2(self)
        img = gradient_image(16, 16)
        figure, _ = F.function_hw1_compare(img, 0.0, 0.5, 0.0)
        panel = figure[:, 3 * 16 + 3 * 4:, :]
        self.assertEqual(panel.shape, (16, 16, 3))
        img_f = img.astype(np.float64) / 255.0
        manual = F._hw1_to_uint8(F._hw1_adjust_in_hsi(img_f, 0.0, 0.5, 0.0))
        official = F._hw1_to_uint8(F._hw1_adjust_in_hls_opencv(img_f, 0.0, 0.5, 0.0))
        self.assertTrue(np.array_equal(panel, F._hw1_difference_vis(manual, official)))

    def test_returns_figure_and_report_text(self):
        require_cv2(self)
        figure, text = F.function_hw1_compare(gradient_image(16, 16), 0.0, 0.0, 0.0)
        self.assertEqual(figure.dtype, np.uint8)
        self.assertEqual(figure.shape[0], 16)
        self.assertEqual(figure.shape[1], 4 * 16 + 3 * 4)
        self.assertIsInstance(text, str)
        for token in ("MAE", "PSNR", "cv2", "p72", "量化", "模型差异"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_figure_panels_match_the_two_implementations(self):
        require_cv2(self)
        img = gradient_image(16, 16)
        figure, _ = F.function_hw1_compare(img, 0.0, 0.5, 0.0)
        manual = hw1(img, HUE_SAT, s=0.5)[0]
        official = hw1(img, OFFICIAL_HLS, s=0.5)[0]
        self.assertTrue(np.array_equal(figure[:, 0:16], img))
        self.assertTrue(np.array_equal(figure[:, 20:36], manual), "第 2 幅必须是手写课件定义的结果")
        self.assertTrue(np.array_equal(figure[:, 40:56], official), "第 3 幅必须是官方 cv2 HLS 的结果")

    def test_none_image_raises(self):
        with self.assertRaises(Exception) as ctx:
            F.function_hw1_compare(None, 0.0, 0.0, 0.0)
        message = str(ctx.exception)
        self.assertIn("输入一张图像", message)
        self.assertIn("处理之前", message)

    def test_identity_parameters_agree_within_one_lsb(self):
        require_cv2(self)
        stats = F._hw1_error_stats(*[hw1(gradient_image(24, 24), mode)[0]
                                     for mode in (HUE_SAT, OFFICIAL_HLS)])
        self.assertLessEqual(stats["max"], 1.0)

    def test_model_divergence_grows_with_saturation(self):
        require_cv2(self)
        img = gradient_image(24, 24)
        errors = [F._hw1_error_stats(hw1(img, HUE_SAT, s=s)[0], hw1(img, OFFICIAL_HLS, s=s)[0])["mae"]
                  for s in (0.0, 0.5, 1.0)]
        self.assertEqual(errors, sorted(errors))
        self.assertGreater(errors[-1], errors[0] * 1.5)

    def test_lightness_definition_difference_dominates(self):
        require_cv2(self)
        img = gradient_image(24, 24)
        l_err = F._hw1_error_stats(hw1(img, HUE_SAT, l=0.5)[0], hw1(img, OFFICIAL_HLS, l=0.5)[0])["mae"]
        s_err = F._hw1_error_stats(hw1(img, HUE_SAT, s=0.5)[0], hw1(img, OFFICIAL_HLS, s=0.5)[0])["mae"]
        self.assertGreater(l_err, s_err,
                           "L 定义不同((R+G+B)/3 vs (max+min)/2)带来的差异应大于 S 定义的差异")

    def test_hue_shift_is_closer_than_lightness_shift(self):
        require_cv2(self)
        img = gradient_image(24, 24)
        h_err = F._hw1_error_stats(hw1(img, HUE_SAT, h=0.5)[0], hw1(img, OFFICIAL_HLS, h=0.5)[0])["mae"]
        l_err = F._hw1_error_stats(hw1(img, HUE_SAT, l=0.5)[0], hw1(img, OFFICIAL_HLS, l=0.5)[0])["mae"]
        self.assertLess(h_err, l_err, "两套色相定义相似(仅量化不同)，差异应小于明度定义差异")


if __name__ == "__main__":
    unittest.main(verbosity=2)
