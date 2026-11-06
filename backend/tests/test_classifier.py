from app.agent.classifier import classify_by_rules, normalize_slang


def test_slang_is_normalized():
    assert "多少钱" in normalize_slang("这个多少米")
    assert "想买" in normalize_slang("我先上车了")


def test_coupon_intent():
    assert classify_by_rules("有没有优惠券可以领")[0] == "ask_coupon"


def test_stock_intent():
    assert classify_by_rules("一号链接还有货吗")[0] == "ask_stock"


def test_logistics_intent():
    assert classify_by_rules("什么时候发货，几天到")[0] == "logistics"


def test_spam_intent():
    assert classify_by_rules("加微信私聊，代购批发")[0] == "spam"


def test_general_fallback():
    assert classify_by_rules("主播今天状态不错")[0] == "general"
