"""
main.py
FastAPI 后端：演示看板（单页前端）+ LSTM 预测 + HRV 异常检测 + AI 简报
启动: uvicorn main:app --port 8000
打开 http://localhost:8000 即是演示看板（前端由后端直接托管，无需 npm）
"""
import json
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "model"))
sys.path.append(str(Path(__file__).resolve().parent))

from predict import predict_next            # noqa: E402
from anomaly_detect import detect_hrv_drop  # noqa: E402
from llm_prompt import generate_brief       # noqa: E402

app = FastAPI(title="WatchHealth-LSTM API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

FRONTEND_DIR = ROOT / "frontend"
FEATURES = ["resting_hr", "hrv_rmssd", "deep_sleep_min", "rem_min",
            "steps", "sedentary_min", "prev_stress"]


class PredictReq(BaseModel):
    stats_7day: dict   # {date: {resting_hr, hrv_rmssd, ...}}
    hrv_series: list   # 过去 N 天 HRV 列表


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "WatchHealth-LSTM"}


@app.get("/api/demo")
def demo(start: int = 18, end: int = 31):
    """返回演示用户（测试用户）的一段 14 天数据供看板画图。
    默认窗口第 18~31 天：覆盖期末压力周开始、HRV 骤降的时刻，
    演示时能看到"预测压力飙升 + 红色预警"的完整故事。
    该用户是训练时留一法留出的测试用户，模型从未见过。"""
    import pandas as pd
    csv = ROOT / "data" / "processed" / "demo_data.csv"
    if not csv.exists():
        return {"error": "先运行 python model/synthesize_demo_data.py"}
    df = pd.read_csv(csv)
    test_user = int(df["user_id"].max())
    u = df[df["user_id"] == test_user].reset_index(drop=True)
    g = u.iloc[start:end + 1]
    # to_json 再 loads，避免 numpy 类型导致 JSON 序列化失败
    records = json.loads(g[FEATURES + ["next_stress"]].to_json(orient="records"))
    # 窗口次日（第 end+1 天）的真实自评压力，用于"预测 vs 真实"对比
    actual_next = float(u["next_stress"].iloc[end + 1]) if end + 1 < len(u) else None
    return {"user_id": test_user, "history": records, "actual_next": actual_next}


@app.post("/api/predict")
def predict(req: PredictReq):
    # 1. LSTM 预测明日压力
    pred = predict_next(req.stats_7day)
    # 2. HRV 异常检测（滑动窗口 z-score）
    anomaly = detect_hrv_drop(req.hrv_series)
    # 3. 讯飞星火生成健康简报（无 key 时本地模板兜底）
    brief = generate_brief(pred, anomaly)
    return {
        "prediction": pred,
        "anomaly": anomaly,
        "brief": brief,
    }


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
