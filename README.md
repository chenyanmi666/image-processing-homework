# 图像处理课程作业

基于 Python、NumPy、OpenCV 和 Gradio 的图像处理实验项目。当前已实现作业 1：图像色相、饱和度、亮度与对比度调整，并提供通道可视化、两种颜色模型的对比实验及实验报告。

## 项目状态

作业 1 的实现、测试、报告与提交包已归档到 `main`。作业 2～5 保留模板接口与占位业务逻辑；网页中出现对应页签，不表示这些作业已实现。

| 分支 / 标签 | 内容 |
| --- | --- |
| `main` | 经审查归档的作业 1 成果与项目说明 |
| [`feat/image-processing-assignment`](https://github.com/chenyanmi666/image-processing-homework/tree/feat/image-processing-assignment) | 保留原开发历史 |
| `template-baseline` | 初始模板快照，未与课程官方压缩包逐字节比对 |

## 作业 1 的功能

| 模式 | 实现方式 | 用途与边界 |
| --- | --- | --- |
| 色相/饱和度 | 按课程公式手写 HSI 变换，界面沿用“HSL”名称 | 调节色相、饱和度及强度 |
| 色相/饱和度（官方 cv2 HLS） | 实际调用 OpenCV 的 BGR↔HLS 变换 | 与手写模型对照；存在 8 位量化误差 |
| 自然饱和度（PS vibrance） | 按原始饱和度衰减增益 | 对低饱和区域施加更强增益 |
| 亮度/对比度 | 自定义线性模型 | 基础亮度与对比度调整 |
| 亮度/对比度（PS 风格） | tanh 曲线与 gamma 亮度变换 | 非线性色调调整；减对比使用正曲线的反函数 |

所有模式通过 `function_hw1(...)` 返回 7 路结果：处理图及 R、G、B、H、S、L 通道可视化。滑块松开后刷新结果；对比实验按钮生成手写模型与 OpenCV 路径的对比图及误差统计。

### 两个容易混淆的概念

- 手写模型的强度为 `I=(R+G+B)/3`，OpenCV HLS 的亮度为 `L=(max+min)/2`。它们是不同的数学定义；不能只根据 MAE 或 PSNR 判断哪一个“更准确”。对比时需区分模型差异与量化误差。
- “PS 风格”是本项目设计的近似效果。项目未使用真实 Photoshop 输出做拟合或逐像素验证，不宣称复刻 Photoshop。

色相误差按圆周最短弧计算；裁剪越界 RGB 值可能改变实际色相、饱和度和强度。

## 快速运行完成版

以下命令以 PowerShell 为例。首次获取仓库：

```powershell
git clone https://github.com/chenyanmi666/image-processing-homework.git
cd image-processing-homework
git switch main
```

已有本地工作区时，先检查未提交改动，再切换分支；不要为了运行演示重置或清理原有文件。

在独立环境中安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r submission/hw1/requirements.txt
.\.venv\Scripts\python.exe web_demo.py
```

服务启动后，在浏览器打开 <http://127.0.0.1:8088/>，进入“作业1”，上传图片并选择模式。

- 依赖为 `numpy`、`gradio`、`opencv-python`；提交包说明建议 Python 3.9+。
- 本次归档验证使用 Gradio 3.36.1。现有依赖文件未锁定版本，新安装环境不保证与历史环境完全一致。
- `gradio_compat.py` 为旧版 Gradio 补充模板所需的组件接口；不能省略。更高版本仍需实际验证，不能据兼容层推断任意版本都可运行。
- 仅体验作业 1 时，可执行 `python tests/ui_smoke_hw1.py --serve`，也可使用 `start_hw1_demo.bat`。该批处理中的旧注释早于完整程序兼容修复；完整程序入口仍为 `web_demo.py`。
- 若端口被占用，先确认占用来源，避免把旧服务误认为当前版本。

## 文件导航

以下文件和目录均在 `main` 中提供。

| 文件 / 目录 | 作用 |
| --- | --- |
| [functions.py](https://github.com/chenyanmi666/image-processing-homework/blob/main/functions.py) | 作业 1 算法与对比统计；保留其他作业接口 |
| [UI.py](https://github.com/chenyanmi666/image-processing-homework/blob/main/UI.py) | Gradio 界面和事件绑定 |
| [web_demo.py](https://github.com/chenyanmi666/image-processing-homework/blob/main/web_demo.py) | 完整演示入口 |
| [gradio_compat.py](https://github.com/chenyanmi666/image-processing-homework/blob/main/gradio_compat.py) | Gradio 组件兼容层 |
| [tests/](https://github.com/chenyanmi666/image-processing-homework/tree/main/tests) | 数组测试、接口契约、服务冒烟和浏览器渲染检查 |
| [reports/hw1/](https://github.com/chenyanmi666/image-processing-homework/tree/main/reports/hw1) | 图表、指标、HTML/PDF 报告及生成脚本 |
| [submission/hw1/](https://github.com/chenyanmi666/image-processing-homework/tree/main/submission/hw1) | 可运行提交包及其专用说明 |
| [AGENTS.md](https://github.com/chenyanmi666/image-processing-homework/blob/main/AGENTS.md) | 项目实现范围、编码和协作规则 |
| [开发日志](https://github.com/chenyanmi666/image-processing-homework/blob/main/PROJECT_LOG.md) | 阶段决策、历史验证记录与已知问题 |

阅读成果可先查看 [界面截图](https://github.com/chenyanmi666/image-processing-homework/blob/main/reports/hw1/fig_ui.png) 和 [实验指标](https://github.com/chenyanmi666/image-processing-homework/blob/main/reports/hw1/metrics.md)。

## 验证与复现

在仓库根目录、已安装依赖的环境中运行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tests/ui_smoke_hw1.py --port 8093
.\.venv\Scripts\python.exe tests/ui_smoke_web_demo.py
.\.venv\Scripts\python.exe tests/test_frontend_render.py
```

检查分别覆盖数组数值与边界、未授权业务改动、Gradio 服务响应及浏览器真实渲染。浏览器渲染检查需要本机 Edge 或 Chrome；详细前提、端口和跳过条件见 [测试说明](https://github.com/chenyanmi666/image-processing-homework/blob/main/tests/README.md)。

2026-10-19 归档前，在独立工作副本中实测通过：自动测试 128/128、作业 1 接口冒烟 23/23、完整程序冒烟 10/10、Edge 无头浏览器渲染 13/13。环境为 Python 3.12.7、NumPy 1.26.4、Gradio 3.36.1、OpenCV 4.12.0。未重新生成报告，也未重新进行人工逐项界面验收；像素级判定应以 Python 数组为准，不能用网页压缩预览代替。

## 报告与提交包

- `reports/hw1/hw1_report.pdf`：脚本生成的 9 页报告材料。
- `submission/hw1/图像处理作业1_新版实验报告_陈彦米.pdf`：提交包中的 6 页排版报告。
- 两者用途不同；正式文件清单以 [提交包说明](https://github.com/chenyanmi666/image-processing-homework/blob/main/submission/hw1/README.md) 和课程要求为准。

提交包包含算法、界面、启动入口、必需兼容层、报告与依赖说明。需要刷新时使用 `tools/make_submission.py`，再运行 `tests/test_hw1_submission.py` 检查与工作版本的一致性。报告生成脚本可能覆盖生成物，阅读现有成果无需运行它。

## 维护约定

`functions.py` 与 `UI.py` 保持 GBK 编码和 CRLF 行尾；`web_demo.py` 保持 UTF-8 和 CRLF。不要用编辑器批量转换业务文件编码。

开发先阅读 `AGENTS.md`。通过分支、阶段提交和 PR 保留历史；合并由项目负责人批准。仓库归档与课程平台提交是两个独立步骤。

范围契约测试固定对照 `template-baseline`，不再把会继续演进的 `main` 当成原始模板。下载源码压缩包时不会包含 Git 标签，需要完整 Git 克隆才能执行这类历史对照检查。
