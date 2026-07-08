from typing import Literal

CategoryName = Literal[
    "priority", "tc_type", "test_type", "platform_type", "other_tags"
]

_DEFAULT_CATEGORIES: dict[CategoryName, list[str]] = {
    "priority": ["@p0", "@p1", "@p2", "@p3", "@p4", "@p5"],
    "tc_type": ["@positive", "@negative"],
    "test_type": ["@smoke", "@regression", "@sanity", "@integration"],
    "platform_type": ["@ui", "@mobile", "@api", "@web", "@desktop"],
    "other_tags": [],
}


def classify_tag(tag: str, custom_map: dict[str, list[str]] | None = None) -> CategoryName:
    tag_lower = tag.lower().strip()
    merged: dict[str, list[str]] = {}
    for cat, tags in _DEFAULT_CATEGORIES.items():
        merged[cat] = list(tags)
    if custom_map:
        for cat, tags in custom_map.items():
            merged.setdefault(cat, []).extend(tags)

    for category, tag_list in merged.items():
        if tag_lower in [t.lower() for t in tag_list]:
            return category  # type: ignore[return-value]

    if tag_lower.startswith("@p") and len(tag_lower) <= 4:
        return "priority"

    return "other_tags"


def classify_tags(tags: list[str], custom_map: dict[str, list[str]] | None = None) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for tag in tags:
        cat = classify_tag(tag, custom_map)
        result.setdefault(cat, []).append(tag)
    return result
