from __future__ import annotations

import json


def extract_json_block(raw_text: str) -> dict:
    text = raw_text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        candidates = []
        for part in parts:
            candidate = part.strip()
            if not candidate:
                continue
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            candidates.append(candidate)
        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    opening_positions = [index for index, char in enumerate(text) if char in "{["]
    closing_positions = [index for index, char in enumerate(text) if char in "}]"]

    for start in opening_positions:
        for end in reversed(closing_positions):
            if end <= start:
                continue
            candidate = text[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise ValueError("Unable to extract valid JSON from model response.")
