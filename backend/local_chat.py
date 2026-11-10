"""
local_chat.py
本地规则对话：不联网、不调用外部大模型，用当前预测/异常结果生成可解释的短回复。

设计取舍：
1. 课程演示要求“本地模型聊天”可用，但没有本地 LLM 运行时；
   这里用规则模板兜底，保证断网也能对话，接口形状与将来接本地 LLM 一致。
2. 回复只做生活方式建议，不做医疗诊断；出现胸痛/晕厥等描述时直接建议就医。
3. 所有数字来自前端传来的 context（预测、异常、HRV），不在这里编造。
"""
from __future__ import annotations


def _v(value, unit: str = "", dec: int = 0) -> str:
    """把可选的数值格式化成“12.3 毫秒”，None 时返回占位符。"""
    if value is None:
        return "—"
    try:
        num = round(float(value), dec)
    except (TypeError, ValueError):
        return "—"
    text = f"{num:g}" if dec == 0 else f"{num:.{dec}f}"
    return f"{text}{unit}"


def _last_user_text(messages) -> str:
    for msg in reversed(messages or []):
        if msg.get("role") == "user" and str(msg.get("content", "")).strip():
            return str(msg["content"]).strip()
    return ""


def generate_reply(messages, context=None) -> str:
    """根据最后一条用户消息 + 当前指标，返回一段 2–3 句的中文回复。"""
    ctx = context or {}
    text = _last_user_text(messages)
    stress = ctx.get("stress")
    fatigue = ctx.get("fatigue")
    hrv = ctx.get("hrv")
    baseline = ctx.get("baseline")
    drop = ctx.get("drop_pct")
    deep = ctx.get("deep")
    alert = bool(ctx.get("alert"))

    if not text:
        return "主人，我在。想聊今天的指标、明天的压力预测，还是今晚的作息？"

    # 安全优先：涉及急性症状不做判断，直接建议就医
    if any(k in text for k in ("胸痛", "胸闷", "胸口", "晕厥", "晕倒", "呼吸困难", "气短", "喘", "心悸")):
        return (
            "主人，这类身体不适不适合只靠模型判断，请尽快去校医院或拨打急救电话。"
            "我可以继续帮你记录最近的心率变异性变化，方便就诊时说明。"
        )

    has_ctx = any(v is not None for v in (stress, fatigue, hrv, baseline, deep))

    if not has_ctx and not any(k in text for k in ("睡", "熬夜", "失眠", "困", "作息", "几点")):
        return (
            "主人，我暂时没拿到今天的指标数据。可以先问我作息、复习或运动安排，"
            "等页面数据加载好，我再结合心率变异性和压力预测细说。"
        )

    if any(k in text for k in ("睡", "熬夜", "失眠", "困", "作息", "几点")):
        if not has_ctx:
            return "主人，今晚尽量 23:10 前上床、睡前 30 分钟不刷手机；把明天的三件事写下来，大脑更容易停下来。"
        if alert or (isinstance(stress, (int, float)) and stress >= 7):
            return (
                f"主人，明天压力预测 {_v(stress, '/10', 1)}，今晚把上床时间前移到 23:10，"
                f"睡前 30 分钟不刷手机。深睡只有 {_v(deep, ' 分钟')}，先把睡眠时长补回来，比任何补剂都有效。"
            )
        return (
            f"主人，昨晚深睡 {_v(deep, ' 分钟')}，今晚尽量 23:10 前上床、卧室降到 18℃ 左右。"
            "睡前把明天的三件事写下来，大脑更容易停下来。"
        )

    if any(k in text for k in ("考试", "复习", "学习", "论文", "答辩", "上课")):
        return (
            f"主人，明天压力预测 {_v(stress, '/10', 1)}，建议把复习拆成 25 分钟一段，"
            "今晚 23:10 前收工；考前做 3 分钟慢呼吸，比再多刷一套题更管用。"
        )

    if any(k in text for k in ("跑", "运动", "健身", "训练", "锻炼")):
        if isinstance(stress, (int, float)) and stress >= 7:
            return (
                "主人，明天不适合高强度训练。换成 20 分钟快走或拉伸，"
                "等压力回落到 5 以下、心率变异性回到基线附近再加量。"
            )
        return "主人，状态还可以，安排 30 分钟中等强度运动就行，别在睡前两小时内练。"

    if any(k in text for k in ("hrv", "心率变异", "心率", "心脏", "心跳")):
        return (
            f"主人，当前心率变异性 {_v(hrv, ' 毫秒', 1)}，个人基线 {_v(baseline, ' 毫秒', 1)}，"
            f"低 {_v(drop, '%')}。这通常和熬夜、压力有关，今晚优先补觉；"
            "如果持续走低或伴随胸闷心悸，去校医院看看。"
        )

    if any(k in text for k in ("压力", "焦虑", "烦", "累", "紧张", "崩")):
        return (
            f"主人，压力 {_v(stress, '/10', 1)} 确实偏高。先做 3 分钟慢呼吸（吸 4 秒、呼 6 秒），"
            "再把明天的事写成 3 条待办，只做第一条。今晚别熬过 23:10。"
        )

    if any(k in text for k in ("咖啡", "吃", "饮食", "晚饭", "奶茶", "喝")):
        return (
            "主人，咖啡因放到 14:00 前，晚餐别太晚、别太油；"
            "今晚的目标是 23:10 上床，把深睡补回来。"
        )

    if not has_ctx:
        return (
            "主人，我暂时没拿到今天的指标数据。可以先问我作息、复习或运动安排，"
            "等页面数据加载好，我再结合心率变异性和压力预测细说。"
        )

    return (
        f"主人，今天心率变异性 {_v(hrv, ' 毫秒', 1)}（基线 {_v(baseline, ' 毫秒', 1)}），"
        f"明天压力预测 {_v(stress, '/10', 1)}、疲劳 {_v(fatigue, '/10', 1)}。"
        "今晚优先补觉，其他安排明天再说。"
    )


if __name__ == "__main__":
    demo_messages = [{"role": "user", "content": "今晚几点睡比较好？"}]
    demo_context = {
        "stress": 8.48, "fatigue": 7.63, "hrv": 23.7, "baseline": 46.4,
        "drop_pct": 49, "deep": 47, "alert": True,
    }
    print(generate_reply(demo_messages, demo_context))
