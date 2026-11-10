# 前端 · WatchHealth-LSTM 健康看板

Mira Bio 风格的 5 页健康看板 + 404。由 FastAPI 直接托管，**无 npm、无构建、可断网**。

## 运行

```powershell
# 在仓库根目录
Push-Location backend; ..\.venv\Scripts\python.exe main.py; Pop-Location
# 打开 http://localhost:8000
```

页面必须通过后端访问（`file://` 打不开：需要 `/api/*` 与 `/static/*`）。

## 文件

| 文件 | 作用 |
|---|---|
| `index.html` | 页面 + 样式 + 逻辑（单文件，hash 路由） |
| `fonts.css` | Geist / Geist Mono（base64 内嵌，离线可用） |
| `lib/echarts.min.js` | 旧版看板遗留，新页面**不再引用** |

## 路由

`#/overview` 总览 · `#/biomarkers` 指标 · `#/sleep` 睡眠 · `#/plan` 计划 ·
`#/care` 本地模型 · `#/404`

## 数据来源

| 接口 | 用途 |
|---|---|
| `GET /api/demo` | 测试用户 #5 最近 14 天窗口（7 项真实指标 + `actual_next`） |
| `POST /api/predict` | LSTM 明日压力/疲劳、HRV 异常、简报 |
| `POST /api/chat` | 本地规则对话（不联网，按关键词 + 当前指标回复） |

页面加载即拉取 `/api/demo` 并自动跑一次预测；「刷新预测」按钮会重新调用 `/api/predict`。
对话输入会 POST 到 `/api/chat`，右侧「平均延迟」为实测请求耗时。

## 真实数据 vs 示例数据

- **真实（来自接口）**：静息心率、心率变异性、深睡、快速眼动、步数、久坐、自评压力、
  14 天趋势、明日预测、HRV 预警、模型简报、对话、延迟。
- **示例（页面已标注）**：其余 10 项指标（`· 示例`）、睡眠阶段/评分/就寝时间、
  今日清单/补剂、生物年龄、复盘排期。这些模块暂无对应数据字段，不要当成真实测量。

## 改版注意

- 品牌保持 `WatchHealth-LSTM`，logo 用 `W`；界面文案中文，称呼用户为“主人”。
- 单文件优先，不引 CDN/在线字体；新增交互保留 `aria-label`。
- 改完刷新即可，无构建步骤。
- 预览版仍在 `presentation/index.html`，与本目录是两份独立实现。
