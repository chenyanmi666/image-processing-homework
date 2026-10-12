"""提交包 submission/hw1/ 的一致性守卫测试。

目的：提交给老师的目录里的 .py 必须与仓库最终工作版本**逐字节一致**，
防止"改了源码但忘了同步提交包"或"提交包里混入了额外/过期文件"。

运行方式（仓库根目录）：
    python -m unittest discover -s tests
    python tests/test_hw1_submission.py
"""
from __future__ import annotations

import pathlib
import re
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

    def test_report_pdf_is_present_and_valid(self):
        """报告 PDF：至少一份、格式有效、未加密、页数 >= 3。

        提交包里的报告由外部排版提供（文件名可能变化），因此这里校验
        “有效性”，而不是与 reports/hw1/hw1_report.pdf 逐字节相等。
        """
        pdfs = sorted(SUBMISSION.glob("*.pdf"))
        self.assertTrue(pdfs, "提交包缺少报告 PDF")
        for pdf in pdfs:
            with self.subTest(pdf=pdf.name):
                raw = pdf.read_bytes()
                self.assertTrue(raw.startswith(b"%PDF-"), "%s 不是有效 PDF" % pdf.name)
                self.assertIn(b"%%EOF", raw[-4096:], "%s 缺少 %%EOF 结束标记" % pdf.name)
                self.assertNotIn(b"/Encrypt", raw, "%s 是加密 PDF" % pdf.name)
                pages = len(re.findall(rb"/Type\s*/Page[^s]", raw))
                self.assertGreaterEqual(pages, 3, "%s 页数过少（%d）" % (pdf.name, pages))

    def test_readme_file_list_matches_directory(self):
        """README 清单里用反引号列出的文件名必须真实存在（清单与目录不得打架）。

        只认“不含空白与路径分隔符”的反引号 token：README 里也有
        ``pip install -r requirements.txt``、``python web_demo.py`` 这类**命令行**，
        它们不是文件名，若一并纳入校验会误报。
        """
        text = (SUBMISSION / "README.md").read_text(encoding="utf-8")
        listed = set(re.findall(r"`([^`\s/]+?\.(?:py|pdf|md|txt))`", text))
        self.assertTrue(listed, "未能从 README 解析出任何文件名：断言正则可能已失效")
        missing = sorted(name for name in listed if not (SUBMISSION / name).is_file())
        self.assertEqual(missing, [],
                         "README 列出、但提交包中不存在的文件：%s" % missing)
        for name in REQUIRED:
            with self.subTest(name=name):
                self.assertIn(name, listed, "README 文件清单未列出 %s" % name)

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
