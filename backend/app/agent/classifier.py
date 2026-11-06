"""意图分类：优先关键词+jieba，LLM 可用时走轻量模型。

弹幕里大量网络用语（「多少米」「yyds」「上车」「踩雷」），直接按关键词匹配会误判，
所以先把黑话归一化成标准说法，再做意图识别。
"""
from typing import Tuple

import jieba

# 网络用语 → 标准表达。顺序有讲究：长的放前面，避免被短词抢先替换
SLANG_MAP = {
    "多少马内": "多少钱",
    "多少米": "多少钱",
    "几米": "多少钱",
    "多钱": "多少钱",
    "能刀吗": "能便宜点吗",
    "能刀不": "能便宜点吗",
    "刀一下": "便宜点",
    "有羊毛吗": "有没有优惠",
    "薅羊毛": "有没有优惠",
    "血亏": "太贵了",
    "白菜价": "便宜",
    "断货没": "还有货吗",
    "还有吗": "还有货吗",
    "还有货吗": "还有货吗",
    "没货了": "断货",
    "能拍吗": "能买吗",
    "拍不了": "不能买",
    "发货吗": "什么时候发货",
    "包邮不": "包邮吗",
    "退退退": "退货",
    "yyds": "很好",
    "绝绝子": "很好",
    "真香": "很好",
    "爱了爱了": "很喜欢",
    "上车": "想买",
    "种草了": "想买",
    "冲了": "想买",
    "拔草": "不买了",
    "踩雷": "差评",
    "翻车": "差评",
    "智商税": "差评",
    "zqsg": "真心",
    "xswl": "好笑",
    "u1s1": "实话",
    "awsl": "喜欢",
    "集美": "姐妹",
    "家人们": "大家",
    "宝子": "朋友",
}


def normalize_slang(text: str) -> str:
    """把弹幕中的网络用语替换成标准表达，便于后续意图识别。"""
    out = text or ""
    for slang, standard in SLANG_MAP.items():
        out = out.replace(slang, standard)
    return out


RULES = [
    ("ask_coupon", ["券", "优惠", "打折", "便宜", "降点", "满减", "羊毛", "活动价", "福利", "怎么买划算"]),
    ("ask_stock", ["库存", "现货", "有货", "还有多少", "能买吗", "断货", "补货", "缺货"]),
    ("logistics", ["发货", "物流", "快递", "几天到", "什么时候发", "送货", "包邮", "运费"]),
    ("aftersale", ["退", "换", "保修", "售后", "质量问题", "换货", "不合适"]),
    ("complaint", ["投诉", "差评", "太差", "垃圾", "骗子", "骗人", "避雷"]),
    ("ask_price", ["价格", "多少钱", "划算", "贵不贵", "贵", "值不值", "价位", "几块"]),
    ("faq_product", ["材质", "成分", "功效", "尺寸", "规格", "怎么用", "用法", "适合",
                     "肤质", "敏感肌", "油皮", "干皮", "色号", "尺码", "想买", "怎么买"]),
    ("faq_policy", ["活动", "规则", "怎么参加", "怎么领", "免邮"]),
    ("spam", ["加vx", "加微信", "加v", "私聊", "代购", "批发", "广告", "兼职", "刷单", "返利"]),
]


def classify_by_rules(text: str) -> Tuple[str, float]:
    text = normalize_slang(text)
    for intent, kws in RULES:
        for kw in kws:
            if kw in text:
                return intent, 0.75
    seg = set(jieba.lcut(text))
    for intent, kws in RULES:
        if seg & set(kws):
            return intent, 0.6
    return "general", 0.4


def classify_by_llm(text: str, llm_client=None, light_model: str = "qwen-turbo") -> Tuple[str, float]:
    if llm_client is None:
        return classify_by_rules(text)
    normalized = normalize_slang(text)
    intent_list = [r[0] for r in RULES] + ["general"]
    prompt = (
        f"对弹幕分类，只能选 {intent_list} 其中一个。"
        "弹幕里可能有网络用语（如 多少米=多少钱、yyds=很好、上车=想买、踩雷=差评），"
        "请理解其真实含义后再分类。只输出 JSON 字符串：{\"intent\":\"xxx\",\"confidence\":0.xx}。\n"
        f"弹幕：{normalized}"
    )
    try:
        resp = llm_client.chat(light_model, [{"role": "user", "content": prompt}], temperature=0.0)
        if resp.get("fallback") or not resp.get("content"):
            return classify_by_rules(text)
        import json
        content = resp["content"].strip()
        if content.startswith("```"):
            content = content.strip("`")
        data = json.loads(content)
        return data.get("intent", "general"), float(data.get("confidence", 0.5))
    except Exception:
        return classify_by_rules(text)
