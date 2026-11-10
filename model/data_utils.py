"""
data_utils.py
数据加载、滑窗构造、留一用户划分训练/测试集、仅用训练集拟合标准化。
train.py 与 run_experiments.py 共用，保证口径一致。

为什么这样设计（答辩可直接引用）：
1. 用"留一用户"划分（5 人训练 / 1 人测试）——检验模型对"没见过的人"的泛化，
   这才是真实使用场景（新用户戴上表，模型就要工作）；
2. 测试用户保留完整 60 天 —— 测试期覆盖平稳期和"期末压力周"，
   若只测平稳期，目标方差太小，R² 会失去区分度；
3. 标准化的 mu/sigma 只用训练用户拟合 —— 用全量数据统计量会造成测试集信息泄漏。
"""
from pathlib import Path

import numpy as np
import pandas as pd

FEATURES = ["resting_hr", "hrv_rmssd", "deep_sleep_min", "rem_min",
            "steps", "sedentary_min", "prev_stress"]
TARGET = "next_stress"
SEQ_LEN = 7


def load_demo_csv() -> pd.DataFrame:
    csv = Path(__file__).resolve().parent.parent / "data" / "processed" / "demo_data.csv"
    if not csv.exists():
        raise FileNotFoundError("先运行 python model/synthesize_demo_data.py 生成数据")
    return pd.read_csv(csv)


def build_sequences(df: pd.DataFrame, seq_len: int = SEQ_LEN):
    """
    构造滑窗样本。返回:
      X: (N, seq_len, 7) 原始量纲
      y: (N,) 次日压力分
      owners: 长度为 N 的 (user_id, 目标日下标) 列表，用于按时间划分
    """
    Xs, ys, owners = [], [], []
    for uid, g in df.groupby("user_id"):
        g = g.reset_index(drop=True)
        feats = g[FEATURES].values.astype(float)
        tgt = g[TARGET].values.astype(float)
        for i in range(seq_len, len(g)):
            Xs.append(feats[i - seq_len:i])
            ys.append(tgt[i])
            owners.append((uid, i))
    return np.array(Xs, dtype=np.float32), np.array(ys, dtype=np.float32), owners


def user_split(owners, test_user=None):
    """留一用户划分：test_user 的全部样本作测试集，其余用户作训练集。
    默认用最大 user_id 作测试用户（与 train.py / predict.py 的演示口径一致）。"""
    if test_user is None:
        test_user = max(uid for uid, _ in owners)
    train_idx = [k for k, (uid, _) in enumerate(owners) if uid != test_user]
    test_idx = [k for k, (uid, _) in enumerate(owners) if uid == test_user]
    return train_idx, test_idx


def fit_scaler(X_train: np.ndarray):
    """只用训练集拟合标准化参数。X_train: (N, seq_len, 7)"""
    flat = X_train.reshape(-1, X_train.shape[-1])
    mu = flat.mean(axis=0)
    sigma = flat.std(axis=0) + 1e-8
    return mu, sigma


def apply_scaler(X: np.ndarray, mu, sigma) -> np.ndarray:
    return ((X - mu) / sigma).astype(np.float32)


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    err = y_pred - y_true
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err ** 2)))
    ss_res = float(np.sum(err ** 2))
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"MAE": round(mae, 3), "RMSE": round(rmse, 3), "R2": round(r2, 3)}
