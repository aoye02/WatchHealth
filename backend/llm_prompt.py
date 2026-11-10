"""
llm_prompt.py
讯飞星火生成健康简报：把 LSTM 预测 + 异常检测结果变成人话。

接入方式：讯飞星火开放平台的 OpenAI 兼容 HTTP 接口（spark-lite 免费）。
  1. 到 https://console.xf-yun.cn/ 创建应用，领取 APIPassword
  2. 设置环境变量 SPARK_API_PASSWORD（可选 SPARK_MODEL，默认 lite）
  3. 没有 key / 调用失败时自动走本地模板兜底，演示不会崩

generate_brief 返回 {"text": str, "source": "spark" | "template"}，
前端会标注简报来源 —— 老师问起来可以坦然说明。
"""
import os

import requests

SPARK_URL = "https://spark-api-open.xf-yun.com/v1/chat/completions"

SYSTEM_PROMPT = """你是一个温和的大学生健康助手。基于模型给出的预测数据，用 80 字以内生成一段今日健康简报。
要求：
1. 语气像朋友，不要机器人腔
2. 不要做任何医疗诊断
3. 如果发现 HRV 异常下降，要建议"必要时咨询医生"
4. 不要罗列数字，要给出一句可执行的建议
"""


def build_user_prompt(pred: dict, anomaly: dict) -> str:
    return f"""模型预测结果：
- 明日压力分: {pred.get('stress')}/10
- 明日疲劳分: {pred.get('fatigue')}/10
- 系统建议: {pred.get('advice')}
- HRV 异常预警: {anomaly.get('message')}

请生成一段 80 字以内的健康简报。"""


def _template_brief(pred: dict, anomaly: dict) -> str:
    """本地模板兜底：没有 API key 或调用失败时使用，保证演示不崩。"""
    if anomaly.get("alert"):
        return (f"最近你压力有点大（{pred['stress']}/10），HRV 也在持续下降，"
                f"今晚早点睡，别再熬夜了。如果持续不舒服，记得去校医院看看。")
    return f"明天压力预测 {pred['stress']}/10。{pred['advice']}。状态还行，按自己节奏来就好。"


def generate_brief(pred: dict, anomaly: dict) -> dict:
    api_pwd = os.getenv("SPARK_API_PASSWORD")
    if not api_pwd:
        return {"text": _template_brief(pred, anomaly), "source": "template"}

    try:
        resp = requests.post(
            SPARK_URL,
            headers={"Authorization": f"Bearer {api_pwd}",
                     "Content-Type": "application/json"},
            json={
                "model": os.getenv("SPARK_MODEL", "lite"),
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(pred, anomaly)},
                ],
                "temperature": 0.7,
                "max_tokens": 200,
            },
            timeout=15,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        return {"text": text, "source": "spark"}
    except Exception:
        return {"text": _template_brief(pred, anomaly), "source": "template"}


if __name__ == "__main__":
    demo_pred = {"stress": 7.2, "fatigue": 6.5, "advice": "推荐轻运动（瑜伽/散步），今晚 23:30 前入睡"}
    demo_anomaly = {"alert": True, "message": "HRV 连续下降超过 15%，建议今晚早睡，避免熬夜"}
    out = generate_brief(demo_pred, demo_anomaly)
    print(f"[{out['source']}] {out['text']}")
