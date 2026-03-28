from app.collector.sources import (
    _adapt_external_item,
    _browser_cdp_endpoint,
    _browser_connection_mode,
    _browser_cookies,
    _build_search_url,
    _locate_existing_search_page,
    _needs_new_page,
    _parse_jd_html,
    _should_close_browser_resources,
)


def test_build_search_url_for_jd():
    url = _build_search_url("jd", "泡脚桶")
    assert "search.jd.com" in url
    assert "keyword=" in url


def test_parse_jd_html_extracts_items():
    html = """
    <ul>
      <li class="gl-item" data-sku="123">
        <div class="p-name">
          <a href="//item.jd.com/123.html">
            <em>美的 泡脚桶 恒温 12L</em>
          </a>
        </div>
        <div class="p-price"><i>299.00</i></div>
        <div class="p-shop"><a>美的旗舰店</a></div>
        <img data-lazy-img="//img10.360buyimg.com/a.jpg" />
      </li>
    </ul>
    """
    rows = _parse_jd_html(html, keyword="泡脚桶", limit=10)
    assert len(rows) == 1
    assert rows[0]["product_id"] == "123"
    assert rows[0]["price_current"] == 299.0
    assert rows[0]["shop_type"] == "flagship"
    assert rows[0]["product_url"].startswith("https://")


def test_parse_jd_html_extracts_new_card_layout():
    html = """
    <div data-sku="100117484513" class="_wrapper_1v6qy_3 plugin_goodsCardWrapper">
      <img class="_img_18s24_1" data-src="//img13.360buyimg.com/demo.jpg" />
      <span class="_text_1g56m_31" title="乱码标题">乱码标题</span>
      <span class="_price_d0rf6_14">
        <i>￥</i>368<span>.</span><span class="_decimal_d0rf6_28">09</span>
      </span>
      <span class="_gray_d0rf6_61">￥399</span>
      <span class="_goods_volume_1xkku_1"><span title="已售20万+">已售20万+</span></span>
      <span class="_name_b6zo3_45"><span>乱码店铺</span></span>
      <a target="_blank"
         href="//chat.jd.com/index.action?pid=100117484513&seller=%25E7%25BE%258E%25E7%259A%2584%25E4%25BA%25AC%25E4%25B8%259C%25E8%2587%25AA%25E8%2590%25A5%25E6%2597%2597%25E8%2588%25B0%25E5%25BA%2597&wname=%25E7%25BE%258E%25E7%259A%2584ZL310%25E8%25B6%25B3%25E6%25B5%25B4%25E7%259B%2586%25E6%258C%2589%25E6%2591%25A9%25E6%259D%2580%25E8%258F%258C%25E5%258A%25A0%25E7%2583%25AD">
      </a>
    </div>
    """
    rows = _parse_jd_html(html, keyword="泡脚桶", limit=10)
    assert len(rows) == 1
    assert rows[0]["product_id"] == "100117484513"
    assert rows[0]["title"] == "美的ZL310足浴盆按摩杀菌加热"
    assert rows[0]["shop_name"] == "美的京东自营旗舰店"
    assert rows[0]["price_current"] == 368.09
    assert rows[0]["price_original"] == 399.0
    assert rows[0]["product_url"] == "https://item.jd.com/100117484513.html"
    assert rows[0]["image_url"] == "https://img13.360buyimg.com/demo.jpg"


def test_adapt_external_item_maps_common_fields():
    source = {
        "id": "sku-123",
        "title": "midea foot bath 12L",
        "brand": "midea",
        "price": 259.9,
        "origin_price": 399.0,
        "image": "https://example.com/i.jpg",
        "url": "https://example.com/p",
        "shop": "midea-flagship",
        "sales": 888,
        "core_features": ["massage", "drain"],
    }

    item = _adapt_external_item(source, "jd")
    assert item["product_id"] == "sku-123"
    assert item["price_current"] == 259.9
    assert item["price_original"] == 399.0
    assert item["sales_or_reviews"] == 888
    assert item["core_features"] == ["massage", "drain"]


def test_browser_cookies_parse_pairs():
    from app.settings import settings

    old = settings.jd_cookie
    settings.jd_cookie = "pt_key=abc; pt_pin=demo"
    try:
        cookies = _browser_cookies("jd")
        assert len(cookies) == 2
        assert cookies[0]["domain"] == ".jd.com"
        assert cookies[0]["name"] == "pt_key"
    finally:
        settings.jd_cookie = old


def test_browser_cdp_endpoint_uses_explicit_endpoint():
    from app.settings import settings

    old_endpoint = settings.browser_cdp_endpoint
    old_port = settings.browser_cdp_port
    settings.browser_cdp_endpoint = "http://127.0.0.1:9333"
    settings.browser_cdp_port = ""
    try:
        assert _browser_cdp_endpoint() == "http://127.0.0.1:9333"
    finally:
        settings.browser_cdp_endpoint = old_endpoint
        settings.browser_cdp_port = old_port


def test_browser_cdp_endpoint_falls_back_to_local_port():
    from app.settings import settings

    old_endpoint = settings.browser_cdp_endpoint
    old_port = settings.browser_cdp_port
    settings.browser_cdp_endpoint = ""
    settings.browser_cdp_port = "9222"
    try:
        assert _browser_cdp_endpoint() == "http://127.0.0.1:9222"
    finally:
        settings.browser_cdp_endpoint = old_endpoint
        settings.browser_cdp_port = old_port


def test_browser_connection_mode_prefers_cdp_over_user_data_dir():
    from app.settings import settings

    old_endpoint = settings.browser_cdp_endpoint
    old_port = settings.browser_cdp_port
    old_user_data_dir = settings.browser_user_data_dir
    settings.browser_cdp_endpoint = ""
    settings.browser_cdp_port = "9222"
    settings.browser_user_data_dir = r"C:\Users\demo\AppData\Local\Google\Chrome\User Data"
    try:
        assert _browser_connection_mode() == "cdp"
    finally:
        settings.browser_cdp_endpoint = old_endpoint
        settings.browser_cdp_port = old_port
        settings.browser_user_data_dir = old_user_data_dir


def test_cdp_mode_does_not_close_existing_browser_resources():
    assert _should_close_browser_resources("cdp") is False
    assert _should_close_browser_resources("persistent") is True
    assert _should_close_browser_resources("ephemeral") is True


def test_locate_existing_search_page_reuses_matching_tab():
    class FakePage:
        def __init__(self, url: str):
            self.url = url

    class FakeContext:
        def __init__(self, pages):
            self.pages = pages

    url = _build_search_url("jd", "???")
    contexts = [FakeContext([FakePage("https://example.com"), FakePage(url)])]

    page = _locate_existing_search_page(contexts, "jd", "???")
    assert page is not None
    assert page.url == url


def test_needs_new_page_is_false_when_existing_search_page_found():
    class FakePage:
        def __init__(self, url: str):
            self.url = url

    url = _build_search_url("jd", "???")
    assert _needs_new_page(FakePage(url), "cdp") is False
    assert _needs_new_page(None, "cdp") is True
    assert _needs_new_page(None, "ephemeral") is True


def test_locate_existing_search_page_matches_keyword_variant_url():
    class FakePage:
        def __init__(self, url: str):
            self.url = url

    class FakeContext:
        def __init__(self, pages):
            self.pages = pages

    variant_url = "https://search.jd.com/Search?keyword=%E6%B3%A1%E8%84%9A%E6%A1%B6&page=3&s=61"
    contexts = [FakeContext([FakePage(variant_url)])]

    page = _locate_existing_search_page(contexts, "jd", "???")
    assert page is not None
    assert page.url == variant_url



def test_jd_page_issue_detects_login_page():
    from app.collector.sources import _jd_page_issue_message

    html = """
    <html>
      <head><title>京东-欢迎登录</title></head>
      <body>
        <div>登录京东</div>
        <div>扫码登录</div>
      </body>
    </html>
    """

    message = _jd_page_issue_message(html)
    assert message is not None
    assert "JD_COOKIE" in message
    assert "登录页" in message


def test_jd_page_issue_detects_verification_page():
    from app.collector.sources import _jd_page_issue_message

    html = """
    <html>
      <head><title>京东验证中心</title></head>
      <body>
        <div>验证码</div>
        <div>安全验证</div>
      </body>
    </html>
    """

    message = _jd_page_issue_message(html)
    assert message is not None
    assert "验证" in message



def test_collect_web_only_prints_clear_message_for_jd_session_issue(capsys, monkeypatch):
    from app.collector import sources

    def fake_fetch(platform: str, keyword: str, limit: int):
        raise sources.CollectorPageStateError("JD_COOKIE ?????????????????????????")

    monkeypatch.setattr(sources, "_fetch_web_items", fake_fetch)

    rows = sources._collect_web_only("jd", "???", 20)
    captured = capsys.readouterr()

    assert rows == []
    assert "JD_COOKIE" in captured.out
    assert "??????" in captured.out
