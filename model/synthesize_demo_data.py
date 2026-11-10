"""
synthesize_demo_data.py
生成演示用合成时序数据：模拟 6 人 × 60 天的手表数据
不依赖 WESAD，先把 pipeline 跑通；后续用真实数据替换即可。
"""
import numpy as np
import pandas as pd
from pathlib import Path

FEATURES = ["resting_hr", "hrv_rmssd", "deep_sleep_min", "rem_min",
            "steps", "sedentary_min", "prev_stress"]


def gen_one_user(seed: int, days: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    # 基线
    hr0 = rng.normal(72, 4)
    hrv0 = rng.normal(55, 8)
    deep0 = rng.normal(85, 20)
    rem0 = rng.normal(70, 15)
    steps0 = rng.normal(7000, 2000)
    sed0 = rng.normal(480, 90)

    rows = []
    prev_stress = 4.0
    for d in range(days):
        # 模拟期末周：第 30-37 天压力飙升
        stress_wave = 2.5 if 30 <= d <= 37 else 0.0
        # 周日活动多一点
        weekend_boost = 1500 if d % 7 in (5, 6) else 0

        hr = hr0 + stress_wave * 2 + rng.normal(0, 2)
        hrv = hrv0 - stress_wave * 8 + rng.normal(0, 4)
        deep = deep0 - stress_wave * 18 + rng.normal(0, 10)
        rem = rem0 - stress_wave * 8 + rng.normal(0, 8)
        steps = steps0 + weekend_boost - stress_wave * 1500 + rng.normal(0, 800)
        sed = sed0 + stress_wave * 120 + rng.normal(0, 40)

        # 真实压力分：跟 HRV↓、深睡↓、静息心率↑ 正相关
        stress = np.clip(
            3.5
            - (hrv - hrv0) / 12
            - (deep - deep0) / 40
            + (hr - hr0) / 5
            + stress_wave * 0.6
            + rng.normal(0, 0.6),
            1, 10,
        )
        rows.append([hr, hrv, deep, rem, steps, sed, prev_stress, stress])
        prev_stress = stress

    df = pd.DataFrame(rows, columns=FEATURES + ["next_stress"])
    return df


def main():
    out_dir = Path(__file__).resolve().parent.parent / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    all_dfs = []
    for uid in range(6):
        df = gen_one_user(seed=uid, days=60)
        df["user_id"] = uid
        all_dfs.append(df)
    full = pd.concat(all_dfs, ignore_index=True)
    out = out_dir / "demo_data.csv"
    full.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"[OK] 生成 {len(full)} 行 -> {out}")
    print(full.head())


if __name__ == "__main__":
    main()