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
| 当前进度 | 阶段 A–I 已完成；作业1 已实现 **5 个模式**（手写 HSL / 官方 cv2.COLOR_BGR2HLS / PS 风格自然饱和度 / 线性亮度对比度 / PS 风格亮度对比度）+ **对比实验按钮与误差统计** + `reports/hw1` 报告材料（阶段 I）；数组层与兼容层 116 项测试、界面冒烟 23 项、前端真实渲染 13 项全部通过；完整 `web_demo.py` 已适配 gradio 3.36.1 **且前端真正渲染出 5 个页签**（阶段 H 修复了"卡在 Loading"），待进入作业2 |
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
---

## 阶段 G · 完整 web_demo.py 的 gradio 版本兼容修复（2026-10-12）

**触发**：用户在浏览器完成作业1 人工测试（色相/饱和度/明度、亮度/对比度两种模式均正常，
七路输出正常），ChatGPT 同意作业1 通过当前阶段验收；要求优先解决"完整 `web_demo.py`
因 gradio 版本不兼容无法启动"，且**改动范围最小、对其他作业影响最小、不得破坏原始模板基线**。

### G1 · 根因（复核确认）

- `UI.py:85` 的 `create_demo_hw3` 使用 `gr.ImageEditor`（第 85 行）与 `gr.Brush`（第 86 行），
  二者均为 **gradio 4.x** 组件；本机 gradio **3.36.1** 中不存在
  （实测 `hasattr(gr, "ImageEditor") is False`、`hasattr(gr, "Brush") is False`）。
- 结果：`python web_demo.py` 在构建界面时即 `AttributeError`、rc=1，**任何页面都打不开**。
- 连带发现（3.36.1 的既存事实，非本次引入，**未改动**）：`gr.Image` 的参数是**单数** `source`
  （合法值仅 `upload`/`webcam`/`canvas`），模板中 5 处 `sources=[...]` 会被 `**kwargs` 吞掉并发出
  `GradioUnusedKwargWarning` → 3.x 下实际只有"上传"通道生效（webcam/clipboard 无效）。

### G2 · 方案比较与选择

| 方案 | 改动面 | 对其他作业的影响 | 结论 |
| --- | --- | --- | --- |
| 升级 gradio 到 4.x | 全局环境 | 影响全部 5 个作业的组件行为 | ✗ 不采用 |
| 改写 `UI.py` 的 hw3 组件写法 | 篡改模板文件 | 破坏"模板基线可回溯" | ✗ 不采用 |
| **新增 `gradio_compat.py` + `web_demo.py` 顶部 2 行** | 1 个新文件 + 入口 2 行 | hw1/hw2/hw4/hw5 零影响 | ✓ 采用 |

**基线保真的硬证据**：`git diff main -- UI.py` **无任何差异**（`functions.py` 的差异全部来自
阶段 F 的作业1 修复，属已批准范围）。

### G3 · 实现（`gradio_compat.py`）

- 3.36.1 的 `gr.Image(tool="sketch", source="upload", type="numpy")` 的 `preprocess` 恰好返回
  `{"image": …, "mask": …}`（见 `gradio/components/image.py:271-276`），是最贴近 4.x 的落点。
- `ImageEditor` = 上述 `gr.Image` 的子类，`preprocess` 返回 **4.x 风格字典**
  `{"background": …, "layers": [mask], "composite": …}`；
  因此 `UI.py` 的 `reset_points`（`bg_img["background"]`）与 `functions.py` 的 `function_hw3`
  （`bg_image["background"]`、`bg_image["layers"][0][:, :, 0]`）**一行都不用改**。
- `Brush` 的最小替身：`default_size` → 3.x 的 `brush_radius`；`colors[0]` → composite 的填充色。
- `install()` 幂等且可退化：gradio ≥ 4 时返回 False、不做任何事（将来升级无需删代码）。
- 能力差异如实写入 `gradio_compat.LIMITATIONS` 并在测试中断言：
  ①无真图层（`layers` 恒为长度 1 的列表）；②画笔颜色固定（`colors`/`color_mode` 被忽略）；
  ③橡皮无法禁用（`eraser=False` 被忽略）；④`composite` 是按 mask 填画笔色的近似值。

### G4 · 测试与实测结果（本轮实际输出）

| 项目 | 命令 | 结果 |
| --- | --- | --- |
| 兼容层单元测试 | `python tests/test_gradio_compat.py` | **19/19 PASS**（1.080 s） |
| 作业1 数组层回归 | `python tests/test_hw1.py` | **46/46 PASS**（0.093 s） |
| 作业1 单页界面冒烟 | `python tests/ui_smoke_hw1.py` | **5/5 PASS**（阶段 F 记录） |
| **完整程序启动冒烟** | `python tests/ui_smoke_web_demo.py --port 8090` | **10/10 PASS** |

兼容层测试覆盖：安装幂等 / 不覆盖官方 API、`source` 收敛规则、`Brush.default_size → brush_radius`、
`preprocess` 的 4.x 契约（background 逐像素回环、`layers[0][:, :, 0]` 与输入 mask 完全一致）、
**把 shim 输出直接喂给模板 `function_hw3` 并数出 4 个连通域**、`postprocess` 接受 numpy 与字典、
`UI.py` 五个界面与 `web_demo.main()`（mock 掉 `launch`）均可构建。

完整程序冒烟输出（8088 被用户手动启动的 hw1 单页服务占用，故用 8090）：

```
启动方式：python -c <bootstrap>（调用真实 web_demo.main()，端口 8090）
[PASS] web_demo.py 进程存活
[PASS] GET / 返回 200 -> status=200
[PASS] 页面含 5 个作业文案 -> 71435 bytes
[PASS] 页签存在：作业1 / 作业2 / 作业3 / 作业4 / 作业5（5 项）
[PASS] 作业3 编辑器退化为 sketch 工具 -> tools=['editor', 'sketch']
[PASS] /config 状态 200
UI smoke (full app): 10/10 PASS
```

- 端口 8088 走**原生** `python web_demo.py`（与手动运行完全一致）；
  本次因端口占用改走 `--port 8090`（仅替换 `server_port`，仍调用真实 `web_demo.main()`）。
- **仍未完成**：用户在浏览器中人工确认完整页面 5 个页签（尤其作业3 的画笔/清空交互）。
  自动化只能证明"能启动 + 页签与编辑器类型正确"，不能替代视觉与交互验证。

### G5 · 提交明细

- `feat: add gradio 3.x compatibility shim for the template UI`（`gradio_compat.py`）
- `chore: install gradio compatibility layer in the entry point`（`web_demo.py`）
- `test: cover the compatibility layer and full-app startup`（`tests/`）
- `docs: record stage G gradio compatibility fix`（`PROJECT_LOG.md`、`AGENTS.md`）

### 下一步

- 用户人工验证完整页面：`python web_demo.py` → <http://127.0.0.1:8088/>（先关闭占用该端口的服务）。
- 通过后进入作业2 `function_hw2`。

---

## 阶段 H · 完整页面"卡在 Loading"根因修复（2026-10-12）

**触发**：用户人工打开 <http://127.0.0.1:8088/> 后，浏览器**一直停在 Gradio 的 "Loading..." 页面**，
五个作业页签完全没渲染出来。→ 阶段 G 的"10/10 冒烟"**不能代表验收通过**，据此推翻此前判断。

### H1 · 现象与复现（三件事必须分开）

| 检查 | 修复前观测 | 说明 |
| --- | --- | --- |
| `GET /` | **200，71423 bytes** | 只证明 HTTP 层正常 |
| `GET /config` | **内容完整**（5 个页签 label 齐全、image 组件齐全） | 只证明服务端配置正常 |
| **浏览器真实渲染** | **只有页脚 + spinner + "Loading..."** | 真正的判据（截图 `C:\temp\shot_before.png`） |

复现方式：`msedge --headless=new ... --screenshot=...` 与 `--dump-dom`（见 H4）。
修前 DOM 特征：`<p class="loading svelte-zlszon">Loading...</p>` 且主容器
`<div class="contain" style="flex-grow: 1;"></div>` **为空**。

### H2 · 根因（源码级，非猜测）

gradio 3.x 用**类名**推导前端组件名：`Component.get_block_name()` →
`camelcase_to_snakecase(cls.__name__)`。阶段 G 的兼容层把子类命名为 `ImageEditor`，
于是 `/config` 里该组件 `type` 变成 **`"imageeditor"`**，而 3.36.1 前端 `component_map`
中只有 `"image"` → 前端找不到组件 → 渲染中断 → 整页停在 Loading（服务端毫无异常）。

实测证据（修复前）：

```
$ python -c "import gradio_compat, gradio as gr; gradio_compat.install(); ..."
ImageEditor block_name: imageeditor      # 前端不认识这个名字
Image block_name: image
$ # 运行中服务的 /config
imageeditor | tool= sketch               # 唯一的非 image 组件就是它
```

**区分点**：`tool="sketch"`（组件能力）与组件 `type`（前端组件名）是两回事，
阶段 G 只验证了前者，漏掉了后者 —— 这是本次阻塞的成因。

### H3 · 最小修复

在 `gradio_compat.ImageEditor` 上覆盖一个类方法（**其余代码零改动**）：

```python
@classmethod
def get_block_name(cls):
    """向 gradio 声明本组件应作为内置 image 渲染（否则前端不认识 imageeditor）。"""
    return "image"
```

- 前端随即按内置 `Image` 组件渲染，`tool="sketch"` 仍是画笔/橡皮编辑器，语义不变。
- 不升级 gradio、不改 `UI.py` / `functions.py`、不动模板基线。

### H4 · 修复后证据（真实渲染，非 HTTP 状态）

| 项 | 修复前 | 修复后 |
| --- | --- | --- |
| `/config` 中带 `tool` 的组件 `type` | `imageeditor` + `image` | **全部 `image`（17 个）** |
| headless 截图 | 仅页脚 + "Loading..."（`C:\temp\shot_before.png`） | **5 个页签 + 作业1 完整界面**（`C:\temp\shot_after.png`） |
| dump-dom 可见文本（已剥离内嵌 config） | 无页签、无组件节点 | 含 5 个页签、`输入图像`/`输出图像`/`模式`…、`data-testid="image"`、`component-N` |

### H5 · 新增可重复的前端渲染测试

`tests/test_frontend_render.py`（用法见 `tests/README.md`）：
启动真实 `web_demo.main()` → 用无头 Edge/Chrome 执行页面 JS → **剥离内嵌
`window.gradio_config` 后**断言页签文案真的渲染出来、且不存在 `Loading...` 遮罩；
另断言 `/config` 中编辑器组件 `type` 全为 `image`（防"回退成前端不认识的名字"）。
本机无浏览器时输出 SKIP 并提示人工验收（不算失败）。

### H6 · 测试结果（本轮实际输出）

| 项目 | 命令 | 结果 |
| --- | --- | --- |
| **前端真实渲染（新增）** | `python tests/test_frontend_render.py --port 8091` | **13/13 PASS**（DOM 108624 bytes） |
| 全量单元测试 | `python -m unittest discover -s tests -v` | **65 tests OK** |
| 作业1 数组层 | `python tests/test_hw1.py` | **46/46 OK**（0.102 s） |
| 兼容层单元 | `python tests/test_gradio_compat.py` | **19/19 PASS** |
| 完整程序启动冒烟 | `python tests/ui_smoke_web_demo.py --port 8090` | **10/10 PASS**（71423 bytes） |

前端渲染测试输出（实测节选）：

```
浏览器：C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
启动方式：python -c <bootstrap>（调用真实 web_demo.main()，端口 8091）
[PASS] /config 编辑器组件 type 全为 image -> types=['image']
[PASS] 抓到渲染后的 DOM -> rc=0 bytes=108624
[PASS] 剥离内嵌 config 后仍见页面标题
[PASS] 渲染结果含页签：作业1 / 作业2 / 作业3 / 作业4 / 作业5（5 项）
[PASS] 不再停留 Loading 遮罩 -> 可见文本长度=681
[PASS] 作业1 页签内容已渲染
[PASS] 图像组件节点已生成
[PASS] 渲染节点 component-N 已生成
前端渲染测试：13/13 PASS
```

### H7 · 排障中踩到的坑（供后续复用）

1. Edge 154 **已移除 old headless**：`--headless` + `--dump-dom` 返回 **0 字节**，必须 `--headless=new`。
2. `msedge.exe` 是**分离启动器**：用 `cmd >` 重定向时句柄可能被浏览器进程持有、命令返回时输出尚未落盘
   → 需**独立进程启动 + 之后单独读取**，或在 Python 里 `subprocess.run(stdout=file)`。
3. 自写同步 CDP 客户端（websocket-client）在本机出现 `recv()` 不返回、进程挂死 → **弃用**；
   若要读前端 console 错误，建议改用 playwright（本机未安装）。
4. `--screenshot` 是最快的"人眼级"证据：**修前只显示页脚 + `Loading...`，修后 5 个页签齐全**。

### H8 · 诚实声明

- 本机**未安装** playwright / selenium（实测 `importlib.util.find_spec` 均为 False），
  前端验证使用 Edge headless（截图 + dump-dom），**不是**成熟浏览器自动化框架。
- 自动化能证明"5 个页签渲染出来、无 Loading 遮罩、组件节点存在"，
  但**交互行为**（hw1 的滑块/模式切换、hw3 的画笔与清空、插值下拉）仍需用户在本机浏览器人工确认。
- 阶段 G 的"10/10 冒烟"本身无误，但其**适用边界被修正**为"服务端起得来、页签与编辑器类型正确"，
  不再视为完整程序可用性的依据；历史结论按约定保留、不抹除。

### 下一步

- 用户**强制刷新**浏览器（Ctrl+Shift+R，避开旧缓存）后人工验收五个页签。
- 通过后进入作业2 `function_hw2`。

---

## 阶段 I · 作业1 满分档扩展：官方 cv2 HLS + 两个进阶功能 + 报告材料（2026-10-12）

**触发**：作业1 的评分档要求 —— 基本信息档需要**直接调用 `cv2.COLOR_BGR2HLS`**，
满分档还需要 **≥2 个进阶功能并附实验依据**。阶段 E 只做了手写 HSL + 线性亮度/对比度（60 分档口径）。

### I1 · 改动清单（限定在作业1 范围内）

| 文件 | 改动 | 约束核对 |
| --- | --- | --- |
| `functions.py`（GBK+CRLF 保真） | 新增 `_hw1_rgb_to_hls_opencv` / `_hw1_hls_opencv_to_rgb`、`_hw1_adjust_in_hsi` / `_hw1_adjust_in_hls_opencv`、`_hw1_apply_vibrance`、`_hw1_ps_*`、`_hw1_to_uint8` / `_hw1_abs_diff` / `_hw1_error_stats` / `_hw1_side_by_side`，以及 `function_hw1_compare`；`function_hw1` 分支 2 → 5 | `function_hw2`~`hw5` 与 `main` **逐字节一致**（契约测试断言） |
| `UI.py`（GBK+CRLF 保真） | 模式下拉 2 → 5 项；新增"进阶① 对比实验"按钮 + 对比图 + 统计文本，且**仅在注入 `process_compare` 时渲染** | `create_demo_hw2`~`hw5` 与 `main` 逐字节一致；不传第二参数时旧界面仍可构建 |
| `web_demo.py`（UTF-8） | 仅作业1 处注入 `function_hw1_compare` | 作业2~5 接线未动（前端渲染测试仍 13/13） |
| `tests/test_hw1.py` | 46 → **89** 项（新增 4 个测试类） | 见 I4 |
| `tests/test_hw1_ui_contract.py`（新增） | 8 项：hw2~hw5 与基线一致 + `UI.py` 编码契约 + 作业1 改动确实存在 | **取代**旧的"`git diff main -- UI.py functions.py` 必须为空"判定（见 `AGENTS.md` §5） |
| `tests/ui_smoke_hw1.py` | 冒烟 12 → **23** 项；端口被占用时 **rc=2 直接退出** | 见 I5 踩坑① |
| `reports/hw1/make_report.py` + 产物（新增） | 报告材料：四联对比图、PS 曲线图、自然饱和度增益图、`metrics.md`、自包含 `hw1_report.html`、`hw1_report.pdf`、界面截图 | 所有数值当场实算，不手填 |
| `AGENTS.md` §4/§5 | 补"官方路径必须真调用 cv2""进阶功能诚实性""减对比必须双向有效"；判定标准改为契约测试 | |

### I2 · 五个模式与数学定义

| 模式 | 数学定义 | 性质 |
| --- | --- | --- |
| 色相/饱和度 | 课件 HSL(HSI)：`L=(R+G+B)/3`、`S=1-3min/Σ`、`H∈[0,360)`；逆变换用课件 p78 分段公式；明度乘性 `L'=L(1+l)` | 浮点往返，默认参数**严格逐像素相等** |
| 色相/饱和度 (官方cv2 HLS) | 直接 `cv2.COLOR_BGR2HLS`/`COLOR_HLS2BGR`：`L=(max+min)/2`、`S=(max-min)/(max+min)` | 内部 8 位量化，恒等往返 ≤1 LSB |
| 自然饱和度 (PS vibrance) | `gain(S)=1+amount·(1-S)²`，`S'=clip(S·gain)`（用饱和度滑杆当强度，忽略色相/明度） | S=1 与 S=0 完全不动 |
| 亮度/对比度 | 线性 `(x-0.5)(1+c)+0.5+b` | 基础功能（**不是** PS 拟合） |
| 亮度/对比度 (PS风格) | 对比度：`a>0` → `0.5+0.5tanh(a(x-0.5))/tanh(a/2)`；`a<0` → 同强度正曲线的**反函数**；亮度：`x^γ`，`γ=2^(-2b)` | 0/0.5/1 三点锚定；不裁剪 |

### I3 · 关键实测数据（`reports/hw1/metrics.md`，测试图为 192×256 色相×饱和度网格 + 灰阶）

两条路径的**空间定义对照**（说明"两套模型本来不同"）：

| 颜色 | 手写 HSL | 官方 cv2 HLS |
| --- | --- | --- |
| 纯红 (255,0,0) | H=0.00° S=1.0000 **L=0.3333** | H=0.00° S=1.0000 **L=0.5020** |
| 纯黄 (255,255,0) | H=60.00° S=1.0000 **L=0.6667** | H=60.00° S=1.0000 **L=0.5020** |
| 中灰 (128,128,128) | H=0.00° S=0.0000 L=0.5020 | H=0.00° S=0.0000 L=0.5020（重合） |

**输出层误差（MAE / 最大误差 / PSNR）**：

| 参数 | MAE | max | PSNR |
| --- | --- | --- | --- |
| 默认参数（恒等） | 0.520 | 5 | 48.46 dB |
| 色相 +90° | 13.276 | 79 | 21.42 dB |
| 饱和度 ×1.5 | 8.235 | 53 | 24.83 dB |
| 饱和度 ×2 | 12.551 | 79 | 21.26 dB |
| 亮度 ×1.5 | **39.227** | 129 | 12.67 dB |

**量化往返（原图 → 空间 → 原图）**：手写 **0.000 / 0（严格相等）**；官方 0.520 / 5（8 位 HLS 量化）。
→ 结论：模型差异远大于量化误差（默认参数下 0.52 全由量化贡献；一旦出现参数，误差跳一个数量级）。

**PS 风格标定**（最小二乘拟合"同中灰斜率的线性斜坡"，a 上限 ±4）：

| 目标斜率 | 拟合 a | RMS | max |
| --- | --- | --- | --- |
| 0.6 | −4.0000（触上限） | 0.04319 | 0.20000 |
| 0.8 | −2.4811 | 0.02709 | 0.10000 |
| 1.0 | 0.0000 | 0.00000 | 0.00000 |
| 1.2 | +2.1303 | 0.01930 | 0.04848 |
| 1.5 | +3.4733 | 0.02791 | 0.06241 |
| 2.0 | +4.0000（触上限） | 0.04424 | 0.10389 |

**中灰斜率**：`c=-1 → 0.4820`、`-0.5 → 0.7616`、`0 → 1.0000`、`+0.5 → 1.3130`、`+1 → 2.0746`
（正负互为倒数；像素域锚点：1/4 灰 64 → c=+1 得 27、c=−1 得 94；3/4 灰 192 → c=−1 得 161）。

**自然饱和度**：`amount=+1` 时增益 `S=0.25→1.562`、`0.50→1.250`、`0.75→1.062`、`1.00→1.000`；
`amount=-1` 时 `0.25→0.438`（降饱和）；纯红/灰/白三种边界像素逐像素不变。

### I4 · 测试结果（本轮实际输出）

| 项目 | 命令 | 结果 |
| --- | --- | --- |
| 全量（数组层+兼容层+契约） | `python -m unittest discover -s tests` | **116 tests OK**（1.34 s） |
| 作业1 数组层 | `python tests/test_hw1.py` | **89/89 OK**（0.205 s） |
| 作业1 改动范围契约（新增） | `python tests/test_hw1_ui_contract.py` | **8/8 OK** |
| 作业1 界面冒烟（新增项） | `python tests/ui_smoke_hw1.py --port 8093` | **23/23 PASS** |
| 前端真实渲染（完整程序） | `python tests/test_frontend_render.py` | **13/13 PASS**（DOM 116268 bytes） |
| 报告材料生成 | `python reports/hw1/make_report.py` | 图/表/HTML(1.60 MB)/PDF(1.78 MB) 全部生成；界面截图 92 239 bytes |

界面冒烟实测（节选）：

```
mode choices: ['色相/饱和度', '色相/饱和度 (官方cv2 HLS)', '自然饱和度 (PS vibrance)',
               '亮度/对比度', '亮度/对比度 (PS风格)']
compare fn_index: 2                     # 4 输入 / 2 输出的对比事件已注册
[PASS] official HLS hue +180: got=[1 255 255] expect=(1, 255, 255)
[PASS] PS tone gray brightness +0.5: got=181 expect=175..185
[PASS] vibrance keeps gray: got=[128 128 128] expect=(128, 128, 128)
compare figure shape: (32, 140, 3)      # 4×(32) + 3×4 分隔条
UI smoke: 23/23 PASS
```

### I5 · 本轮踩坑与发现（供复用）

1. **端口占用会造成"假通过"**：8088 上是一个**阶段 H 留下的旧服务实例**（PID 35500，非本阶段启动，
   未去动它）。冒烟脚本连上旧实例后，"恒等/亮度/色相/饱和度"4 项仍打印 PASS，但模式列表只有 2 项、
   对比事件不存在 → 已给 `tests/ui_smoke_hw1.py` 加"端口被占用即 rc=2 退出"的护栏，并固定用 8093 验证新代码。
2. **cv2 8 位 HLS 的"恒等"不是严格恒等**：纯红恒等得到 `(255,1,1)` —— `L=(255+0)/2=127.5→128`，
   逆变换 `min=L(1-S)=1/255`。属官方库量化误差，已在测试与报告中显式说明，不再当作实现错误。
3. **PS 风格对比度对 `a` 是偶函数（真缺陷，已修复）**：原公式
   `0.5+0.5tanh(a(x-0.5))/tanh(a/2)` 里分子分母同时变号，导致 **`a<0` 与 `a>0` 完全同曲线**——
   "减对比"实际变成了"增对比"。修复：`a<0` 改用**同强度正曲线的反函数**
   `y=0.5+artanh((2x-1)tanh(k/2))/k`（`k=|a|`），中灰斜率由 1 降到 0.4820；标定搜索区间扩展到 `[-4,4]`；
   补 3 项回归测试（含"减对比 ≠ 增对比"的偶函数防护）。旧注释写的是"a<0 变平"，
   说明**注释正确但实现错的缺陷不会被静态阅读发现，只能靠性质测试**。
4. Gradio 预览图有损压缩，**不能**作为像素判据；界面冒烟一律在返回的 PNG 解码后做数组断言。

### I6 · 诚实声明与局限（须与报告一致）

- `PS 风格` 两个功能**未与真实 Photoshop 比对**（本机未安装 PS）：验证的是本实现自洽的数学性质
  （锚点、单调性、解析斜率、标定残差、边界不动），**不是**"与 PS 一致"。
- 对比度参数上限 `a=±4`：中灰斜率可达区间约 `[0.482, 2.075]`，目标斜率 2.0 与 0.6 都会触上限（表中已标出）。
- 两条路径的 H/S/L **不可直接互比**；报告只比较"最终 RGB 输出"与"换算到同一空间后的 H/S/L"，
  并把量化往返误差单列，**不判定**哪种实现"更准确"。
- 界面证据为**无头浏览器截图 + DOM 渲染测试**，属自动化；**人工浏览器交互验收仍需用户完成**
  （步骤见 `tests/README.md`：`python tests/ui_smoke_hw1.py --serve` 或 `start_hw1_demo.bat`）。
- 8088 端口上的旧服务实例仍在运行（阶段 H 遗留），用户如看到旧界面请关闭该窗口后用新端口/脚本重启。

### I7 · 下一步

- 用户在本机浏览器人工验收作业1 的 5 个模式与对比实验按钮（确认后本阶段闭环）。
- 之后进入作业2 `function_hw2`（本阶段**未**触碰作业2~5 的业务逻辑）。

