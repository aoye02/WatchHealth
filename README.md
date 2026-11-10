# WatchHealth-LSTM

> 把智能手表的数据真正用起来 —— 基于多变量 LSTM 的大学生次日压力/疲劳预测与 AI 健康简报系统
> 深度学习课程 Presentation ｜ 广州商学院 人工智能学院

---

## 这是什么
现在大学生几乎人手一块智能手表，但手表只告诉你"今天睡了 6 小时"，不会告诉你"明天你会很累，今天早点睡"。
我们用 **多变量 LSTM** 分析过去 7 天的心率 / HRV / 深睡 / 步数等 7 维时序数据，**预测明天的压力指数和疲劳指数**，并通过**讯飞星火大模型**生成一段人话的健康简报。

## 目录结构
```
WatchHealth-LSTM/
├─ README.md                  ← 你正在看
├─ data/
│  ├─ raw/WESAD/              ← 公开数据集（组员 A 下载）
│  ├─ raw/self_collect/       ← 组员手表自采集 csv
│  └─ processed/              ← 清洗后训练数据
├─ model/                     ← 核心模型（袁志强主操）
│  ├─ lstm_model.py           ← LSTM 网络定义
│  ├─ data_utils.py           ← 数据划分（留一用户）+ 标准化（仅训练集拟合）
│  ├─ synthesize_demo_data.py ← 生成演示用合成数据（先跑通 pipeline）
│  ├─ train.py                ← 训练最终模型
│  ├─ run_experiments.py      ← 一键复现 PPT 全部实验数字（含 baseline/消融/特征重要性）
│  ├─ predict.py              ← 推理：输入 7 天序列 → 输出明日压力
│  ├─ anomaly_detect.py       ← HRV 骤降异常检测（滑动窗口 z-score）
│  └─ best_lstm.pth           ← 训练好的权重（训练后生成）
├─ backend/                   ← FastAPI 后端（托管演示看板）
│  ├─ main.py
│  ├─ llm_prompt.py           ← 讯飞星火 HTTP 接入 + 本地模板兜底
│  └─ requirements.txt
├─ frontend/                  ← 演示看板（单页 HTML + 本地 ECharts，无需 npm）
│  ├─ index.html
│  └─ lib/echarts.min.js      ← 已本地化，断网可演示
├─ presentation/              ← PPT 全套材料（重点！）
│  ├─ slide_content.md        ← PPT 逐页文字
│  ├─ PPT_script.md           ← 演讲稿
│  ├─ demo_notes.md           ← 现场演示避坑手册 + 答辩 Q&A
│  └─ 分工表.md
└─ experiment/                ← loss 曲线、模型对比图、特征重要性图、results.csv
```

## 快速启动（3 步跑通）
```bash
# 1. 安装依赖
pip install -r backend/requirements.txt

# 2. 先生成合成演示数据并训练（不依赖 WESAD，先跑通）
cd model
python synthesize_demo_data.py   # 生成 data/processed/demo_data.csv
python train.py                  # 训练最终模型，输出 experiment/loss_curve.png
python run_experiments.py        # 复现 PPT 全部实验数字：baseline 对比 + 消融 + 特征重要性
python predict.py                # 测试单条预测

# 3. 启动后端（看板由后端托管，无需 npm）
cd ../backend
uvicorn main:app --port 8000
# 浏览器打开 http://localhost:8000 看演示看板，/docs 看接口
# 可选：设置环境变量 SPARK_API_PASSWORD 后，AI 简报走讯飞星火实时生成
```

## 技术栈
- **模型**：PyTorch LSTM（2 层，hidden=64，参数量 5.4 万）
- **后端**：FastAPI + Uvicorn
- **前端**：单页 HTML + ECharts（已本地化，断网可演示）
- **LLM**：讯飞星火（spark-lite HTTP 接口，无 key 时本地模板兜底）
- **数据**：WESAD 公开集 + 6 人 × 14 天自采集 + 合成演示数据
- **评估**：留一用户验证（5 人训练 / 1 人测试），标准化仅用训练集拟合
