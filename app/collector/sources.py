from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests
from bs4 import BeautifulSoup

from app.settings import settings


@dataclass(slots=True)
class CollectorConfig:
    per_keyword_limit: int = 100


class BaseCollector:
    platform = "unknown"

    def __init__(self, config: CollectorConfig | None = None) -> None:
        self.config = config or CollectorConfig()

    def collect(self, keyword: str) -> list[dict[str, Any]]:
        raise NotImplementedError


class ExternalApiCollector(BaseCollector):
    api_url = ""

    def collect(self, keyword: str) -> list[dict[str, Any]]:
        mode = settings.collector_mode.lower().strip()
        limit = self.config.per_keyword_limit

        if mode == "mock":
            return _mock_items(self.platform, keyword, limit)
        if mode == "web":
            return _collect_web_only(self.platform, keyword, limit)
        if mode == "api":
            return _collect_api_only(self.api_url, self.platform, keyword, limit)
        return _collect_auto(self.api_url, self.platform, keyword, limit)


class JDCollector(ExternalApiCollector):
    platform = "jd"
    api_url = settings.jd_data_api_url


class TmallCollector(ExternalApiCollector):
    platform = "tmall"
    api_url = settings.tmall_data_api_url


def _collect_web_only(platform: str, keyword: str, limit: int) -> list[dict[str, Any]]:
    try:
        return _fetch_web_items(platform, keyword, limit)
    except requests.RequestException as exc:
        print(f"[collector:{platform}] web crawl failed: {exc}")
        return []



def _collect_api_only(
    api_url: str,
    platform: str,
    keyword: str,
    limit: int,
) -> list[dict[str, Any]]:
    if not api_url:
        print(f"[collector:{platform}] api mode enabled but URL not configured")
        return []
    try:
        return _fetch_live_items(api_url, platform, keyword, limit)
    except requests.RequestException as exc:
        print(f"[collector:{platform}] api request failed: {exc}")
        return []



def _collect_auto(api_url: str, platform: str, keyword: str, limit: int) -> list[dict[str, Any]]:
    try:
        web_items = _fetch_web_items(platform, keyword, limit)
        if web_items:
            return web_items
    except requests.RequestException as exc:
        print(f"[collector:{platform}] web crawl failed in auto mode: {exc}")

    if api_url:
        try:
            api_items = _fetch_live_items(api_url, platform, keyword, limit)
            if api_items:
                return api_items
        except requests.RequestException as exc:
            print(f"[collector:{platform}] api failed in auto mode: {exc}")

    return _mock_items(platform, keyword, limit)



def _request_headers() -> dict[str, str]:
    return {
        "User-Agent": settings.crawler_user_agent,
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Upgrade-Insecure-Requests": "1",
    }



def _fetch_web_items(platform: str, keyword: str, limit: int) -> list[dict[str, Any]]:
    html = ""
    if settings.use_browser_collector:
        html = _fetch_browser_html(platform, keyword)
    if not html:
        html = _fetch_requests_html(platform, keyword)

    if platform == "jd":
        return _parse_jd_html(html, keyword, limit)
    if platform == "tmall":
        return _parse_tmall_html(html, keyword, limit)
    return []



def _browser_cookies(platform: str) -> list[dict[str, object]]:
    raw = settings.jd_cookie if platform == "jd" else settings.tmall_cookie
    if not raw:
        return []

    domain = ".jd.com" if platform == "jd" else ".tmall.com"
    cookies: list[dict[str, object]] = []
    for pair in raw.split(";"):
        if "=" not in pair:
            continue
        name, value = pair.split("=", 1)
        name = name.strip()
        value = value.strip()
        if not name:
            continue
        cookies.append(
            {
                "name": name,
                "value": value,
                "domain": domain,
                "path": "/",
                "httpOnly": False,
                "secure": True,
            }
        )
    return cookies


def _browser_cdp_endpoint() -> str:
    endpoint = settings.browser_cdp_endpoint.strip()
    if endpoint:
        return endpoint

    port = settings.browser_cdp_port.strip()
    if port:
        return f"http://127.0.0.1:{port}"
    return ""



def _browser_connection_mode() -> str:
    if _browser_cdp_endpoint():
        return "cdp"
    if settings.browser_user_data_dir.strip():
        return "persistent"
    return "ephemeral"


def _should_close_browser_resources(mode: str) -> bool:
    return mode != "cdp"



def _locate_existing_search_page(
    contexts: list[Any],
    platform: str,
    keyword: str,
) -> Any | None:
    target_url = _build_search_url(platform, keyword)
    for context in contexts:
        for page in context.pages:
            if page.url == target_url:
                return page
            if platform == "jd" and "search.jd.com/Search" in page.url:
                return page
    return None



def _needs_new_page(page: Any | None, mode: str) -> bool:
    return page is None or mode != "cdp"



def _fetch_browser_html(platform: str, keyword: str) -> str:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ""

    url = _build_search_url(platform, keyword)
    try:
        with sync_playwright() as p:
            browser = None
            page = None
            mode = _browser_connection_mode()
            if mode == "cdp":
                browser = p.chromium.connect_over_cdp(_browser_cdp_endpoint())
                context = browser.contexts[0] if browser.contexts else browser.new_context(
                    user_agent=settings.crawler_user_agent,
                    locale="zh-CN",
                )
                page = _locate_existing_search_page(browser.contexts, platform, keyword)
            elif mode == "persistent":
                context = p.chromium.launch_persistent_context(
                    settings.browser_user_data_dir,
                    headless=settings.browser_headless,
                    user_agent=settings.crawler_user_agent,
                    locale="zh-CN",
                )
            else:
                browser = p.chromium.launch(headless=settings.browser_headless)
                context = browser.new_context(
                    user_agent=settings.crawler_user_agent,
                    locale="zh-CN",
                )
            cookies = _browser_cookies(platform)
            if cookies:
                context.add_cookies(cast(Any, cookies))
            if _needs_new_page(page, mode):
                page = context.new_page()
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=settings.request_timeout_sec * 1000,
                )
            if page is None:
                raise RuntimeError("browser page initialization failed")
            page.wait_for_timeout(3000)
            if platform == "jd":
                try:
                    page.wait_for_selector("li.gl-item, #J_goodsList, .gl-warp", timeout=8000)
                except PlaywrightTimeoutError:
                    pass
            html = page.content()
            if _should_close_browser_resources(mode):
                context.close()
                if browser is not None:
                    browser.close()
            return html
    except PlaywrightError as exc:
        print(f"[collector:{platform}] browser crawl failed: {exc}")
        return ""



def _fetch_requests_html(platform: str, keyword: str) -> str:
    url = _build_search_url(platform, keyword)
    response = requests.get(
        url,
        headers=_request_headers(),
        timeout=settings.request_timeout_sec,
    )
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding or "utf-8"
    return response.text



def _build_search_url(platform: str, keyword: str) -> str:
    escaped = quote_plus(keyword)
    if platform == "jd":
        return f"https://search.jd.com/Search?keyword={escaped}"
    if platform == "tmall":
        return f"https://list.tmall.com/search_product.htm?q={escaped}"
    raise ValueError(f"unsupported platform: {platform}")



def _parse_jd_html(html: str, keyword: str, limit: int) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[dict[str, Any]] = []

    for node in soup.select("li.gl-item"):
        if len(items) >= limit:
            break

        product_id = str(node.get("data-sku") or "")
        p_name = node.select_one(".p-name")
        title = " ".join(p_name.stripped_strings) if p_name else ""
        p_price = node.select_one(".p-price i")
        price_text = p_price.get_text(strip=True) if p_price else ""
        price = _extract_price(price_text)

        link_node = node.select_one(".p-name a")
        href = link_node.get("href") if link_node else ""
        product_url = _normalize_url(str(href or ""))

        image_node = node.select_one("img")
        image_url = ""
        if image_node:
            image_url = str(image_node.get("data-lazy-img") or image_node.get("src") or "")
            image_url = _normalize_url(image_url)

        shop_node = node.select_one(".p-shop a")
        shop_name = shop_node.get_text(strip=True) if shop_node else ""

        if title:
            items.append(
                {
                    "product_id": product_id,
                    "title": title,
                    "brand": _guess_brand(title),
                    "price_current": price,
                    "price_original": None,
                    "image_url": image_url,
                    "product_url": product_url,
                    "shop_name": shop_name,
                    "shop_type": _shop_type(shop_name),
                    "sales_or_reviews": 0,
                    "heating_type": "unknown",
                    "core_features": [],
                    "rating": None,
                    "keyword": keyword,
                }
            )

    if items:
        return items

    items = _parse_jd_new_card_layout(soup, keyword, limit)
    if items:
        return items

    for match in re.finditer(r"jQuery\d+\((\{.*?\})\)\s*;", html, flags=re.DOTALL):
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        rows = payload.get("291", []) if isinstance(payload, dict) else []
        parsed = _parse_jd_json_rows(rows, keyword, limit)
        if parsed:
            return parsed

    return []


def _parse_jd_new_card_layout(
    soup: BeautifulSoup,
    keyword: str,
    limit: int,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for node in soup.select("[data-sku]"):
        if len(items) >= limit:
            break

        product_id = str(node.get("data-sku") or "")
        if not product_id:
            continue

        chat_link = node.select_one('a[href*="chat.jd.com"]')
        chat_href = str(chat_link.get("href") or "") if chat_link else ""
        query = parse_qs(urlparse(_normalize_url(chat_href)).query)

        title = _decode_jd_query_value(query, "wname")
        if not title:
            title_node = node.select_one('span[class*="_text_"]')
            if title_node:
                title = str(
                    title_node.get("title") or title_node.get_text(strip=True) or ""
                )

        shop_name = _decode_jd_query_value(query, "seller")
        if not shop_name:
            shop_node = node.select_one('span[class*="_name_"] span')
            shop_name = shop_node.get_text(strip=True) if shop_node else ""

        image_node = node.select_one("img[data-src], img[src]")
        image_url = ""
        if image_node:
            image_url = str(image_node.get("data-src") or image_node.get("src") or "")
            image_url = _normalize_url(image_url)

        price_node = node.select_one('span[class*="_price_"]')
        price_current = _extract_price(
            price_node.get_text(" ", strip=True) if price_node else ""
        )

        price_original_node = node.select_one('span[class*="_gray_"]')
        price_original = _extract_price(
            price_original_node.get_text(" ", strip=True) if price_original_node else ""
        )

        sales_node = node.select_one('span[class*="_goods_volume_"] [title]') or node.select_one(
            'span[class*="_goods_volume_"] span'
        )
        sales_value = ""
        if sales_node:
            sales_title = sales_node.get("title")
            sales_value = (
                str(sales_title)
                if sales_title is not None
                else sales_node.get_text(strip=True)
            )
        sales_or_reviews = _extract_numeric_volume(sales_value)

        if title:
            items.append(
                {
                    "product_id": product_id,
                    "title": title,
                    "brand": _guess_brand(title),
                    "price_current": price_current,
                    "price_original": price_original or None,
                    "image_url": image_url,
                    "product_url": f"https://item.jd.com/{product_id}.html",
                    "shop_name": shop_name,
                    "shop_type": _shop_type(shop_name),
                    "sales_or_reviews": sales_or_reviews,
                    "heating_type": "unknown",
                    "core_features": [],
                    "rating": None,
                    "keyword": keyword,
                }
            )
    return items


def _decode_jd_query_value(query: dict[str, list[str]], key: str) -> str:
    values = query.get(key, [])
    if not values:
        return ""
    value = values[0]
    # JD chat links often carry doubly-encoded UTF-8 strings.
    for _ in range(2):
        if "%" not in value:
            break
        value = unquote(value)
    return value.strip()


def _extract_numeric_volume(raw: str | None) -> int:
    text = str(raw or "").replace("+", "")
    matched = re.search(r"(\d+(?:\.\d+)?)", text)
    if not matched:
        return 0
    number = float(matched.group(1))
    if "万" in text:
        number *= 10000
    return int(number)



def _parse_jd_json_rows(rows: object, keyword: str, limit: int) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []

    items: list[dict[str, Any]] = []
    for row in rows:
        if len(items) >= limit:
            break
        if not isinstance(row, dict):
            continue

        sku = str(row.get("sku") or row.get("wareId") or "")
        title = str(row.get("imageTitle") or row.get("wname") or "")
        if not title:
            continue
        image_url = _normalize_url(str(row.get("imageurl") or row.get("imageUrl") or ""))
        fallback_url = f"//item.jd.com/{sku}.html"
        product_url = _normalize_url(
            str(row.get("click_url") or row.get("wareUrl") or fallback_url)
        )
        shop_name = str(row.get("shop_name") or row.get("shopName") or "")
        items.append(
            {
                "product_id": sku,
                "title": title,
                "brand": _guess_brand(title),
                "price_current": _extract_price(str(row.get("jdPrice") or row.get("price") or "0")),
                "price_original": None,
                "image_url": image_url,
                "product_url": product_url,
                "shop_name": shop_name,
                "shop_type": _shop_type(shop_name),
                "sales_or_reviews": 0,
                "heating_type": "unknown",
                "core_features": [],
                "rating": None,
                "keyword": keyword,
            }
        )
    return items



def _parse_tmall_html(html: str, keyword: str, limit: int) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[dict[str, Any]] = []

    nodes: list[Any] = []
    for selector in ["div.product", "div.product-iWrap", "div[data-itemid]"]:
        nodes = soup.select(selector)
        if nodes:
            break

    for node in nodes:
        if len(items) >= limit:
            break

        product_id = str(node.get("data-id") or node.get("data-itemid") or "")
        title_node = node.select_one("img[alt]") or node.select_one("a[title]")
        title = str(title_node.get("alt") or title_node.get("title") or "") if title_node else ""

        price_node = node.select_one(".productPrice em")
        if price_node is None:
            price_node = node.select_one(".price")
        price_text = price_node.get_text(strip=True) if price_node else ""
        price = _extract_price(price_text)

        link_node = node.select_one("a")
        href = link_node.get("href") if link_node else ""
        product_url = _normalize_url(str(href or ""))

        img_node = node.select_one("img")
        image_url = ""
        if img_node:
            image_url = str(img_node.get("src") or img_node.get("data-ks-lazyload") or "")
            image_url = _normalize_url(image_url)

        shop_node = node.select_one(".productShop a")
        shop_name = shop_node.get_text(strip=True) if shop_node else ""

        if title:
            items.append(
                {
                    "product_id": product_id,
                    "title": title,
                    "brand": _guess_brand(title),
                    "price_current": price,
                    "price_original": None,
                    "image_url": image_url,
                    "product_url": product_url,
                    "shop_name": shop_name,
                    "shop_type": _shop_type(shop_name),
                    "sales_or_reviews": 0,
                    "heating_type": "unknown",
                    "core_features": [],
                    "rating": None,
                    "keyword": keyword,
                }
            )

    return items



def _shop_type(shop_name: str) -> str:
    if "旗舰" in shop_name:
        return "flagship"
    return "other"



def _normalize_url(url: str) -> str:
    cleaned = url.strip()
    if not cleaned:
        return ""
    if cleaned.startswith("//"):
        return f"https:{cleaned}"
    return cleaned



def _extract_price(raw: str) -> float:
    normalized = re.sub(r"\s*\.\s*", ".", raw)
    matched = re.search(r"(\d+(?:\.\d+)?)", normalized)
    if not matched:
        return 0.0
    return float(matched.group(1))



def _guess_brand(title: str) -> str:
    aliases = ["美的", "海尔", "奥克斯", "小米", "midea", "haier", "aux", "xiaomi"]
    lower_title = title.lower()
    for brand in aliases:
        if brand.lower() in lower_title:
            return brand
    return "unknown-brand"



def _fetch_live_items(
    api_url: str,
    platform: str,
    keyword: str,
    limit: int,
) -> list[dict[str, Any]]:
    headers: dict[str, str] = {}
    if settings.data_api_key:
        headers["Authorization"] = f"Bearer {settings.data_api_key}"

    query_params: dict[str, str | int] = {
        "platform": platform,
        "keyword": keyword,
        "limit": limit,
    }
    response = requests.get(
        api_url,
        params=query_params,
        headers=headers,
        timeout=settings.request_timeout_sec,
    )
    response.raise_for_status()

    body = response.json()
    raw_items = body.get("items", []) if isinstance(body, dict) else []

    records: list[dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        records.append(_adapt_external_item(item, platform))
    return records



def _adapt_external_item(item: dict[str, Any], platform: str) -> dict[str, Any]:
    sales_or_reviews = item.get("sales_or_reviews") or item.get("sales") or item.get("reviews") or 0
    core_features = item.get("core_features")
    return {
        "product_id": str(item.get("product_id") or item.get("id") or ""),
        "title": str(item.get("title") or ""),
        "brand": str(item.get("brand") or ""),
        "price_current": item.get("price_current") or item.get("price") or 0,
        "price_original": item.get("price_original") or item.get("origin_price"),
        "image_url": str(item.get("image_url") or item.get("image") or ""),
        "product_url": str(item.get("product_url") or item.get("url") or ""),
        "shop_name": str(item.get("shop_name") or item.get("shop") or ""),
        "shop_type": str(item.get("shop_type") or "other"),
        "sales_or_reviews": sales_or_reviews,
        "capacity_l": item.get("capacity_l"),
        "heating_type": str(item.get("heating_type") or "unknown"),
        "core_features": core_features if isinstance(core_features, list) else [],
        "rating": item.get("rating"),
        "source_platform": platform,
    }



def _mock_items(platform_name: str, keyword: str, limit: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    brands = ["midea", "haier", "aux", "xiaomi"]
    features = ["massage", "foldable", "constant-temp", "drain"]
    rng = random.Random(f"{platform_name}-{keyword}")

    for idx in range(limit):
        brand = brands[idx % len(brands)]
        feat = features[idx % len(features)]
        price = round(rng.uniform(129, 499), 2)
        items.append(
            {
                "product_id": f"{platform_name}-{keyword}-{idx}",
                "title": f"{brand} {keyword} {feat} 12L home-use",
                "brand": brand,
                "price_current": price,
                "price_original": round(price + rng.uniform(20, 100), 2),
                "image_url": "https://example.com/image.jpg",
                "product_url": "https://example.com/product",
                "shop_name": f"{brand}-flagship",
                "shop_type": "flagship",
                "sales_or_reviews": rng.randint(100, 3000),
                "heating_type": "constant-temp" if "constant-temp" in feat else "fast-heat",
                "rating": round(rng.uniform(4.5, 5.0), 1),
            }
        )
    return items

