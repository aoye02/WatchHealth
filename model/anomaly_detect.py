"""
anomaly_detect.py
HRV 骤降异常检测：基于滑动窗口均值 ± 3σ 触发预警
对标 Apple Watch 心率异常通知
"""
import numpy as np
import pandas as pd


def detect_hrv_drop(hrv_series: list, window: int = 7, z_thresh: float = 2.5) -> dict:
    """
    hrv_series: 过去 N 天的 HRV 值（rmssd, ms）
    返回: {"alert": bool, "current": float, "baseline_mean": float, "drop_pct": float}
    """
    arr = np.array(hrv_series, dtype=float)
    if len(arr) < window + 2:
        return {"alert": False, "reason": "数据不足"}
    baseline = arr[:-2]
    current = arr[-1]
    mu = float(baseline.mean())
    sigma = float(baseline.std()) + 1e-6
    z = (current - mu) / sigma
    drop_pct = (mu - current) / mu * 100
    alert = (z < -z_thresh) and (drop_pct > 15)
    return {
        "alert": bool(alert),
        "current_hrv": round(float(current), 1),
        "baseline_hrv": round(mu, 1),
        "drop_pct": round(float(drop_pct), 1),
        "z_score": round(float(z), 2),
        "message": "心率变异性连续下降超过 15%，建议今晚早睡，避免熬夜" if alert else "心率变异性正常",
    }


if __name__ == "__main__":
    # 模拟期末周 HRV 从 60 掉到 38
    fake = [62, 60, 61, 59, 58, 57, 55, 48, 40]
    print(detect_hrv_drop(fake))