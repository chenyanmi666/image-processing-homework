# 测试说明

## 作业1：图像色相/饱和度/亮度/对比度调整工具（`function_hw1`）

测试文件：`tests/test_hw1.py`

这是**数组层**测试：直接调用 `functions.py` 中的算法函数，不启动 Gradio 服务；
未安装 gradio 时会自动注入最小替身，因此可在纯算法环境运行。

在仓库根目录执行（任选其一）：

```
python tests/test_hw1.py
python -m unittest discover -s tests -v
```

若本机已安装 pytest，也可：

```
python -m pytest tests/test_hw1.py -v
```

### 覆盖范围

| 测试类 | 覆盖内容 |
| --- | --- |
| `TestContract` | 7 路输出、形状/dtype、通道分解图与结果图一致、H 通道灰度映射 |
| `TestIdentity` | 默认滑块在两种模式下逐像素复制原图（真恒等，不依赖短路） |
| `TestHueSaturation` | 浮点/uint8 往返、色相 ±180 与 +60 锚点、360 度周期性、饱和度单调性、明度乘性模型 |
| `TestBrightnessContrast` | 亮度线性、对比度 -1 变 128 灰、先对比度后亮度 |
| `TestInverseSegments` | 分段实现与旧“全段计算 + `np.where`”实现位级一致；`np.cos` 探针证明**只对命中分段求值**；全域色相扫描无 `RuntimeWarning`、输出有限；单分段整图、分段边界色相、H 越界取模 |
| `TestInputValidation` | `None`、1 维/4 维、通道数 2/5、字符串/object dtype、空数组均抛出带实际 shape/dtype 的 `ValueError`；灰度、单通道、RGBA、bool、[0,1] 与 0-255 浮点输入被正确接受 |
| `TestModeBranch` | 未知 `mode` / `None` 抛错；亮度/对比度模式忽略色相滑块 |
| `TestEdgeAndPerformance` | 纯黑/纯白/纯灰/纯红 × 极值滑块、1 像素图、512×512 性能 |
| `TestOfficialCv2HlsPath` | 官方 `cv2.COLOR_BGR2HLS` 路径：5 个模式统一返回 7 路 uint8；OpenCV 定义 `L=(max+min)/2` 与课件定义 `L=(R+G+B)/3` 数值不同（灰色处重合）；默认参数恒等 `max ≤ 1`（8 位量化）；色相 ±180 周期性、红+180→青、S×(1-1)→灰、L×(1-1)→黑、饱和度单调性 |
| `TestVibrance` | 进阶③：amount=0 恒等、增益随 S 单调递减且 ≤1+amount、纯色/灰色/纯白完全不动、负 amount 降饱和、随 amount 单调、忽略色相/明度滑杆、结果不同于整体饱和度缩放、通道分解图与结果一致 |
| `TestPsStyleTone` | 进阶②：b=c=0 严格恒等、黑白端点固定、中灰锚定（±2）、解析中灰斜率与数值微分一致（c 从 -1 到 +1 共 5 档）、**减对比取同强度曲线的反函数**（中灰斜率 1→0.482，正负互为倒数，回归防护"偶函数把减对比变成增对比"）、对比度=1 不把 1/4 灰与 3/4 灰压到端点、亮度为 gamma 幂律且单调、暗部提升多于亮部、标定残差随目标斜率增大且 a ≤ 4、目标斜率 <1 时拟合出负 a（0.8→a<0、0.6 停在上限 -4）、与线性模型 MAE > 10 |
| `TestCompareExperiment` | 进阶①：`_hw1_abs_diff` 不回绕、同图 PSNR=∞、拼接几何与补白、四联图宽度 = 4W+3×gap、各面板与两路径输出逐像素一致、统计文本含 MAE/PSNR/cv2/p72/量化/模型差异、恒等 MAE ≤ 1、模型差异随参数增大、L 定义差异 > S 定义差异 > 色相差异；**色相按圆周最短弧统计**（`_hw1_hue_angle_delta`：359°↔1° 记 2°、对称、上限 180°、与“直接相减”口径对比）、报告中 H 一行与按最短弧重算的值一致、**差异图 ×5 放大不回绕**（int8/uint8 会按 256 取模：255×5→251、60×5→44；现改为 int32 内放大后裁剪，3×5=15 不被裁剪、255 饱和到 255） |
| `TestSubmissionPackage` | 提交包 `submission/hw1/`：必需文件齐全（`functions.py` / `UI.py` / `web_demo.py` / `gradio_compat.py` / 报告 PDF / `README.md`）、**与工作区逐字节一致**、无多余 `.py`、README 写清依赖与“PS 风格”诚实声明、包内 `UI.py` 仍含作业1 的 5 个模式与对比实验接线 |

### 重要说明

- 数组层全部通过 **不等于** 界面测试通过。界面需要在本机启动
  `python web_demo.py` 后打开 <http://127.0.0.1:8088/> 人工验证，
  相关记录见仓库根目录 `PROJECT_LOG.md`。
- 测试文件为 UTF-8 + LF；业务文件（`functions.py`）保持 GBK + CRLF，两者互不影响。

## 界面层冒烟（Gradio，作业1）

```
python tests/ui_smoke_hw1.py            # 自动冒烟：启动服务 -> POST /run/predict -> 断言 -> 关闭
python tests/ui_smoke_hw1.py --serve    # 只启动服务，供人工在浏览器中测试
```

- 自动断言：页面可访问、默认参数逐像素恒等、亮度 +0.5、色相 +180°、饱和度 -1、R 通道分解图，
  以及本次扩展的**5 个模式下拉**、**对比实验事件已注册**（4 输入 / 2 输出）、
  官方 cv2 HLS 的恒等/色相+180/饱和度-1、PS 风格中灰亮度、自然饱和度不改灰色与低饱和增益、
  对比图 4 联几何、统计文本含 MAE/PSNR/cv2/量化。
- 端口被占用时脚本**直接报错退出（rc=2）**，避免连到旧服务而产生假通过（阶段 I 踩过）。
- 服务端输出写入系统临时目录的 `ui_smoke_hw1_server.log`（`--serve` 模式直接打印在控制台）。

### 为什么本脚本单独注册 hw1 界面

本机 gradio 为 **3.36.1**，其中**没有** `gr.ImageEditor`（gradio 4.x 组件），
而原模板 `UI.py` 的 `create_demo_hw3` 使用了它 →
完整 `web_demo.py` 在本机执行时立即 `AttributeError: module 'gradio' has no attribute 'ImageEditor'`（rc=1）。

本脚本**不修改** `UI.py` / `web_demo.py`，只是为作业1 单独构建页面以便实测；
该兼容性问题的结论与待决策项见 `PROJECT_LOG.md` 阶段 F。

仓库根目录另提供双击启动脚本 `start_hw1_demo.bat`（等价于 `python tests/ui_smoke_hw1.py --serve`）。

## 作业1 改动范围契约（作业2~5 不得被改）

```
python tests/test_hw1_ui_contract.py
```

- 断言 `UI.py` / `functions.py` 的 **hw2~hw5 函数体与 `main` 基线逐字节一致**、
  `UI.py` 仍为 GBK+CRLF 无 BOM，且作业1 的 5 个模式与对比实验接线确实存在；
- 基线文本用 `git show main:UI.py` 现场读取；本机没有 git 或没有 `main` 分支时 SKIP；
- 该测试**取代**了旧判定标准"`git diff main -- UI.py functions.py` 必须为空"：
  作业1 扩展必然改动这两个文件的作业1 相关部分，因此判定范围收窄到作业2~5。

## 报告材料生成（作业1）

```
python reports/hw1/make_report.py
```

生成 `reports/hw1/` 下的四联对比图、PS 曲线图、自然饱和度增益图、指标表 `metrics.md`、
自包含 `hw1_report.html` 与 `hw1_report.pdf`（用本机 Edge/Chrome 无头模式打印；
本机没有浏览器时 PDF 输出 SKIP 并保留 HTML 手动导出）。
其中 `fig_ui.png` 为无头浏览器截图，**只作视觉证据，不等于人工浏览器验收**。

## 提交包（作业1）

```
python tools/make_submission.py          # 生成/刷新 submission/hw1/（只复制 + 逐字节校验）
python tests/test_hw1_submission.py      # 守卫测试：提交包与工作区必须逐字节一致
```

老师要求的提交物是 3 个 Python 文件（`functions.py`、`UI.py`、`web_demo.py`）+ 报告 PDF，
但 `web_demo.py` 顶部 `import gradio_compat` 决定了 **`gradio_compat.py` 也是必需文件**：
只交 3 个文件会在启动时 `ModuleNotFoundError`。因此正式提交清单为
`functions.py` + `UI.py` + `web_demo.py` + `gradio_compat.py` + 报告 PDF
（另附 `README.md`、`requirements.txt`），见 `submission/hw1/`。
提交包内的报告为外部排版版 `图像处理作业1_新版实验报告_陈彦米.pdf`（6 页）；
仓库内由 `reports/hw1/make_report.py` 自动生成的 `hw1_report.pdf`（9 页）**不**放入提交包，
避免两份报告混淆。文件清单以 `submission/hw1/` 实际内容为准，并由 `tests/test_hw1_submission.py` 校验。
`web_demo.py` 里的 `gr.Blocks(css='style.css')` 传入的是字符串（gradio 将它当内联 CSS），
仓库中并无 `style.css`，不影响运行，故提交包不含该文件。

## gradio 版本兼容层

`gradio_compat.py`（仓库根目录）为 gradio 3.x 补上模板 `UI.py` 用到的 4.x 组件
（`gr.ImageEditor` / `gr.Brush`），由 `web_demo.py` 顶部调用一次；
`gradio_compat.py` **不修改** `UI.py` / `functions.py` 的组件写法（兼容层阶段这两个文件与 `main` 逐字节一致；阶段 I 起作业1 相关部分有受控改动，判定标准改为 `tests/test_hw1_ui_contract.py`：hw2~hw5 与 `main` 逐字节一致）。

- 单元测试：`python tests/test_gradio_compat.py`
  （安装幂等性 / 不覆盖官方 API、4.x 输入契约、模板 `function_hw3` 的取心逻辑在 3.x 下仍成立、
  `UI.py` 五个界面与 `web_demo.main()` 均可构建）
- 全量程序冒烟：`python tests/ui_smoke_web_demo.py`
  （子进程启动 `web_demo.py` → `GET /` 200 → `GET /config` 校验 5 个作业页签 → 关闭）
- gradio ≥ 4 时 `install()` 自动让位给官方实现，不做任何事。

## 前端真实渲染测试（完整程序）

```
python tests/test_frontend_render.py            # 默认端口 8091（避开手动服务 8088）
python tests/test_frontend_render.py --port 8092
```

**为什么需要它**：`GET /` 返回 200、`/config` 内容正确，**都不等于浏览器完成了渲染**。
阶段 H 的实例：兼容层子类名让 `/config` 出现 `type: "imageeditor"`（gradio 3.x 前端
`component_map` 里只有 `image`）→ 前端渲染中断、整页停在 `Loading...`，
而服务端日志与 HTTP 状态全部正常。**只有真正执行页面 JS 才能发现这类问题。**

本脚本会：

1. 以子进程启动真实 `web_demo.main()`（与 `ui_smoke_web_demo.py` 相同的启动方式）；
2. 用本机 Edge/Chrome 的 **headless 模式**（`--headless=new --dump-dom`）抓取
   **执行 JS 之后**的 DOM；
3. **剥离内嵌 `window.gradio_config` 后**，断言 5 个作业页签文案确实渲染出来、
   且不存在 `Loading...` 遮罩、组件节点（`data-testid="image"`、`component-N`）已生成；
4. 断言 `/config` 中所有带 `tool` 的组件 `type` 均为 `image`（防止再退回前端不认识的名字）。

注意事项：

- 本机无 Edge/Chrome 时输出 **SKIP** 而不是失败，并提示改由人工在浏览器验收。
- Edge ≥ 132 / Chrome ≥ 132 已移除 old headless，**必须**用 `--headless=new`，
  否则 `--dump-dom` 无输出（阶段 H 踩过）。
- 该脚本不参与 `unittest discover`（无 `TestCase`），不拖慢数组层测试。
