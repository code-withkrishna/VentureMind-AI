from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from core.config import Settings
from core.models import SourceRecord
from core.retry import RetryPolicy, run_with_retry

_ENDPOINT_NEWS = "https://google.serper.dev/news"
_ENDPOINT_WEB = "https://google.serper.dev/search"


class SerperSearchTool:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.retry_policy = RetryPolicy(attempts=settings.tool_retries)

    def search(self, query: str, mode: str = "web_search") -> list[SourceRecord]:
        endpoint = _ENDPOINT_NEWS if mode == "news_search" else _ENDPOINT_WEB
        payload = {
            "q": query,
            "num": self.settings.search_results,
            "hl": self.settings.search_language,
            "gl": self.settings.search_country,
        }

        body = run_with_retry(
            self._make_request(endpoint, payload),
            self.retry_policy,
            should_retry=self._should_retry,
        )
        return self._parse_results(body, mode)

    def _make_request(self, endpoint: str, payload: dict):
        def operation() -> dict:
            request = urllib.request.Request(
                url=endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Accept": "application/json",
                    "X-API-KEY": self.settings.serper_api_key,
                    "Content-Type": "application/json",
                    "User-Agent": "Agentathon-Intelligence-Copilot/1.0",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=self.settings.request_timeout_seconds,
                ) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                error_body = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"Serper request failed with HTTP {exc.code}: {error_body}") from exc
            except urllib.error.URLError as exc:
                raise RuntimeError(f"Serper request failed: {exc.reason}") from exc

        return operation

    def _parse_results(self, body: dict, mode: str) -> list[SourceRecord]:
        if mode == "news_search":
            raw_results = body.get("news") or body.get("organic") or []
        else:
            raw_results = body.get("organic") or body.get("news") or []

        results: list[SourceRecord] = []
        for item in raw_results[: self.settings.search_results]:
            if not isinstance(item, dict):
                continue
            url = str(item.get("link") or item.get("url") or "").strip()
            if not url:
                continue
            domain = urllib.parse.urlparse(url).netloc.replace("www.", "")
            results.append(
                SourceRecord(
                    title=str(item.get("title") or "Untitled result"),
                    url=url,
                    snippet=str(
                        item.get("snippet")
                        or item.get("description")
                        or item.get("body")
                        or ""
                    ),
                    source=str(item.get("source") or domain),
                    published_at=str(item.get("date") or item.get("publishedAt") or ""),
                )
            )
        return results

    @staticmethod
    def _should_retry(error: Exception) -> bool:
        lowered = str(error).lower()
        return "429" in lowered or "rate limit" in lowered or "timed out" in lowered
