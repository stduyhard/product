from app.collector.sources import (
    _adapt_external_item,
    _browser_cdp_endpoint,
    _browser_connection_mode,
    _browser_cookies,
    _build_search_url,
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
