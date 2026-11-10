"""
lstm_model.py
多变量 LSTM 网络定义：输入过去 7 天的 7 维特征，输出次日压力分（回归）
对应课程第 8 周 RNN/LSTM 内容。
"""
import torch
import torch.nn as nn


class MultiVarLSTM(nn.Module):
    """
    输入 shape: (batch, seq_len=7, feature_dim=7)
    输出 shape: (batch,)  次日压力分
    """

    def __init__(self, feature_dim=7, hidden_dim=64, num_layers=2, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=feature_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        out, _ = self.lstm(x)
        last = out[:, -1, :]
        y = self.head(last)
        return y.squeeze(-1)


if __name__ == "__main__":
    model = MultiVarLSTM()
    dummy = torch.randn(4, 7, 7)
    out = model(dummy)
    print(f"输入: {dummy.shape} -> 输出: {out.shape}")
    print(f"参数量: {sum(p.numel() for p in model.parameters()):,}")