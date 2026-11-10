# 数据目录说明

## 子目录
- `raw/WESAD/`：公开数据集 WESAD（组员 A 下载解压到这里）
  - 下载地址：https://archive.ics.uci.edu/dataset/465/wesad+wearable+stress+affect+and+affect+recognition+dataset
- `raw/self_collect/`：6 位组员戴手表连续 14 天导出的 CSV
  - 字段：date, resting_hr, hrv_rmssd, deep_sleep_min, rem_min, steps, sedentary_min, self_stress(1-10)
- `processed/`：清洗、标准化后的训练数据
  - `demo_data.csv`：合成演示数据（先跑通用，不依赖真实下载）
  - `mu.csv` / `sigma.csv`：标准化均值方差

## 跑通顺序
```bash
# 1. 先用合成数据跑通 pipeline（不用下载任何东西）
python model/synthesize_demo_data.py
python model/train.py

# 2. 真实数据替换
#    - 把 WESAD 解压到 raw/WESAD/
#    - 把组员手表导出 CSV 放到 raw/self_collect/
#    - 改 train.py 里的数据加载部分读真实数据
```