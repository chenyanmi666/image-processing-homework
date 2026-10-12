# 项目规则（唯一权威来源）

> 本文件是本课程作业项目规则的**唯一权威来源**。
> `.clinerules/README.md` 只指向本文件、不重复内容，避免两份规则互相冲突。
> 通用开发流程（分支/提交/推送/PR/权限分级）见全局 Skill `git-development-workflow`
> （`~/.cline/skills/git-development-workflow/SKILL.md`），本文件只写**项目专有约束**。

## 1. 项目概况

- 本地绝对路径：`D:\ -- functions.py UI.py web_demo.py`
  —— 目录名异常（含空格与 `--`），**严禁重命名、移动或"清理"**。
- 组成：`functions.py`（算法实现）、`UI.py`（界面与事件绑定）、`web_demo.py`（Gradio 启动入口/学号展示）。
- 课程讲义：`2 图像处理基础 上.pdf`、`4 编程实践基础 (1).pdf` —— 版权材料，**不入库**。
- 学号：`2400013156`。

## 2. 文件编码（严格，改动时不得改变）

| 文件 | 编码 | 说明 |
| --- | --- | --- |
| `functions.py` | **GBK** | 中文注释为 GBK，写成 UTF-8 会乱码 |
| `UI.py` | **GBK** | 模式名等中文字面量为 GBK（如 `"色相/饱和度"`） |
| `web_demo.py` | **UTF-8** | 内含 HTML 模板 |

所有文件为 **CRLF** 行尾；仓库已设 `core.autocrlf=false` + `.gitattributes` 的 `* -text` 保证字节保真。

## 3. 接口契约（不可破坏）

`function_hw1(input_image, mode, h_slider, s_slider, l_slider, brightness, contrast)`

- 7 个入参，必须返回 **7 个值** `(output_image, R, G, B, H, S, L)`，与 `UI.py` 的输出绑定一致。
- 由 `input_image.change` 与各滑块 `release` 高频触发 → 实现必须**全 numpy 向量化**，禁止逐像素 Python 循环。

## 4. 算法定义（以课件为唯一准绳）

- 采用课件《图像处理基础（上）》**p66–p84** 的手写 HSL/HSI 定义：
  `I = (R+G+B)/3`、`S = 1 - 3*min(R,G,B)/(R+G+B)`、`H ∈ [0,360)`；逆变换用课件 p78 的分段公式。
- 黑色、灰色等退化情况（S 分母为 0）单独处理。
- 亮度采用**乘性模型** `I' = I*(1+l)`（保持 H/S 不变、保持黑色为黑）。
- 结果超出 RGB 立方体时允许裁剪，但**必须承认裁剪会改变实际 H/S/I**，
  不得宣称裁剪后其余通道严格不变。
- 基础亮度/对比度是**自定义线性模型**，**不得冒充 Photoshop 拟合**；PS 风格属独立进阶功能。
- `cv2.cvtColor(..., COLOR_RGB2HLS)` 是**另一套数学定义**，仅作对比；
  不得声称两者是"同一模型的两种实现"，也不得仅凭通道误差判定谁更准确
  （量化误差与模型差异必须分开讨论）。

## 5. 修改范围约束

- 允许修改：`function_hw1` 及其专用辅助函数。
- **不得修改 `function_hw2` ~ `function_hw5` 的业务逻辑**（签名、返回值结构、既有实现）。
- 未经明确指令，不修改 `UI.py` / `web_demo.py` 的业务逻辑。

## 6. 测试与报告真实性（强制）

- 只报告**实际运行过**的测试与输出；未执行的测试必须显式声明为"未执行"。
- 必测项：返回数量/形状/dtype、默认参数下与原图逐像素相等、滑块单调性、
  HSI 边界（S=0、I→0、I→1、S=1 且 I→1 属定义域外）、H 跨越 0/360 的周期性、
  RGB/BGR 通道顺序。
- 像素级判定必须在 **Python 数组层**完成（Gradio 网页预览走 webp 有损压缩，不能作为判据）。

## 7. Git 与协作约定

- `main`：稳定基线，tag `template-baseline` = 初始课程模板快照
  —— **未与课程官方压缩包逐字节比对**，不得声称"已核验的官方原件"。
- 开发分支：`feat/image-processing-assignment`。
- 远程：私有仓库 `https://github.com/chenyanmi666/image-processing-homework.git`。
- 每完成一个经测试的阶段即 commit + push 到功能分支；PR 由 ChatGPT 独立审查，
  **未经用户批准不得合并**。
- 禁止：`push --force`、删除远程分支/仓库、公开私有仓库、改写 `main` 历史。
