from __future__ import annotations

import json
from dataclasses import asdict

import requests

from app.models import JobResult, ProductRecord
from app.settings import settings


class FeishuBitableClient:
    auth_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

    def _tenant_token(self) -> str:
        payload = {
            "app_id": settings.feishu_app_id,
            "app_secret": settings.feishu_app_secret,
        }
        response = requests.post(self.auth_url, json=payload, timeout=20)
        response.raise_for_status()
        body = response.json()
        if body.get("code") != 0:
            raise RuntimeError(f"feishu auth failed: {body}")
        return body["tenant_access_token"]

    def _access_token(self) -> str:
        if settings.feishu_user_access_token:
            return settings.feishu_user_access_token
        return self._tenant_token()

    def sync_products(self, records: list[ProductRecord]) -> None:
        if not settings.feishu_enabled:
            print(f"[dry-run] products sync skipped, sample={len(records)}")
            return

        token = self._access_token()
        url = (
            "https://open.feishu.cn/open-apis/bitable/v1/apps/"
            f"{settings.feishu_app_token}/tables/{settings.feishu_table_products}/records/batch_create"
        )
        payload = {
            "records": [{"fields": _product_to_fields(rec)} for rec in records[:500]],
        }
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()

    def sync_jobs(self, jobs: list[JobResult]) -> None:
        if not settings.feishu_enabled:
            print(f"[dry-run] jobs sync skipped, sample={len(jobs)}")
            return

        token = self._access_token()
        url = (
            "https://open.feishu.cn/open-apis/bitable/v1/apps/"
            f"{settings.feishu_app_token}/tables/{settings.feishu_table_jobs}/records/batch_create"
        )
        payload = {
            "records": [{"fields": _job_to_fields(job)} for job in jobs[:500]],
        }
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()


def _link_field(value: object) -> dict[str, str]:
    text = str(value or "")
    return {"text": text, "link": text}


def _product_to_fields(rec: ProductRecord) -> dict[str, object]:
    payload = asdict(rec)
    payload["capture_time"] = int(rec.capture_time.timestamp() * 1000)
    payload["core_features"] = ",".join(rec.core_features)
    payload["raw"] = json.dumps(rec.raw, ensure_ascii=False)

    if not settings.feishu_use_cn_fields:
        return payload

    return {
        "记录ID": payload["record_id"],
        "平台": payload["platform"],
        "关键词": payload["keyword"],
        "商品ID": payload["product_id"],
        "标题": payload["title"],
        "品牌": payload["brand"],
        "当前价格": payload["price_current"],
        "原价": payload["price_original"],
        "主图": payload["image_url"],
        "商品链接": _link_field(payload["product_url"]),
        "店铺名": payload["shop_name"],
        "店铺类型": payload["shop_type"],
        "销量或评价": payload["sales_or_reviews"],
        "容量L": payload["capacity_l"],
        "加热方式": payload["heating_type"],
        "核心功能": payload["core_features"],
        "评分": payload["rating"],
        "采集时间": payload["capture_time"],
        "质量标记": payload["data_quality_flag"],
        "原始数据": payload["raw"],
    }


def _job_to_fields(job: JobResult) -> dict[str, object]:
    payload = asdict(job)
    payload["run_time"] = int(job.run_time.timestamp() * 1000)

    if not settings.feishu_use_cn_fields:
        return payload

    return {
        "任务ID": payload["job_id"],
        "执行时间": payload["run_time"],
        "平台": payload["platform"],
        "关键词": payload["keyword"],
        "目标数": payload["target_count"],
        "成功数": payload["success_count"],
        "失败数": payload["fail_count"],
        "状态": payload["status"],
        "错误摘要": payload["error_summary"],
    }

