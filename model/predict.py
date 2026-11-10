"""
predict.py
加载 best_lstm.pth，输入 7 天序列，输出明日压力分
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import torch

sys.path.append(str(Path(__file__).resolve().parent))
from lstm_model import MultiVarLSTM  # noqa: E402

FEATURES = ["resting_hr", "hrv_rmssd", "deep_sleep_min", "rem_min",
            "steps", "sedentary_min", "prev_stress"]
SEQ_LEN = 7


def load_model():
    root = Path(__file__).resolve().parent.parent
    model_path = Path(__file__).parent / "best_lstm.pth"
    if not model_path.exists():
        raise FileNotFoundError("先运行 train.py 训练模型")
    model = MultiVarLSTM()
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()
    mu = pd.read_csv(root / "data" / "processed" / "mu.csv", index_col=0).iloc[:, 0]
    sigma = pd.read_csv(root / "data" / "processed" / "sigma.csv", index_col=0).iloc[:, 0]
    return model, mu, sigma


def predict_next(stats_7day: dict) -> dict:
    """
    stats_7day: dict, key 是日期，value 是 dict 含 7 个特征
    返回: {"stress": float, "fatigue": float, "advice": str}
    """
    model, mu, sigma = load_model()
    df = pd.DataFrame(stats_7day).T[FEATURES].astype(float)
    df = (df - mu) / sigma
    x = torch.tensor(df.values, dtype=torch.float32).unsqueeze(0)  # (1,7,7)
    with torch.no_grad():
        stress = float(model(x).item())
    stress = float(np.clip(stress, 1, 10))
    fatigue = round(stress * 0.9, 2)  # 简化：疲劳分与压力相关
    if stress >= 7:
        advice = "压力偏高，推荐轻运动（瑜伽/散步），避免高强度间歇，今晚 23:30 前入睡"
    elif stress >= 4.5:
        advice = "状态中等，可正常学习，适度运动 30 分钟"
    else:
        advice = "状态良好，可安排高强度任务或运动"
    return {"stress": round(stress, 2), "fatigue": fatigue, "advice": advice}


if __name__ == "__main__":
    # 用最后 7 天合成数据测试
    root = Path(__file__).resolve().parent.parent
    df = pd.read_csv(root / "data" / "processed" / "demo_data.csv")
    last7 = df.tail(SEQ_LEN)[FEATURES]
    fake_input = {f"day-{i}": row for i, row in enumerate(last7.to_dict("records"))}
    out = predict_next(fake_input)
    print("预测结果:", out)