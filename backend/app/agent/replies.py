"""弹幕回复话术库：按意图/场景提供多样化、语义感知的回复。"""
import random
from typing import Optional

# 每个场景对应多条回复模板，运行时随机挑选，避免话术单调。
# {name} 占位符会被替换为对应用户昵称；其余占位符按需填充。

LOGISTICS_REPLIES = [
    "亲亲～我们全场满 199 包邮，下单后 24 小时内发货，支持 7 天无理由退换哦！",
    "{name} 放心拍，满 199 包邮，24 小时内发出，7 天无理由退换～",
    "物流这边统一安排，满 199 包邮、24h 发货、7 天无理由，放心下单！",
    "关于发货：全场满 199 包邮，付款后 24 小时内发出，支持 7 天无理由退换货哒。",
    "包邮门槛满 199，24 小时内发货，退换无忧，{name} 可以安心下单哦～",
]

NO_COUPON_REPLIES = [
    "本场优惠券暂时抢光啦，关注主播不迷路，下一波福利马上就来～",
    "券已经发完咯，{name} 先点点关注，稍后还有专属福利放送！",
    "这一波券刚被抢空，主播正在加急申请，稍等片刻马上安排～",
    "优惠券暂时缺货，先把关注点起来，下轮福利第一时间通知你！",
    "亲，本场券已发完啦，关注主播，下次开播福利不错过哦～",
]

COUPON_ISSUED_REPLIES = [
    "已为 {name} 发放一张【满{threshold}{unit}{value}】优惠券，去小黄车下单即可使用～",
    "券已到账！满{threshold}{unit}{value}，马上下单就能抵扣，冲冲冲！",
    "{name} 专属券已发放：满{threshold}{unit}{value}，有效期内下单立减哦～",
    "搞定！一张满{threshold}{unit}{value}的券已放入你的账户，快去下单吧～",
    "优惠券已送达，满{threshold}{unit}{value}可用，{name} 记得在有效期内使用呀！",
]

STOCK_REPLIES = [
    "这款{product}（{spec}）目前库存 {stock} 件，价格 ¥{price}，手慢无哦～",
    "{name} 问到的 {product} {spec} 还有 {stock} 件，¥{price}，要的抓紧拍！",
    "帮你查了下，{product}（{spec}）库存 {stock}，单价 ¥{price}，库存有限先到先得～",
    "实时库存播报：{product} {spec} 剩 {stock} 件，¥{price}，下单从速！",
    "{product} {spec} 当前库存 {stock} 件、¥{price}，{name} 赶紧锁定名额吧～",
]

NO_SKU_REPLIES = [
    "主推商品的 SKU 主播正在调整中，稍等马上为你上架～",
    "这款商品的规格马上设置好，{name} 先点点关注，等主播喊上架！",
    "SKU 正在配置中，主播马上处理，稍等一下下哦～",
]

HUMAN_REPLIES = [
    "你的问题已经转给人工客服啦，请稍候，马上为你处理～",
    "已为 {name} 转接人工客服，耐心等待一下，马上就来！",
    "这个问题需要人工跟进，已帮你登记，客服很快会联系你～",
    "收到，已转交人工处理，{name} 稍等片刻哦～",
]

GENERAL_FALLBACK_REPLIES = [
    "主播收到啦，欢迎继续提问～",
    "{name} 的问题主播看到了，正在看哦～",
    "好的好的，主播正在关注你的问题～",
    "收到啦，有任何问题随时在弹幕里说哦～",
    "{name} 别急，主播这边已经看到你的弹幕啦～",
]

PRODUCT_FAQ_SUFFIXES = [
    "（以上信息来自商品库，放心参考哦～）",
    "（数据实时同步，{name} 可以安心下单）",
    "（来自商品库真实数据，无套路～）",
    "",
]


def _pick(pool: list[str], name: Optional[str] = None, **kwargs) -> str:
    text = random.choice(pool)
    text = text.replace("{name}", name or "亲")
    for k, v in kwargs.items():
        text = text.replace(f"{{{k}}}", str(v))
    return text


def logistics_reply(name: Optional[str] = None) -> str:
    return _pick(LOGISTICS_REPLIES, name=name)


def no_coupon_reply(name: Optional[str] = None) -> str:
    return _pick(NO_COUPON_REPLIES, name=name)


def coupon_issued_reply(coupon, name: Optional[str] = None) -> str:
    threshold = float(coupon.threshold or 0)
    value = float(coupon.discount or 0)
    if coupon.type == "discount":
        unit = "减"
        value_str = f"¥{value:.0f}"
    elif coupon.type == "percent":
        unit = "享"
        value_str = f"{(value * 10):.1f}折"
    else:
        unit = ""
        value_str = "包邮"
    threshold_str = f"¥{threshold:.0f}" if threshold > 0 else "任意金额"
    return _pick(COUPON_ISSUED_REPLIES, name=name,
                 threshold=threshold_str, unit=unit, value=value_str)


def stock_reply(product_name: str, spec: str, stock: int, price, name: Optional[str] = None) -> str:
    return _pick(STOCK_REPLIES, name=name,
                 product=product_name, spec=spec, stock=stock, price=price)


def no_sku_reply(name: Optional[str] = None) -> str:
    return _pick(NO_SKU_REPLIES, name=name)


def human_reply(name: Optional[str] = None) -> str:
    return _pick(HUMAN_REPLIES, name=name)


def general_fallback(name: Optional[str] = None) -> str:
    return _pick(GENERAL_FALLBACK_REPLIES, name=name)


def product_faq_suffix(name: Optional[str] = None) -> str:
    return _pick(PRODUCT_FAQ_SUFFIXES, name=name)
