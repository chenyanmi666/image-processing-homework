"""作业1 改动范围契约测试：刻意改动的只有作业1，作业2~5 必须与 `main` 基线逐字节一致。

背景：`AGENTS.md` 原判定标准是 `git diff main -- UI.py functions.py` 必须为空
（模板基线字节保真）。作业1 扩展（官方 cv2 HLS 模式、对比实验按钮）经用户批准后
必然修改这两个文件的**作业1 相关部分**，因此判定标准细化为：

1. `UI.py` / `functions.py` 的**作业2~5 函数体**必须与 `main` 基线逐字节一致；
2. 作业1 的改动必须确实存在（5 个模式、对比实验接线），而不是"哪都没改"；
3. `UI.py` 仍为 GBK + CRLF、无 BOM（编码契约不能被破坏）。

基线文本用 `git show main:UI.py` 现场读取；本机没有 git 或没有 `main` 时 SKIP。

用法（仓库根目录）：
    python tests/test_hw1_ui_contract.py
    python -m unittest discover -s tests
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

HW1_MODES = ("色相/饱和度",
             "色相/饱和度 (官方cv2 HLS)",
             "自然饱和度 (PS vibrance)",
             "亮度/对比度",
             "亮度/对比度 (PS风格)")


def baseline_text(relative_path):
    """读取 `main` 分支上的文件文本（按 GBK 解码）；失败返回 None。"""
    try:
        result = subprocess.run(["git", "show", "main:%s" % relative_path],
                                cwd=str(ROOT), capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.decode("gbk", "replace")


def top_level_defs(text):
    """把模块级 `def` 切成 {函数名: 函数源码}（直到下一个模块级 def）。"""
    defs = {}
    current = None
    buffer = []
    for line in text.split("\n"):
        if line.startswith("def "):
            if current is not None:
                defs[current] = "\n".join(buffer)
            current = line[4:].split("(", 1)[0].strip()
            buffer = [line]
        elif current is not None:
            buffer.append(line)
    if current is not None:
        defs[current] = "\n".join(buffer)
    return defs


class EncodingContractTests(unittest.TestCase):
    """UI.py 必须仍是 GBK + CRLF + 无 BOM（模板编码契约）。"""

    def setUp(self):
        self.raw = (ROOT / "UI.py").read_bytes()

    def test_no_bom_and_gbk_decodable(self):
        self.assertFalse(self.raw.startswith(b"\xef\xbb\xbf"), "UI.py 不得出现 UTF-8 BOM")
        self.assertNotIn(b"\xef\xbb\xbf", self.raw[:8])
        self.raw.decode("gbk")     # 解不出来会直接抛异常

    def test_crlf_only(self):
        self.assertGreater(self.raw.count(b"\r\n"), 0)
        self.assertEqual(self.raw.count(b"\n"), self.raw.count(b"\r\n"),
                         "UI.py 必须全为 CRLF，不能混入裸 LF")

    def test_functions_py_crlf_only(self):
        raw = (ROOT / "functions.py").read_bytes()
        self.assertEqual(raw.count(b"\n"), raw.count(b"\r\n"))
        raw.decode("gbk")


class BaselineScopeTests(unittest.TestCase):
    """作业2~5 不允许被改动；作业1 必须确实改过。"""

    @classmethod
    def setUpClass(cls):
        cls.ui_now = (ROOT / "UI.py").read_bytes().decode("gbk", "replace")
        cls.fn_now = (ROOT / "functions.py").read_bytes().decode("gbk", "replace")
        cls.ui_base = baseline_text("UI.py")
        cls.fn_base = baseline_text("functions.py")
        if cls.ui_base is None or cls.fn_base is None:
            raise unittest.SkipTest("无法读取 main 基线（缺少 git 或 main 分支），跳过范围比对")

    def test_ui_hw2_to_hw5_bodies_are_byte_identical_to_baseline(self):
        now = top_level_defs(self.ui_now)
        base = top_level_defs(self.ui_base)
        for name in ("create_demo_hw2", "create_demo_hw3", "create_demo_hw4", "create_demo_hw5"):
            with self.subTest(function=name):
                self.assertIn(name, now)
                self.assertIn(name, base)
                self.assertEqual(now[name], base[name], "%s 的作业2~5 业务逻辑不得改动" % name)

    def test_functions_hw2_to_hw5_bodies_are_byte_identical_to_baseline(self):
        now = top_level_defs(self.fn_now)
        base = top_level_defs(self.fn_base)
        for name in ("function_hw2", "function_hw3", "function_hw4", "function_hw5"):
            with self.subTest(function=name):
                self.assertEqual(now[name], base[name], "%s 的签名/实现不得改动" % name)

    def test_ui_hw1_really_changed(self):
        self.assertNotEqual(top_level_defs(self.ui_now)["create_demo_hw1"],
                            top_level_defs(self.ui_base)["create_demo_hw1"],
                            "作业1 的界面扩展应当存在；若这里失败说明改动被回退")
        self.assertNotEqual(self.fn_now, self.fn_base)

    def test_ui_hw1_exposes_five_modes_and_compare_hook(self):
        for mode in HW1_MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, self.ui_now, "界面下拉框必须包含模式：%s" % mode)
        self.assertIn("process_compare", self.ui_now)
        self.assertIn("function_hw1_compare", (ROOT / "web_demo.py").read_text(encoding="utf-8"))

    def test_ui_hw1_keeps_compare_widgets_conditional(self):
        """对比按钮/图/文本必须是可选的后端注入：不传 process_compare 时旧界面仍可构建。"""
        self.assertIn("if process_compare is not None", self.ui_now)


if __name__ == "__main__":
    unittest.main(verbosity=2)
