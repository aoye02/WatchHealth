# AGENTS.md · 项目协作与代码规范

> **【强制】任何 AI / 自动化代理进入本仓库，必须先完整读完本文件，再执行任何操作**
> （读代码、改文件、跑命令、生成文档、给出结论都算）。没读完不得动手。
>
> 1. 优先级：**用户当次指令 > 本文件 > 其他文档**。冲突时按用户执行，并在结束后更新本文件。
> 2. 本文件上限 200 行；内容过期直接改写，不要层层追加。
> 3. 边界不清（该改哪个目录、能不能动后端/数据）时先问，不要猜。
> 4. 交流、注释、文档、提交信息一律用中文（代码标识符、类名除外）。

---

## 1. 项目是什么

深度学习课程演示项目：**用智能手表 7 维时序数据预测「明日压力 / 疲劳」**，并提供 HRV 异常预警与健康简报。
数据当前为**合成演示数据**（`synthesize_demo_data.py` 生成，6 人 × 60 天），真实数据（WESAD + 组员自采集）尚未接入。
评估口径：**留一用户**（5 人训练 / 1 人测试，测试用户 `user_id=5` 模型从未见过）。

## 2. 技术栈与环境（已实测）

| 项 | 值 |
|---|---|
| Python | 3.13.5，虚拟环境在 `.venv/`（`torch 2.15.0+cpu`、`fastapi 0.162.2`） |
| 模型 | PyTorch 多变量 LSTM：7 天窗口 × 7 特征，hidden=64，2 层，约 5.4 万参数 |
| 后端 | FastAPI + Uvicorn，单文件 `backend/main.py`，同时托管前端 |
| 前端 | 原生 HTML/CSS/JS 单文件（**无 npm、无构建、无 CDN**） |
| LLM | 讯飞星火 HTTP（`SPARK_API_PASSWORD`），无 key 时本地模板兜底 |
| 平台 | Windows + PowerShell；读写 UTF-8，读中文文件要加 `-Encoding UTF8` |

## 3. 目录职责

| 路径 | 职责 | 改动注意 |
|---|---|---|
| `model/` | 数据生成、训练、实验、推理、异常检测 | `data_utils.py` 是口径唯一来源 |
| `backend/` | `/api/demo`、`/api/predict`、静态托管 | 改契约必须同步前端与本文档 |
| `frontend/` | 正式看板（单页，调用 `/api/*`） | 品牌保持 WatchHealth-LSTM |
| `presentation/` | PPT 材料 + 评审用静态预览 `index.html` | 预览是独立成品，与 `frontend/` 不共享代码 |
| `data/processed/` | `demo_data.csv`、`mu.csv`、`sigma.csv` | 由脚本生成，不手工改 |
| `data/raw/` | WESAD / 自采集原始数据 | 体积大，**不要提交、不要自动下载** |
| `experiment/` | 结果表与图（PPT 数字来源） | 由 `run_experiments.py` 生成 |
| `need/` | 需求文档 | 只读，不要修改 |

## 4. 运行命令（在仓库根目录）

```powershell
.\.venv\Scripts\python.exe model\synthesize_demo_data.py   # 生成合成数据
.\.venv\Scripts\python.exe model\train.py                   # 训练，写 best_lstm.pth / mu / sigma / loss_curve
.\.venv\Scripts\python.exe model\run_experiments.py         # 复现 PPT 全部实验数字
.\.venv\Scripts\python.exe model\predict.py                 # 单条推理自测
Push-Location backend; ..\.venv\Scripts\python.exe main.py; Pop-Location   # 起服务 :8000
```

- 看板：<http://localhost:8000>；接口文档：`/docs`；健康检查：`/api/health`。
- 预览：直接双击 `presentation/index.html`（`file://` 可跑，零网络请求）。
- `frontend/index.html` **不能**用 `file://` 打开（需要 `/api/*` 与 `/static/fonts.css`）。

## 5. 数据契约（不得随意改）

`GET /api/demo?start=18&end=31` → `{ user_id, history[14], actual_next }`
`history[i]` 含：`resting_hr, hrv_rmssd, deep_sleep_min, rem_min, steps, sedentary_min, prev_stress, next_stress`。

`POST /api/predict`，请求 `{ "stats_7day": { "日期": {7 个特征} }, "hrv_series": [数值] }` →
`{ prediction:{stress,fatigue,advice}, anomaly:{alert,current_hrv,baseline_hrv,drop_pct,z_score,message}, brief:{text,source} }`。

- 特征顺序（三处定义，必须同步）：`model/data_utils.py`、`model/predict.py`、`backend/main.py`。
- `SEQ_LEN=7`；`predict.py` 把输出裁到 `1–10`，疲劳 = `stress × 0.9`；建议阈值 7 / 4.5。
- 异常检测：窗口 7、`z < -2.5` 且降幅 >15%，数据不足返回 `alert=false`。
- 演示口径（PPT / 口播 / 页面必须一致）：预测 **8.5**、疲劳 **7.6**、真实自评 **8.47**、HRV 基线 **46.4→23.7（−49%，z≈−5.4）**、深睡 **47**、久坐 **824**、步数 **5,598**、测试集 **MAE 0.729**。

## 6. 已踩过的坑（务必遵守）

1. **数据没有日期列**：`demo_data.csv` 按行=天，无 `date` 字段。界面**不得**把日期/天数当成数据事实（如 `2026-11-10`、“期末周第 N 天”、`11-17`）；只能用相对表达（最近 14 天 / 昨夜）、标注“展示约定/示例”，或先让后端补 `date`。
2. **“期末周”是合成出来的**：生成器只在第 30–37 天加 `stress_wave=2.5`；窗口 18–31 的最后一天是模拟期末周第 2 天。不要把它说成真实日历。
3. **标准化不许泄漏**：`mu/sigma` 只能由训练用户拟合（`fit_scaler(X[tr])`），测试用户只 transform。
4. **`best_lstm.pth` 已被 git 跟踪**，重训会覆盖；未被要求时不要重训，重训后指标可能有 ±0.01 波动，需同步 `experiment/results.csv`。
5. **根目录已有 `.gitignore`**：`__pycache__/`、`*.pyc`、`.venv/`、`data/raw/`、`.env*`、系统/编辑器/临时文件都已忽略；`backend/__pycache__`、`model/__pycache__` 已 `git rm --cached`。**不要**把缓存、虚拟环境、原始数据再加回来。
6. **示例数据必须标注**：睡眠阶段、计划、补剂、生物年龄、其余 10 项指标都是占位内容，必须保留“示例/占位”标记，不能伪装成真实结果。
7. **不要把“待接入”写成已完成**：预约只是本地记录（刷新丢失），不要宣称已对接排期；聊天与刷新预测已实现，不要退回占位。
8. **前端两份实现互不依赖**：改 `presentation/` 不要顺手改 `frontend/`；反之亦然。

## 7. 代码风格

**Python**
- 4 空格缩进；`snake_case` 函数/变量，`UPPER_CASE` 常量，类名 `PascalCase`。
- 文件头写中文 docstring：说明用途、输入输出、为什么这样设计（答辩可直接引用）。
- 路径一律 `pathlib.Path(__file__).resolve().parent...`，**禁止**硬编码绝对路径。
- 特征名、目标名、窗口长度用常量，不要散落魔法数。
- 依赖已有的 `data_utils` 口径，不要复制训练/标准化逻辑。
- 异常处理要兜底可演示：外部 API 失败必须回退本地模板，演示不能崩。

**前端（原生 HTML/CSS/JS）**
- 单文件优先，无框架、无 CDN、无构建；断网必须可用。
- 2 空格缩进；CSS 自定义属性集中在 `:root`；组件用语义类名（`.card`、`.chip`、`.mrow`、`.checkrow`）。
- 颜色/字号不写死零散值，优先复用 token。
- 交互必须有可访问名称（`aria-label`）、键盘可用、尊重 `prefers-reduced-motion`。
- 图表用内联 SVG，**不要**引外链字体/图表库。

**通用**
- 命名、注释跟着所在文件现有风格走；不重排无关代码，不制造无关 diff。
- 新增依赖要先问；能用标准库解决就不加包。

## 8. 产品与文案约定（界面口径）

- **界面全中文**：标签、单位、状态、表格头、Toast、`aria-label` 都要中文（品牌与代码标识符除外）。
  单位：`次/分`、`毫秒`、`分钟`、`小时`、`℃`；状态：`达标 / 关注 / 偏低`；
  术语：`HRV→心率变异性`、`REM→快速眼动`、`LSTM→长短期记忆网络`、`MAE→平均绝对误差`。
- **对话/问候把用户称为“主人”**（首屏问候、模型消息、简报、404）。
- 品牌统一用 `WatchHealth-LSTM`，logo 用 `W`（不翻译）。
- 前端固定 6 个路由：`#/overview`、`#/biomarkers`、`#/sleep`、`#/plan`、`#/care`、`#/404`。
- 设计基线：浅色 `#EFEFEE`、主文字 `#0F110F`、强调青柠 `#D7F43A`、暗卡橄榄渐变、32px 圆角卡片、mono 小标签；桌面/平板/手机三档，手机底部标签栏。
- 两个必保功能：**本地模型聊天**（`#/care`）与**明日状态预测**（Overview 的 Prediction Card），任何改版不得删减。

## 9. 改动流程

1. 读本文件 + 相关目录代码，确认改哪一层（model / backend / frontend / presentation）。
2. 只做被要求的最小改动；跨层改动先说明影响面。
3. 自检：
   - Python：`.\.venv\Scripts\python.exe -m py_compile <改动的 .py>`；涉及接口则起服务请求一次 `/api/health` 与目标接口。
   - 前端：浏览器逐页走 6 个路由，检查文案、换行、横向滚动、控制台报错、筛选/勾选/发送/刷新预测是否正常。
   - 数据类改动：核对 `experiment/results.csv` 与页面/PPT 数字一致。
4. 同步文档：`README.md`、`presentation/前端功能盘点与预览说明.md`、`presentation/assets/preview/*.png` 截图、本文件。
   **若用户限制“只改某文件”，遵守限制，但必须在回复里指出哪些文档/截图已过期。**
5. 汇报时写清：改了什么、为什么、怎么验证、遗留风险。

## 10. 提交规范

- 提交信息中文，格式 `类型: 简述`（`新增` / `修复` / `文档` / `重构` / `样式` / `杂项`）。
- 一次提交只做一件事；不混入格式化全文件、删除无关代码。
- 提交前 `git status` 自查：不带上 `.venv/`、`__pycache__/`、`data/raw/`、临时截图、编辑器文件。
- `model/best_lstm.pth`、`data/processed/*.csv`、`experiment/*` 属于产物：非必要不改；确需更新要在提交说明里写明原因与指标变化。

## 11. 禁止事项（红线）

- ❌ 改 `data/processed/` 的原始数值来“让图好看”。
- ❌ 在界面/文档里写没有字段来源的日期、天数、指标值。
- ❌ 删除或弱化「本地模型聊天」「明日状态预测」。
- ❌ 引入需要联网的 CDN、在线字体、在线图表库。
- ❌ 未经确认修改 `frontend/`、`backend/` 契约、`need/` 需求文档、PPT/DOCX 成品。
- ❌ 把示例数据描述成真实测量结果，或把未接入的功能说成已完成。
