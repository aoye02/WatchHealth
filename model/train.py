"""
train.py
训练最终的多变量 LSTM，输出 best_lstm.pth、mu/sigma 和 loss 曲线。
划分与标准化口径与 run_experiments.py 完全一致（留一用户 + 训练集拟合标准化）。
运行前先 python synthesize_demo_data.py 生成数据。
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

sys.path.append(str(Path(__file__).resolve().parent))
from data_utils import (FEATURES, SEQ_LEN, apply_scaler, build_sequences,  # noqa: E402
                        fit_scaler, load_demo_csv, regression_metrics,
                        user_split)
from lstm_model import MultiVarLSTM  # noqa: E402


class HealthDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, i):
        return self.X[i], self.y[i]


def main():
    torch.manual_seed(42)
    root = Path(__file__).resolve().parent.parent
    df = load_demo_csv()

    X, y, owners = build_sequences(df, seq_len=SEQ_LEN)
    tr, te = user_split(owners)
    mu, sigma = fit_scaler(X[tr])          # 只拟合训练用户，防止测试集泄漏
    Xs = apply_scaler(X, mu, sigma)
    Xtr, Xte, ytr, yte = Xs[tr], Xs[te], y[tr], y[te]
    print(f"训练集 {len(Xtr)}  |  测试集 {len(Xte)}（留一用户）")

    # 保存标准化参数供 predict.py 使用（index 为特征名）
    pd.Series(mu, index=FEATURES).to_csv(root / "data" / "processed" / "mu.csv")
    pd.Series(sigma, index=FEATURES).to_csv(root / "data" / "processed" / "sigma.csv")

    train_loader = DataLoader(HealthDataset(Xtr, ytr), batch_size=16, shuffle=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MultiVarLSTM().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()

    history = []
    best_mae = 1e9
    for epoch in range(60):
        model.train()
        total = 0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
            total += loss.item() * len(xb)
        train_loss = total / len(Xtr)

        model.eval()
        with torch.no_grad():
            preds = model(torch.tensor(Xte).to(device)).cpu().numpy()
        m = regression_metrics(yte, preds)
        history.append((train_loss, m["MAE"]))
        if m["MAE"] < best_mae:
            best_mae = m["MAE"]
            best_metrics = m
            torch.save(model.state_dict(), Path(__file__).parent / "best_lstm.pth")
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1:3d}  train_loss={train_loss:.4f}  test_MAE={m['MAE']:.3f}")

    # 出 loss 曲线
    ex = [h[0] for h in history]
    ey = [h[1] for h in history]
    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(ex, label="Train MSE", color="tab:blue")
    ax1.set_xlabel("Epoch"); ax1.set_ylabel("Train MSE", color="tab:blue")
    ax2 = ax1.twinx()
    ax2.plot(ey, label="Test MAE", color="tab:red")
    ax2.set_ylabel("Test MAE", color="tab:red")
    plt.title("Multi-variate LSTM Training Curve")
    fig.tight_layout()
    out_fig = root / "experiment" / "loss_curve.png"
    plt.savefig(out_fig, dpi=120)
    print(f"[OK] 最佳测试指标: MAE={best_metrics['MAE']}  RMSE={best_metrics['RMSE']}  R2={best_metrics['R2']}")
    print(f"[OK] 权重 -> model/best_lstm.pth | loss 曲线 -> {out_fig}")


if __name__ == "__main__":
    main()
