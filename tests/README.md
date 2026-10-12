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

- 自动断言：页面可访问、默认参数逐像素恒等、亮度 +0.5、色相 +180°、饱和度 -1、R 通道分解图。
- 服务端输出写入系统临时目录的 `ui_smoke_hw1_server.log`（`--serve` 模式直接打印在控制台）。

### 为什么本脚本单独注册 hw1 界面

本机 gradio 为 **3.36.1**，其中**没有** `gr.ImageEditor`（gradio 4.x 组件），
而原模板 `UI.py` 的 `create_demo_hw3` 使用了它 →
完整 `web_demo.py` 在本机执行时立即 `AttributeError: module 'gradio' has no attribute 'ImageEditor'`（rc=1）。

本脚本**不修改** `UI.py` / `web_demo.py`，只是为作业1 单独构建页面以便实测；
该兼容性问题的结论与待决策项见 `PROJECT_LOG.md` 阶段 F。

仓库根目录另提供双击启动脚本 `start_hw1_demo.bat`（等价于 `python tests/ui_smoke_hw1.py --serve`）。

## gradio 版本兼容层

`gradio_compat.py`（仓库根目录）为 gradio 3.x 补上模板 `UI.py` 用到的 4.x 组件
（`gr.ImageEditor` / `gr.Brush`），由 `web_demo.py` 顶部调用一次；
`UI.py` 与 `functions.py` **保持字节级原样**（`git diff main -- UI.py` 为空）。

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
