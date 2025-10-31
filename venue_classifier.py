from __future__ import annotations

from enum import Enum
from typing import Literal


class VenueTier(str, Enum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"


def classify_venue(venue_description: str) -> VenueTier:
    """Classify venue into a size tier based on simple keyword heuristics.

    This is intentionally lightweight to unblock imports and runtime.
    """
    text = (venue_description or "").lower()

    if any(k in text for k in ["sân vận động", "stadium", "đường 30m", "arena", "outdoor lớn"]):
        return VenueTier.XL
    if any(k in text for k in ["quảng trường", "large hall", "ngoài trời", "auditorium"]):
        return VenueTier.L
    if any(k in text for k in ["hội trường", "hall", "trung bình", "indoor"]):
        return VenueTier.M
    if any(k in text for k in ["phòng họp", "meeting room", "nhỏ"]):
        return VenueTier.S
    return VenueTier.XS


def _coerce_tier(tier: VenueTier | str) -> VenueTier:
    """Coerce inputs like "XL" or "VenueTier.XL" or already-enum to VenueTier."""
    if isinstance(tier, VenueTier):
        return tier
    text = str(tier).strip()
    if text.startswith("VenueTier."):
        name = text.split(".", 1)[1]
        return VenueTier[name]
    # Prefer by value ("XL") first; fallback to by-name ("XL") which is same here
    try:
        return VenueTier(text)
    except Exception:
        return VenueTier[text]


def get_tier_multiplier(tier: VenueTier | str) -> float:
    """Return a scaling multiplier used to stretch durations/effort by tier."""
    return {
        VenueTier.XS: 0.8,
        VenueTier.S: 0.9,
        VenueTier.M: 1.0,
        VenueTier.L: 1.25,
        VenueTier.XL: 1.5,
    }.get(_coerce_tier(tier), 1.0)


def scale_complexity(base: Literal["low", "medium", "high", "critical"], tier: VenueTier | str) -> str:
    """Scale qualitative complexity by venue tier."""
    order = ["low", "medium", "high", "critical"]
    base_idx = max(0, order.index(base)) if base in order else 1

    bump = {
        VenueTier.XS: 0,
        VenueTier.S: 0,
        VenueTier.M: 0,
        VenueTier.L: 1,
        VenueTier.XL: 1,
    }[_coerce_tier(tier)]

    return order[min(len(order) - 1, base_idx + bump)]


def scale_risk_level(base: Literal["low", "medium", "high", "critical"], tier: VenueTier | str) -> str:
    """Scale qualitative risk by venue tier using the same ladder as complexity."""
    return scale_complexity(base, tier)


