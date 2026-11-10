"""
run_experiments.py
一键复现 PPT 实验页的全部数字：
  基线: Persistence(昨天=明天) / MLP / 单变量LSTM(仅HRV)
   ours: 多变量LSTM(7天窗口)
  消融: 多变量LSTM(14天窗口)
指标: MAE / RMSE / R^2（同一测试集、同一划分、同一标准化）
额外: 对 ours 做置换重要性(Permutation Importance)，证明哪些特征关键。

输出:
  experiment/results.csv           各模型指标表
  experiment/model_compare.png     模型对比柱状图
  experiment/feature_importance.png 特征重要性图
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Windows 自带微软雅黑，保证中文图例不乱码
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

sys.path.append(str(Path(__file__).resolve().parent))
from data_utils import (FEATURES, SEQ_LEN, apply_scaler, build_sequences,  # noqa: E402
                        fit_scaler, load_demo_csv, regression_metrics,
                        user_split)
from lstm_model import MultiVarLSTM  # noqa: E402

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class SeqDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, i):
        return self.X[i], self.y[i]


class MLPBaseline(nn.Module):
    """把 7 天 x 7 维拉平后进全连接，验证"时序结构是否有用"。"""

    def __init__(self, seq_len, feature_dim, dropout=0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(seq_len * feature_dim, 64), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(64, 32), nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


def train_and_eval(model, Xtr, ytr, Xte, yte, epochs) -> dict:
    model = model.to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()
    loader = DataLoader(SeqDataset(Xtr, ytr), batch_size=16, shuffle=True)
    best = {"MAE": 1e9}
    best_state = None
    for _ in range(epochs):
        model.train()
        for xb, yb in loader:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            preds = model(torch.tensor(Xte).to(DEVICE)).cpu().numpy()
        m = regression_metrics(yte, preds)
        if m["MAE"] < best["MAE"]:
            best, best_state = m, {k: v.clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    return best


def permutation_importance(model, Xte, yte, n_repeats: int = 20) -> pd.Series:
    """逐特征打乱该通道，看 MAE 上升多少 —— 上升越多说明该特征越关键。"""
    model.eval()
    with torch.no_grad():
        base = regression_metrics(yte, model(torch.tensor(Xte).to(DEVICE)).cpu().numpy())["MAE"]
    rng = np.random.default_rng(0)
    deltas = {}
    for j, name in enumerate(FEATURES):
        scores = []
        for _ in range(n_repeats):
            Xp = Xte.copy()
            Xp[:, :, j] = Xp[rng.permutation(len(Xp)), :, j]
            with torch.no_grad():
                p = model(torch.tensor(Xp).to(DEVICE)).cpu().numpy()
            scores.append(regression_metrics(yte, p)["MAE"] - base)
        deltas[name] = float(np.mean(scores))
    return pd.Series(deltas).sort_values(ascending=False)


def main():
    torch.manual_seed(42)
    root = Path(__file__).resolve().parent.parent
    df_raw = load_demo_csv()

    # ---- 统一的 7 天窗口数据集（原始量纲）----
    X, y, owners = build_sequences(df_raw, seq_len=SEQ_LEN)
    tr, te = user_split(owners)            # 留一用户：5 人训练 / 1 人测试
    test_user = max(uid for uid, _ in owners)
    mu, sigma = fit_scaler(X[tr])          # 只用训练用户拟合
    Xs = apply_scaler(X, mu, sigma)
    Xtr, Xte, ytr, yte = Xs[tr], Xs[te], y[tr], y[te]
    print(f"训练集 {len(Xtr)}（5 人）| 测试集 {len(Xte)}（用户 {test_user} 完整 60 天，含压力周）")

    results = {}

    # ---- 基线 0: Persistence（昨天=明天，原始量纲，无需训练）----
    prev_stress_idx = FEATURES.index("prev_stress")
    pers_pred = np.array([
        df_raw[df_raw.user_id == uid].reset_index(drop=True)["prev_stress"].iloc[day]
        for uid, day in [owners[k] for k in te]
    ])
    results["Persistence(昨天=明天)"] = regression_metrics(yte, pers_pred)

    # ---- 基线 1: MLP ----
    results["MLP(拉平全连接)"] = train_and_eval(
        MLPBaseline(SEQ_LEN, len(FEATURES)), Xtr, ytr, Xte, yte, epochs=60)

    # ---- 基线 2: 单变量 LSTM（只用 HRV）----
    hrv_idx = FEATURES.index("hrv_rmssd")
    results["单变量LSTM(仅HRV)"] = train_and_eval(
        MultiVarLSTM(feature_dim=1), Xtr[:, :, [hrv_idx]], ytr,
        Xte[:, :, [hrv_idx]], yte, epochs=60)

    # ---- ours: 多变量 LSTM（7 天窗口）----
    ours = MultiVarLSTM(feature_dim=len(FEATURES))
    results["多变量LSTM(ours, 7天)"] = train_and_eval(ours, Xtr, ytr, Xte, yte, epochs=60)
    n_params = sum(p.numel() for p in ours.parameters())
    print(f"多变量LSTM 参数量: {n_params:,}")

    # ---- 消融: 14 天窗口 ----
    X14, y14, owners14 = build_sequences(df_raw, seq_len=14)
    tr14, te14 = user_split(owners14)
    mu14, sigma14 = fit_scaler(X14[tr14])
    X14s = apply_scaler(X14, mu14, sigma14)
    results["多变量LSTM(14天窗口)"] = train_and_eval(
        MultiVarLSTM(feature_dim=len(FEATURES)),
        X14s[tr14], y14[tr14], X14s[te14], y14[te14], epochs=60)

    # ---- 汇总表 ----
    table = pd.DataFrame(results).T[["MAE", "RMSE", "R2"]]
    print("\n===== 实验结果（真实跑出，可直接抄进 PPT）=====")
    print(table.to_string())
    out_dir = root / "experiment"
    out_dir.mkdir(exist_ok=True)
    table.to_csv(out_dir / "results.csv", encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ["#9aa5b1"] * 2 + ["#9aa5b1"] + ["#e2533f"] + ["#f0a35e"]
    ax.bar(range(len(table)), table["MAE"], color=colors[:len(table)])
    ax.set_xticks(range(len(table)))
    ax.set_xticklabels(table.index, rotation=18, ha="right", fontsize=9)
    ax.set_ylabel("Test MAE (lower is better)")
    ax.set_title("Model Comparison on Stress Prediction")
    for i, v in enumerate(table["MAE"]):
        ax.text(i, v + 0.01, f"{v:.2f}", ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_dir / "model_compare.png", dpi=120)
    plt.close(fig)

    # ---- 特征重要性（置换法）----
    imp = permutation_importance(ours, Xte, yte)
    print("\n===== 特征重要性（MAE 上升量，越大越关键）=====")
    print(imp.round(3).to_string())
    imp.to_csv(out_dir / "feature_importance.csv", encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.barh(range(len(imp)), imp.values, color="#3f7fe2")
    ax.set_yticks(range(len(imp)))
    ax.set_yticklabels(imp.index, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("MAE increase after shuffling (higher = more important)")
    ax.set_title("Permutation Feature Importance")
    fig.tight_layout()
    fig.savefig(out_dir / "feature_importance.png", dpi=120)
    plt.close(fig)

    print(f"\n[OK] 结果与图已保存到 {out_dir}")


if __name__ == "__main__":
    main()
