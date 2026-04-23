from __future__ import annotations

import json
import urllib.error
import urllib.request

from core.config import Settings
from core.json_utils import extract_json_block
from core.retry import RetryPolicy, run_with_retry


class ProviderError(RuntimeError):
    """Raised when an upstream API request fails."""


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.retry_policy = RetryPolicy(attempts=settings.llm_retries)

    def complete_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> str:
        payload = {
            "model": self.settings.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature if temperature is not None else self.settings.groq_temperature,
            "max_tokens": self.settings.groq_max_tokens,
        }

        body = run_with_retry(self._make_request(payload), self.retry_policy, should_retry=self._should_retry)
        try:
            return body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"Unexpected LLM response structure: {body}") from exc

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: dict,
    ) -> dict:
        json_prompt = (
            f"{user_prompt}\n\n"
            "Return only valid JSON. Do not wrap it in markdown fences. "
            "Do not include commentary before or after the JSON payload."
        )

        raw_response = self.complete_text(system_prompt, json_prompt)
        try:
            return extract_json_block(raw_response)
        except ValueError:
            repair_prompt = (
                "Repair the following model output into valid JSON without changing intent.\n\n"
                f"{raw_response}"
            )
            repaired_response = self.complete_text(
                "You fix malformed JSON responses. Output valid JSON only.",
                repair_prompt,
                temperature=0.0,
            )
            try:
                return extract_json_block(repaired_response)
            except ValueError:
                return fallback

    def _make_request(self, payload: dict):
        def operation() -> dict:
            request = urllib.request.Request(
                url="https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.settings.groq_api_key}",
                    "Accept": "application/json",
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
                if exc.code == 403 and "1010" in error_body:
                    raise ProviderError(
                        "Groq blocked the request with HTTP 403 / Cloudflare 1010. "
                        "This is usually a network or client-signature block rather than a prompt bug. "
                        "Try switching networks, disabling VPN/proxy, verifying the key in Groq Console, "
                        "and retrying from a local machine."
                    ) from exc
                raise ProviderError(f"LLM request failed with HTTP {exc.code}: {error_body}") from exc
            except urllib.error.URLError as exc:
                raise ProviderError(f"LLM request failed: {exc.reason}") from exc

        return operation

    @staticmethod
    def _should_retry(error: Exception) -> bool:
        if not isinstance(error, ProviderError):
            return False
        lowered = str(error).lower()
        return "429" in lowered or "rate limit" in lowered or "timed out" in lowered
