# 演示看板（单页 HTML + ECharts）

不需要 npm、不需要 Vue 工程化——后端 FastAPI 直接托管这个页面，
`uvicorn main:app --port 8000` 启动后访问 **http://localhost:8000** 即可。

## 文件
- `index.html`：看板页面（样式 + 图表 + 交互全在这一个文件里，方便组员 B 讲解）
- `lib/echarts.min.js`：ECharts 已本地化，**教室断网也能演示**

## 页面结构
1. 中部：4 条 ECharts 折线（静息心率 / HRV / 深睡 / 步数），数据来自 `GET /api/demo`
2. 右侧：
   - 「生成明日预测」按钮 → `POST /api/predict`
   - 预测卡片：明日压力分（大数字 + 档位标签）、疲劳分、建议
   - 红色预警卡片：HRV 骤降时显示（z-score + 降幅）
   - AI 简报卡片：讯飞星火生成，右下角标注来源（spark 实时生成 / template 本地兜底）

## 演示数据说明
`/api/demo` 默认返回测试用户（user 5，模型训练时没见过）第 18~31 天——
期末压力周开始、HRV 骤降的 14 天，演示效果最佳。
可用 `/api/demo?start=0&end=13` 查看其他窗口。
