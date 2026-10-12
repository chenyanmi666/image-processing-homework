# 作业1 提交包（图像色相/饱和度/亮度/对比度调整工具）

学号：2400013156

本目录是**最小可运行提交集**：老师要求的 3 个 Python 文件 + 1 个必需的兼容层 +
报告 PDF。所有 .py 文件都与仓库最终工作版本**逐字节一致**（无删改）。

## 1. 文件清单

| 文件 | 作用 | 是否必需 |
| --- | --- | --- |
| `functions.py` | 作业1 算法实现（`function_hw1`、`function_hw1_compare`）与作业2~5 的函数占位实现 | 必需（老师要求） |
| `UI.py` | Gradio 界面与事件绑定（`create_demo_hw1` ~ `create_demo_hw5`） | 必需（老师要求） |
| `web_demo.py` | 启动入口（含学号展示），`python web_demo.py` 即启动 | 必需（老师要求） |
| `gradio_compat.py` | gradio 3.x/4.x 兼容层：只为 4.x 组件（`ImageEditor`/`Brush`）提供等价语义 | **必需**：`web_demo.py` 第 6 行 `import gradio_compat`，缺它无法启动 |
| `hw1_report.pdf` | 作业报告（含算法、实验、界面证据与局限） | 必需（老师要求） |
| `requirements.txt` | 依赖清单 | 便于复现 |

## 2. 依赖

- Python 3.9+（实测环境：Anaconda，Python 3.x）
- `numpy`（必需）
- `gradio`（必需；本作业同时兼容 gradio 3.x 与 4.x，兼容层自动处理差异）
- `opencv-python`（**使用"色相/饱和度 (官方cv2 HLS)"模式时必需**；未安装时该模式会给出可读提示，其它 4 个模式不受影响）

安装：`pip install -r requirements.txt`

## 3. 运行

```
python web_demo.py
```

浏览器打开 `http://127.0.0.1:8088/`，在"作业1"标签页：

1. 上传图像；
2. 选择模式（共 5 个）：`色相/饱和度`（手写 HSL/HSI，课件 p72-p78）、
   `色相/饱和度 (官方cv2 HLS)`（直接调用 `cv2.COLOR_BGR2HLS`）、
   `自然饱和度 (PS vibrance)`、`亮度/对比度`、`亮度/对比度 (PS风格)`；
3. 拖动滑杆（松手即刷新）；
4. 点"进阶①：手写 HSL vs 官方 cv2 HLS 对比实验"查看两条路径的对比图与误差统计。

## 4. 关于 `style.css`

`web_demo.py` 中 `gr.Blocks(css='style.css')` 传入的是**字符串**（gradio 把 `css` 参数
当作内联 CSS 文本），仓库中并不存在 `style.css` 文件，也不影响运行，因此本提交包不提供该文件。

## 5. 关于"PS 风格"功能的真实性与局限（重要）

- `亮度/对比度 (PS风格)`：本作业**自行设计**的模拟（tanh S 曲线 + gamma 亮度），
  数学性质（中灰/端点锚定、中灰斜率解析式）可验证，但**没有**用真实 Photoshop 输出数据做拟合。
- `自然饱和度 (PS vibrance)`：本作业**自行设计**的近似算法 `gain(S)=1+amount·(1-S)²`，
  同样**没有**用真实 Photoshop 输出数据拟合。
- 本机未安装 Photoshop，**未做**与 Photoshop 实际输出的逐像素比对；
  因此全篇只写"PS 风格"，不写"复刻 PS""拟合 PS""与 PS 一致"。
- `色相/饱和度`（手写）与 `色相/饱和度 (官方cv2 HLS)` 是**两套不同的数学模型**
  （`L=(R+G+B)/3, S=1-3min/Σ` vs `L=(max+min)/2, S=(max-min)/(max+min)`），
  数值不一致不代表任何一方实现错误；对比实验把"模型差异"与"8 位量化误差"分开报告。
- 色相 H 是角度量，报告中的 H 偏差按**圆周最短弧**统计（359° 与 1° 相差 2°）；
  灰/近灰像素色相在数值上不稳定，报告中单列"双方饱和度 ≥ 0.10 的像素"口径并说明局限。

## 6. 复现实验与测试（可选，需要在完整仓库中运行）

```
python -m unittest discover -s tests          # 数组层 + 兼容层测试
python tests/ui_smoke_hw1.py --port 8093      # 界面层冒烟（真实 gradio 服务）
python tests/test_frontend_render.py          # 无头浏览器渲染
python reports/hw1/make_report.py             # 重新生成报告材料（PDF/HTML/图表）
```
