from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable


def normalize_text(value: object) -> str:
    if value is None:
        return ""

    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"\s+", " ", text).strip().casefold()
    return text


def split_terms(values: Iterable[str] | None) -> list[str]:
    if not values:
        return []

    terms: list[str] = []
    for value in values:
        for part in value.split(","):
            normalized = normalize_text(part)
            if normalized:
                terms.append(normalized)
    return terms


def any_keyword_matches(haystack: Iterable[object], keywords: Iterable[str]) -> bool:
    normalized_haystack = " ".join(normalize_text(value) for value in haystack)
    return any(keyword in normalized_haystack for keyword in keywords)
