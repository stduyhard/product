from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class Settings:
    feishu_app_id: str = os.getenv("FEISHU_APP_ID", "")
    feishu_app_secret: str = os.getenv("FEISHU_APP_SECRET", "")
    feishu_user_access_token: str = os.getenv("FEISHU_USER_ACCESS_TOKEN", "")
    feishu_app_token: str = os.getenv("FEISHU_APP_TOKEN", "")
    feishu_table_products: str = os.getenv("FEISHU_TABLE_PRODUCTS", "")
    feishu_table_jobs: str = os.getenv("FEISHU_TABLE_JOBS", "")
    feishu_use_cn_fields: bool = os.getenv("FEISHU_USE_CN_FIELDS", "1") == "1"
    bot_verify_token: str = os.getenv("BOT_VERIFY_TOKEN", "dev-token")

    collector_mode: str = os.getenv("COLLECTOR_MODE", "auto")
    collector_platforms: str = os.getenv("COLLECTOR_PLATFORMS", "jd,tmall")
    collector_per_platform_limit: int = int(os.getenv("COLLECTOR_PER_PLATFORM_LIMIT", "30"))
    keywords_override: str = os.getenv("KEYWORDS_OVERRIDE", "")
    jd_data_api_url: str = os.getenv("JD_DATA_API_URL", "")
    tmall_data_api_url: str = os.getenv("TMALL_DATA_API_URL", "")
    data_api_key: str = os.getenv("DATA_API_KEY", "")
    use_browser_collector: bool = os.getenv("USE_BROWSER_COLLECTOR", "1") == "1"
    browser_headless: bool = os.getenv("BROWSER_HEADLESS", "1") == "1"
    browser_user_data_dir: str = os.getenv("BROWSER_USER_DATA_DIR", "")
    browser_cdp_endpoint: str = os.getenv("BROWSER_CDP_ENDPOINT", "")
    browser_cdp_port: str = os.getenv("BROWSER_CDP_PORT", "")
    jd_cookie: str = os.getenv("JD_COOKIE", "")
    tmall_cookie: str = os.getenv("TMALL_COOKIE", "")
    crawler_user_agent: str = os.getenv(
        "CRAWLER_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    )
    request_timeout_sec: int = int(os.getenv("REQUEST_TIMEOUT_SEC", "20"))
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "deepseek-chat")
    bot_vector_cache_path: str = os.getenv(
        "BOT_VECTOR_CACHE_PATH",
        "data/knowledge_base.vector.bin",
    )

    @property
    def feishu_enabled(self) -> bool:
        auth_ready = bool(
            self.feishu_user_access_token
            or (self.feishu_app_id and self.feishu_app_secret)
        )
        return bool(
            auth_ready
            and self.feishu_app_token
            and self.feishu_table_products
            and self.feishu_table_jobs
        )

    @property
    def ai_enabled(self) -> bool:
        return bool(self.openai_api_key and self.openai_base_url and self.openai_model)


settings = Settings()
