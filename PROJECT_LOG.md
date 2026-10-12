# 项目进展记录（PROJECT_LOG）

> 本文件记录**阶段级事实与决策**，供新会话 / 独立 Reviewer 快速掌握项目状态，无需翻阅聊天记录。
> 规则与约束见 `AGENTS.md`（唯一权威）；通用开发流程见全局 Skill `git-development-workflow`。
> 仓库：`https://github.com/chenyanmi666/image-processing-homework`（Private）
> 约定：新条目追加到对应阶段；**归档而非覆盖**，旧结论被取代时注明"取代了 xx"，不得抹除历史判断。

## 项目速览

| 项 | 值 |
| --- | --- |
| 本地路径 | `D:\ -- functions.py UI.py web_demo.py`（目录名异常，严禁重命名/移动） |
| 当前分支 | `feat/image-processing-assignment` |
| 基线 | `main` = `6dcd9f9148c476f32d2e0af07a3aa6b7ba2bce5f`，tag `template-baseline` |
| 远程 | `origin` = 上方私有仓库；`main` / 功能分支 / tag 均已推送 |
| 当前进度 | 阶段 A–F 已完成；作业1 已实现，数组层 46/46 PASS、界面层 API 实测通过，待人工浏览器实测 |
| 学号 | `2400013156`（已写入 `web_demo.py` 第 17 行） |

---

## 阶段 A · 项目现状核查（2026-10-12，只读）

**做了什么**：确认项目路径与内容；检查 Git 现状；识别基线来源；扫描风险内容；读取规则文件。

**结论与证据**

- 目录内含 3 份 py 与 2 份课程讲义 PDF；目录名含空格与 `--` → **决定保持不动**。
- 该目录及父目录**此前不存在任何 Git 仓库**，无既有历史需要保护。
- 三份 py 判定为**未改动的原始模板**。辅助证据：修改时间 `2025-10-08`；
  `web_demo.py` 仍为占位学号 `2400000000`；`functions.py` 中 hw1~hw5 均为空壳（`pass` / 原样返回）。
- 环境：git 2.51.0.windows.1；**无 `gh` CLI**；Git Credential Manager 已保存 GitHub 凭据（可静默认证）。
- 编码约定：`functions.py`、`UI.py` = **GBK**；`web_demo.py` = **UTF-8**；全部 **CRLF**。

---

## 阶段 B · Git 初始化与 GitHub 推送（2026-10-12）

**关联 commit**：`6dcd9f9148c476f32d2e0af07a3aa6b7ba2bce5f`
（`chore: preserve original course template`）
**关联 tag**：`template-baseline`；annotated tag 对象 = `8ea23dfe207002c5b7c95579382e185bdb604c6b`，指向 `6dcd9f9`

**做了什么**

1. `git init -b main`；仓库级设置 `core.autocrlf=false`、`core.quotepath=false`。
2. 新增 `.gitattributes`（`* -text`）保证 CRLF 字节保真；新增 `.gitignore`。
3. 建立基线提交（5 files）→ 打 annotated tag → 建功能分支 → 推送远程并绑定 upstream。

**关键证据**

- 提交前后三份源文件 SHA256 一致（证明零字节改动）：
  - `functions.py` = `07de2201d7a2c607b9c09bc0dc21affc31434ba8cd901ebd297fb0c600ef9931`
  - `UI.py` = `d42451fde182807e7026f5e2c0838f132e60fcb28a2996f8334dd93cf410c3c2`
  - `web_demo.py` = `b4b0e976584e8cb8991adba0bfc67f7b8293211b89d4f10db6c230b0557cad07`
- `git ls-remote origin` 实测：远程 `refs/heads/main`、`refs/heads/feat/image-processing-assignment`、
  `refs/tags/template-baseline`（含 `^{}` 解引用）与本地完全一致。
- `git ls-files` 仅 7 个文件，无 PDF、无环境目录、无密钥。

**技术决策**

1. `.gitignore` **不使用 `*.pdf` 通配**，仅精确忽略两份讲义 → 避免误伤将来的作业报告 PDF。
2. `.clinerules/` **不忽略**，规则文件需入库供独立 Reviewer 阅读。
3. 远程仓库设为 **Private**。

**已知限制（重要）**

- 三份文件**未与课程官方压缩包逐字节比对**（本机无该压缩包）。
  因此基线只能声明为"经现状检查的初始模板快照"，**不得声称"已核验的官方原件"**。
  该声明已同时写入 commit body、tag 注解与本文件。

---

## 阶段 C · 全局 Skill 与项目规则（2026-10-12）

**关联 commit**：`5b315a97c32c5a7707cbd3178c771e72230a4484`
（`docs: add project rules (AGENTS.md as single source of truth)`）

**做了什么**

- 查证 Cline 原生 Skills 机制后创建全局 Skill（**仅一处，不建副本**）：
  `C:\Users\雁\.cline\skills\git-development-workflow\SKILL.md`
- 建立项目规则：`AGENTS.md` 为唯一权威来源；`.clinerules/README.md` 仅作**指针**、不复制内容。

**关键证据（源码级，非猜测）**

- `SBp() = path.join(os.homedir(), ".cline", "skills")` → 全局 Skill 扫描目录之一。
- 项目级扫描目录：`.clinerules/skills`、`.cline/skills`、`.claude/skills`、`.agents/skills`。
- `SKILL.md` 必须由 YAML frontmatter 包裹；字段白名单 =
  `{name, description, license, compatibility, metadata, allowed-tools}`；
  目录名必须与 `name` 一致；`name ≤ 64`、`description ≤ 1024`、`compatibility ≤ 500`。
- 格式校验脚本（`C:\temp\verify_skill.py`，复刻同一套规则）结果：frontmatter 正则匹配、
  PyYAML 解析成功、无多余字段、无 BOM、目录名 = `name`。

**技术决策**

4. 通用流程只写全局 Skill；项目专有细节只写 `AGENTS.md`（避免污染其他项目、避免规则分叉）。
5. 为 Skill 增加**项目进展记录机制**（`PROJECT_LOG.md`），章节见 Skill 第 10 节。
6. 修订 `AGENTS.md` §4：乘性明度模型 `I' = I*(1+l)` 定位为**当前默认设计**，
   而非不可变更的数学要求；若有测试/对比依据且经用户明确批准可调整，
   但必须同步修订规则、记录于本文件并重跑测试。

---

## 阶段 D · 验证与遗留（2026-10-12）

**已实测通过**

- `main` = `6dcd9f9`、`feat/image-processing-assignment` = `5b315a9`，远程 refs 与本地一致，无 ahead/behind。
- 标签 `template-baseline` 有效且已推送。
- 源文件 SHA256 与基线一致；`.gitignore` 精确命中两份讲义且未误伤其他 PDF。
- 独立 Reviewer（ChatGPT）已通过 GitHub 连接器读取 `AGENTS.md`、`.clinerules/README.md`、`.gitignore`，
  并核对 `main` 与功能分支的真实差异 → **阶段 B 验收通过，阶段 C 结构与格式检查通过**（来源：用户告知）。

**未验证 / 限制（不得视为已通过）**

1. **Skill 运行时加载仍待验证** —— 文件存在 + YAML 校验通过**不等于** Cline 实际识别并注入。
   已确认新版 Cline 数据布局为 `~/.cline/data/{db,sessions,logs,settings,globalState.json}`；
   本会话任务启动时间早于 SKILL.md 创建时间，因此**本会话的 system prompt 不含该 Skill 列表**，
   必须**在 SKILL.md 创建后新开的任务中**验证（详见下方"待验证事项"）。
2. 基线未与官方压缩包逐字节比对（见阶段 B）。
3. **业务代码零测试** —— 本阶段按指令未改动任何算法代码，故不存在"算法测试通过"的结论。
4. PR 未创建：遵循用户决定"等实际功能完成后再创建"；本机无 `gh` CLI，届时通过 GitHub 网页创建。
5. 环境噪声：终端输出捕获不稳定 → 命令统一改为"写脚本到 `C:\temp` + 输出落文件再读取"；
   本项目会话的 `%TEMP%` 指向 `C:\temp`。

**自我纠错（保留记录，不删除）**

- 一度依据 `globalStorage` 目录名误判"用户使用中文版 Cline"。时间戳实证推翻该判断：
  `~/.cline/data` 于本次会话被写入，而 `~/.cline-chinese/data` 停留在 `2026-09-05`。
  实际使用的是**正版 Cline**（`saoudrizwan.claude-dev`），数据根目录为 `~/.cline`。
  结论方向不变，但依据已替换为实证。

**待验证事项（下一阶段开头处理）**

- [x] 官方版 4.1.23 源码复核（本轮完成，直接读取 `dist/extension.js` 实测）：
      `_Bp() = join(homedir(), ".cline")`、`SBp() = join(_Bp(), "skills")` → `~/.cline/skills`；
      `TBp() = join(homedir(), ".agents", "skills")`；
      项目级扫描函数 `p1n()` 含 `.clinerules/skills`、`.cline/skills`、`.claude/skills`；
      校验路径 `bOo() = join(<skills 根>, <name>, "SKILL.md")` → 每个 Skill 占一个子目录。
      → 已落盘的位置与命名**符合官方版机制**（结构层面已确认）。
- [ ] **运行时注入仍未验证**（不得视为通过）：必须在 SKILL.md 创建之后**新开的任务**中
      确认 Cline 是否把 `git-development-workflow` 注入可用 Skill 列表。
      核验脚本已备好：`C:\temp\check_new_task_skill.py`
      （读取最新会话的 `messages.json`，检查其 system prompt 中是否出现该 Skill 名与正文）。


---

## 阶段 E · 作业1 `function_hw1`（已完成，待界面实测）

**关联 commit**：`ac9ee1b4c7b5dfdd0362bd1d79d9a69336626a4a`

**目标**：按课件《图像处理基础（上）》p66–p84 手写 RGB↔HSI，实现
「色相/饱和度」与「亮度/对比度」两种模式，返回 7 个输出以匹配 `UI.py` 绑定。

**约束**：全 numpy 向量化（禁用逐像素 Python 循环）；默认滑块全 0 时必须与原图逐像素相等；
不得修改 hw2~hw5 与 `UI.py` 业务逻辑；像素级判定只在 Python 数组层完成。

**实现**（`functions.py`，仅改 `function_hw1` 及其 `_hw1_` 前缀辅助函数）

- 新增 `_hw1_rgb_to_hsi`、`_hw1_hsi_to_rgb`（课件 p66–p84 定义 + p78 分段逆变换）、
  `_hw1_as_float_rgb`（输入规整）；全部 numpy 向量化，无逐像素 Python 循环。
- 模式「色相/饱和度」：`H' = (H + 180*h_slider) mod 360`、`S' = clip(S*(1+s_slider))`、
  `I' = clip(I*(1+l_slider))`。
- 模式「亮度/对比度」：自定义线性模型，先对比度后亮度 `(I-0.5)*(1+c)+0.5+b`。
- 7 路输出 `(结果图, R, G, B, H, S, I)`，通道分解图取自处理后的结果图（H 以 H/360*255 灰度显示）。

**测试**（`C:\temp\test_hw1.py`：数组层直接调用算法函数，不依赖界面；**22/22 PASS**）

| 检验项 | 结果 |
| --- | --- |
| 返回 7 值 / 形状 / dtype | PASS：(64,64,3) uint8，通道图为单通道 uint8 |
| **默认滑块全 0 与原图逐像素相等** | PASS：两种模式均 `max|d|=0`（无需任何恒等短路） |
| RGB→HSI→RGB 浮点往返 | PASS：最大误差 `3.16e-14` |
| RGB→HSI→RGB uint8 往返 | PASS：`max|d|=0` |
| 纯红 +180° | PASS：`[0,128,128]`（青） |
| 纯红 +60° | PASS：`[128,128,0]`（黄） |
| 色相 ±180 周期性 | PASS：`max|d|=0` |
| 饱和度 -1 → 灰度 | PASS：R==G==B |
| 明度乘性 `I'=I*(1+l)` | PASS：实测比值 `1.5000`（l=0.5） |
| l=-1 → 全黑 | PASS |
| 饱和度单调性 | PASS：平均 S 由 `0.0 → 0.2507 → 0.5015 → 0.7017 → 0.8599` |
| 亮度线性精确性 | PASS：`max|d|=0` |
| 对比度 -1 → 恒定 128 灰 | PASS |
| 边界：纯黑/纯白/纯灰/单像素 × 2 模式 × 极值参数 | PASS：无异常、无 NaN |
| 空输入（None） | 抛出异常（见下方已知问题） |
| 512×512 性能 | PASS：`0.112 s` |

**已知问题（原模板既存，本轮未修改）**

- 本机 gradio 版本为 **3.36.1**，其 `gr.Error.__init__(self, message: str = 'Error raised.')`
  **不接受 `duration` 参数**；而模板中 hw1~hw5 均写作 `raise gr.Error('...', duration=5)`
  → 空输入时实际抛出 `TypeError`，界面得不到友好提示。
  这属于**原模板与本地 gradio 版本不兼容**，非本次改动引入；是否修复需用户决定。

**过程记录（自我修正，保留不删）**

- 重写 `function_hw1` 时曾把原始 GBK 提示语误"猜译"为"图像处理操作之前请先上传一张图像"，
  已依据改动前备份还原为原文 `'输入错误：在处理之前请先输入一张图像'`（校验 `MATCH_ORIGINAL: True`）。
- 已验证 `function_hw2` 及之后所有内容与改动前**逐字节一致**；文件为纯 CRLF、无 BOM。

**下一步（待用户确认）**

- 是否填写学号 `2400013156` 到 `web_demo.py`（当前仍为占位 `2400000000`）。
- 是否处理 gradio/Gr.Error 兼容问题。
- 进入作业2 `function_hw2`（此前需先确认作业1 界面实测通过）。

---

## 阶段 F · 作业1 加固修复与界面层实测（2026-10-12）

**触发**：外部 Reviewer（ChatGPT，经 GitHub 连接器）审查 commit `ac9ee1b` 与本日志后，
认可算法与接口方向，但**暂不最终验收、暂不进入作业2**，要求先完成 8 项加固（本节逐项记录）。

### F1 · HSI 逆变换改为分段局部计算（`_hw1_hsi_to_rgb`）

- **旧写法**：对全图套用三段公式后用 `np.where` 选择 → 无效分段也会被计算。
  例：H=210 属第 2 段，旧实现同时计算第 3 段的 `H' = 210-240 = -30`，
  分母 `cos(60-(-30)) = cos(90°) ≈ 6.1e-17` → 中间量量级 1e16（结果虽被 `np.where` 丢弃，仍属数值不稳定）。
- **新写法**：布尔掩码索引，`if seg1.any(): ...` 只对命中分段的像素求值。
- **等价性证据**：720 个色相 × 循环 (S,I) 组合下，与旧实现 `np.array_equal` **位级一致**。
- **"只算命中段"的证据**：用 `np.cos` 探针拦截全部 cos 调用，断言被求值角度均落在 `[0,120)`；
  旧实现会立即失败（会看到 210、-30 等越界角度）。

### F2 · `_hw1_as_float_rgb` 输入校验

- `None`、无法转数组、1 维/4 维、通道数 2 或 5、非数值 dtype（str/object）、空尺寸
  → 一律抛 `ValueError`，消息中带**实际 shape/dtype**（不再出现难以定位的索引异常）。
- 正确接受：2D 灰度、`(H,W,1)`、`(H,W,4)`（丢弃 alpha）、bool、`[0,1]` 浮点、0-255 浮点。

### F3 · `mode` 显式分支

- 改为 `if / elif / else`：未知模式与 `None` 均抛 `gr.Error("不支持的模式：...")`，
  不再静默落入亮度/对比度分支。

### F4 · gradio 3.36.1 `gr.Error(duration=5)` 兼容（最小修改）

- **方案**：`functions.py` 顶部新增模块级兼容层 `_GradioCompat`，只接管 `Error` 构造
  （支持 `duration` 的版本原样透传，不支持的退化为单参数构造），其余属性转发真实 gradio。
- **边界**：`function_hw2` ~ `function_hw5` 业务代码**零改动**（符合 AGENTS §5）；
  未修改 gradio 模块本身；`UI.py` / `web_demo.py` 里的 `gr` 不受影响；未升级环境。

### F5 · 测试脚本入库

- 新增 `tests/test_hw1.py`（`unittest` 驱动，仅依赖 numpy）与 `tests/README.md`（执行说明 + 覆盖表）。
  执行方式：`python tests/test_hw1.py` 或 `python -m unittest discover -s tests -v`。

### F6 · 学号写入

- `web_demo.py` 第 17 行 `2400000000` → `2400013156`；采用**字节级替换**，
  实测纯 CRLF、无 BOM、文件长度不变（两串同为 10 字符）。

### F7 · 数组层回归结果（本轮实测）

`python tests/test_hw1.py` → **46/46 PASS，0 failures，0 errors，用时 0.09–0.12 s**

| 测试类 | 数量 | 覆盖 |
| --- | --- | --- |
| `TestContract` | 3 | 7 路输出、形状/dtype、通道分解图与结果图一致 |
| `TestIdentity` | 2 | 默认滑块两种模式逐像素复制原图（`max|d|=0`） |
| `TestHueSaturation` | 10 | 浮点/uint8 往返、色相锚点、周期性、饱和度单调、明度乘性 |
| `TestBrightnessContrast` | 4 | 亮度线性、对比度 -1 → 128 灰、先对比度后亮度 |
| `TestInverseSegments` | 8 | 与旧实现位级一致、cos 探针、全域无 `RuntimeWarning`、边界色相、越界取模 |
| `TestInputValidation` | 14 | 非法/合法输入形态全覆盖 |
| `TestModeBranch` | 4 | 未知模式抛错、亮度模式忽略色相滑块 |
| `TestEdgeAndPerformance` | 3 | 极端图像、单像素、512×512（实测 0.079–0.097 s） |

**测试自身纠错（保留不删）**：首轮 3 个失败均为**测试写错**而非实现缺陷——
① 误把单通道分解图当 3 维；② 误把 ±90° 当周期等价（应为 ±180°）；
③ 明度乘性测试用了高饱和色，放大后触及 RGB 边界被裁剪（改用低饱和色后精确 `1.5000`）。

### F8 · 界面层实测（关键发现）

**发现 1：完整 `web_demo.py` 在本机无法启动（原模板既存问题，非本次改动引入）**

- 报错：`AttributeError: module 'gradio' has no attribute 'ImageEditor'`
  —— `UI.py:85` 的 `create_demo_hw3` 使用 `gr.ImageEditor`，该组件为 **gradio 4.x** 才有。
- 影响：本机 gradio 3.36.1 下 `python web_demo.py` **启动即退出（rc=1）**，任何页面都打不开。
- 处置：**未修改 `UI.py`**（AGENTS §5 禁止擅自改动）；改为对 **hw1 单独注册界面** 做实测，
  脚本入库为 `tests/ui_smoke_hw1.py`（`--serve` 供人工测试，默认自动冒烟）。

**发现 2：hw1 界面层端到端验证通过**

- 方式：启动仅含 hw1 的 Gradio 服务，用原生 `POST /run/predict` 真实走
  「组件序列化 → `function_hw1` → 反序列化」全链路（输入 32×32 纯红 `[255,0,0]`）：

| 调用 | 返回 |
| --- | --- |
| 页面 `GET /` | HTTP 200，33902 字节，含"作业一""色相/饱和度""亮度/对比度" |
| 色相/饱和度 默认参数 | 7 个输出，`[255,0,0]`（逐像素恒等） |
| 亮度/对比度 `b=0.5` | `[255,128,128]` |
| 色相 `h=1.0`（+180°） | `[0,128,128]`（青） |
| 饱和度 `s=-1.0` | `[85,85,85]`（I=1/3 → 85） |
| R 通道分解图 | `[85,85,85]`，与结果图一致 |

- `gradio_client` 与本机 gradio 版本不匹配（422 / `KeyError: 'data'`）无法使用 → 已改用原生 HTTP 端点。
- **仍未完成**：人工在浏览器中拖动滑块观察实时联动（数组层与 API 层通过**不等于**视觉/交互通过）。

### F9 · 提交明细

- `fix: harden function_hw1 ...`（`functions.py`）
- `test: add reusable array-level test suite and UI smoke script`（`tests/`）
- `chore: fill in student id in web_demo.py`（`web_demo.py`）
- `docs: record stage F fixes, regressions and UI smoke results`（`PROJECT_LOG.md`、`AGENTS.md`）

### 下一步

- 用户人工实测 hw1 页面：`python tests/ui_smoke_hw1.py --serve` → 浏览器打开 <http://127.0.0.1:8088/>。
- 通过后再进入作业2 `function_hw2`。
- **待用户决策**：完整 `web_demo.py` 的 gradio 版本问题
  （升级 gradio 4.x / 本地临时替换 hw3 组件 / 保持现状只做单页实测）。
