"""提交包 submission/hw1/ 的一致性守卫测试。

目的：提交给老师的目录里的 .py 必须与仓库最终工作版本**逐字节一致**，
防止"改了源码但忘了同步提交包"或"提交包里混入了额外/过期文件"。

运行方式（仓库根目录）：
    python -m unittest discover -s tests
    python tests/test_hw1_submission.py
"""
from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission" / "hw1"
REQUIRED = ["functions.py", "UI.py", "web_demo.py", "gradio_compat.py"]


class TestSubmissionPackage(unittest.TestCase):
    """老师要求的 3 个文件 + 必需兼容层 + 报告 PDF。"""

    def test_required_files_present(self):
        for name in REQUIRED:
            with self.subTest(name=name):
                self.assertTrue((SUBMISSION / name).is_file(), "提交包缺少 %s" % name)

    def test_python_files_are_byte_identical_to_working_copy(self):
        for name in REQUIRED:
            with self.subTest(name=name):
                self.assertEqual(
                    (ROOT / name).read_bytes(),
                    (SUBMISSION / name).read_bytes(),
                    "submission/hw1/%s 与工作区版本不一致，请重新运行 "
                    "python tools/make_submission.py（或 ask AI 重新生成）" % name)

    def test_report_pdf_is_present_and_identical(self):
        pdf = SUBMISSION / "hw1_report.pdf"
        self.assertTrue(pdf.is_file(), "提交包缺少报告 PDF")
        self.assertEqual(
            (ROOT / "reports" / "hw1" / "hw1_report.pdf").read_bytes(),
            pdf.read_bytes(),
            "提交包里的报告 PDF 与 reports/hw1/hw1_report.pdf 不一致")

    def test_no_extra_python_files(self):
        extra = sorted(p.name for p in SUBMISSION.glob("*.py") if p.name not in REQUIRED)
        self.assertEqual(extra, [], "提交包出现多余 Python 文件：%s" % extra)

    def test_readme_documents_dependencies(self):
        readme = SUBMISSION / "README.md"
        self.assertTrue(readme.is_file(), "提交包缺少 README.md")
        text = readme.read_text(encoding="utf-8")
        for token in ("gradio_compat.py", "web_demo.py", "requirements.txt",
                      "opencv-python", "PS 风格", "style.css"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_packaged_ui_still_exposes_five_hw1_modes(self):
        """提交包里的 UI.py 必须仍然提供作业1 的 5 个模式与对比实验接线。"""
        text = (SUBMISSION / "UI.py").read_bytes().decode("gbk")
        for mode in ("色相/饱和度", "色相/饱和度 (官方cv2 HLS)", "自然饱和度 (PS vibrance)",
                     "亮度/对比度", "亮度/对比度 (PS风格)"):
            with self.subTest(mode=mode):
                self.assertIn(mode, text)
        self.assertIn("process_compare", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
