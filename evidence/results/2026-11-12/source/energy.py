# ============================================================
#  File: energy.py
#  Project: SEVEN (Sustainable Energy via Efficient Neural-routing)
#  Description: Energy profile registry and estimator helpers.
#  Author(s): Team SEVEN
#  Date: 2025-11-18
# ============================================================
"""Reusable energy profiling primitives for SEVEN.

This module provides two independent profilers—one for cloud inference tiers
and one for local hardware tiers. Each profiler is expressed as an immutable
`EnergyProfile` with normalized per-token or per-query coefficients. Router and
CLI layers can import the estimator helpers to translate token counts (or
fallback baselines) into joules, watt-hours, and kilowatt-hours without
duplicating constants or unit conversions anywhere else in the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple, Union

JOULES_PER_WH = 3600.0


@dataclass(frozen=True)
class EnergyProfile:
    """Normalized energy coefficients for a single hardware/model tier."""

    slug: str
    label: str
    per_token_j: Optional[float] = None
    per_token_j_min: Optional[float] = None
    per_token_j_max: Optional[float] = None
    per_query_wh: Optional[float] = None
    per_query_wh_min: Optional[float] = None
    per_query_wh_max: Optional[float] = None
    source: str = ""
    note: str = ""


@dataclass(frozen=True)
class EnergyEstimate:
    """Result produced by the estimator helpers for downstream display."""

    profile_label: str
    tokens: int
    joules: float
    watt_hours: float
    kilowatt_hours: float
    joules_min: Optional[float]
    joules_max: Optional[float]
    watt_hours_min: Optional[float]
    watt_hours_max: Optional[float]
    kilowatt_hours_min: Optional[float]
    kilowatt_hours_max: Optional[float]
    average_power_w: Optional[float]
    source: str
    note: str


class CloudProfile(Enum):
    """Cloud inference anchors derived from published/estimated data."""

    GPT4O_SHORT = "gpt4o_short"
    CLOUD_GENERIC = "cloud_generic"
    GEMINI_TEXT = "gemini_text"
    GPT5_INSTANT = "gpt5_instant"
    GPT5_THINKING = "gpt5_thinking"
    CLAUDE_SONNET_SHORT = "claude_sonnet_short"
    CLAUDE_SONNET_MEDIUM = "claude_sonnet_medium"
    CLAUDE_SONNET_LONG = "claude_sonnet_long"


class LocalProfile(Enum):
    """Local hardware anchors for NPUs, GPUs, and CPU-only baselines."""

    NPU_RYZEN_AI = "npu_ryzen_ai"
    NPU_APPLE_ANE = "npu_apple_ane"
    GPU_LAPTOP_HIGH = "gpu_laptop_high"
    GPU_A100 = "gpu_a100"
    GPU_H100 = "gpu_h100"
    CPU_LEGACY = "cpu_legacy"


CLOUD_PROFILES: Dict[CloudProfile, EnergyProfile] = {
    CloudProfile.GPT4O_SHORT: EnergyProfile(
        slug="gpt4o_short",
        label="GPT-4o short prompt (Jegham 2025)",
        per_token_j=3.10,
        per_token_j_min=2.50,
        per_token_j_max=3.50,
        per_query_wh=0.43,
        source="Jegham 2025 infra-aware estimate",
        note="Upper-bound for short GPT-4o prompts including infra overhead.",
    ),
    CloudProfile.CLOUD_GENERIC: EnergyProfile(
        slug="cloud_generic",
        label="Generic GPT-4-class cloud call",
        per_token_j=2.50,
        per_token_j_min=2.0,
        per_token_j_max=3.0,
        per_query_wh=0.34,
        per_query_wh_min=0.30,
        per_query_wh_max=0.40,
        source="OpenAI leadership remarks + independent infra studies",
        note="Use when the exact frontier model is unknown.",
    ),
    CloudProfile.GEMINI_TEXT: EnergyProfile(
        slug="gemini_text",
        label="Gemini Apps text (official median)",
        per_token_j=1.73,
        per_query_wh=0.24,
        source="Google TPUv5 sustainability report",
        note="Median text-only prompt including infra overhead.",
    ),
    CloudProfile.GPT5_INSTANT: EnergyProfile(
        slug="gpt5_instant",
        label="GPT-5.1 Instant (working estimate)",
        per_token_j=0.75,
        per_token_j_min=0.40,
        per_token_j_max=1.10,
        source="SEVEN pricing-derived assumption",
        note="Estimate derived from Instant-mode pricing vs. GPT-4 tokens.",
    ),
    CloudProfile.GPT5_THINKING: EnergyProfile(
        slug="gpt5_thinking",
        label="GPT-5.1 Thinking (working estimate)",
        per_token_j=2.5,
        per_token_j_min=2.0,
        per_token_j_max=3.0,
        source="SEVEN architecture + pricing assumption",
        note="Use for complex GPT-5.1 calls comparable to GPT-4o load.",
    ),
    CloudProfile.CLAUDE_SONNET_SHORT: EnergyProfile(
        slug="claude_sonnet_short",
        label="Claude 3.7 Sonnet short prompts",
        per_query_wh=0.836,
        per_query_wh_min=0.734,
        per_query_wh_max=0.938,
        source='"How Hungry is AI?" (Jegham 2025)',
        note="Third-party estimate; Anthropic has not published official metrics.",
    ),
    CloudProfile.CLAUDE_SONNET_MEDIUM: EnergyProfile(
        slug="claude_sonnet_medium",
        label="Claude 3.7 Sonnet medium prompts",
        per_query_wh=2.781,
        per_query_wh_min=2.504,
        per_query_wh_max=3.058,
        source='"How Hungry is AI?" (Jegham 2025)',
        note="Third-party estimate for medium-length prompts.",
    ),
    CloudProfile.CLAUDE_SONNET_LONG: EnergyProfile(
        slug="claude_sonnet_long",
        label="Claude 3.7 Sonnet long prompts",
        per_query_wh=5.518,
        per_query_wh_min=4.767,
        per_query_wh_max=6.269,
        source='"How Hungry is AI?" (Jegham 2025)',
        note="Third-party estimate for long/complex prompts.",
    ),
}


LOCAL_PROFILES: Dict[LocalProfile, EnergyProfile] = {
    LocalProfile.NPU_RYZEN_AI: EnergyProfile(
        slug="npu_ryzen_ai",
        label="Ryzen AI / XDNA 2 NPU (1–3B SLM)",
        per_token_j=0.85,
        per_token_j_min=0.40,
        per_token_j_max=1.30,
        source="AMD XDNA 2 datasheets + aggregated NPU vs GPU studies",
        note="Baseline for SEVEN local deployments targeting 1–3B models.",
    ),
    LocalProfile.NPU_APPLE_ANE: EnergyProfile(
        slug="npu_apple_ane",
        label="Apple Neural Engine (A17/M4 era)",
        per_token_j=0.90,
        per_token_j_min=0.45,
        per_token_j_max=1.40,
        source="Academic NPU vs GPU comparisons (35–70% less power)",
        note="Use for Apple Silicon client routing when ANE handles inference.",
    ),
    LocalProfile.GPU_LAPTOP_HIGH: EnergyProfile(
        slug="gpu_laptop_high",
        label="Laptop dGPU (RTX 40/50 class)",
        per_token_j=1.60,
        per_token_j_min=0.60,
        per_token_j_max=4.00,
        source="Inference scaling from A100/H100 vs. mobile GPUs",
        note="Represents high-end laptop GPUs running 7–14B models locally.",
    ),
    LocalProfile.GPU_A100: EnergyProfile(
        slug="gpu_a100",
        label="Datacenter GPU (A100, LLaMA-65B proxy)",
        per_token_j=3.50,
        per_token_j_min=3.0,
        per_token_j_max=4.0,
        source='Samsi et al., "From Words to Watts"',
        note="Legacy GPT-3/4-class deployments on NVIDIA A100.",
    ),
    LocalProfile.GPU_H100: EnergyProfile(
        slug="gpu_h100",
        label="Datacenter GPU (H100 FP8, 70B proxy)",
        per_token_j=0.35,
        per_token_j_min=0.30,
        per_token_j_max=0.40,
        source="LLM-Tracker H100 benchmarks",
        note="≈10× more efficient than 2023 A100 figures.",
    ),
    LocalProfile.CPU_LEGACY: EnergyProfile(
        slug="cpu_legacy",
        label="Legacy CPU-heavy inference",
        per_token_j=45.0,
        per_token_j_min=40.0,
        per_token_j_max=50.0,
        source="Li et al. GPT-3 CPU energy studies",
        note="Worst-case baseline for early GPT-3-era CPU clusters.",
    ),
}

_LOCAL_PROFILE_INDEX = {profile.value: profile for profile in LocalProfile}
_CLOUD_PROFILE_INDEX = {profile.value: profile for profile in CloudProfile}
DEFAULT_LOCAL_PROFILE = LocalProfile.NPU_RYZEN_AI
DEFAULT_CLOUD_PROFILE = CloudProfile.GPT4O_SHORT


def estimate_cloud_energy(
    tokens: Optional[int],
    profile: CloudProfile,
    *,
    latency_s: Optional[float] = None,
    default_tokens: int = 500,
) -> EnergyEstimate:
    """Estimate energy for a cloud inference invocation."""

    return _estimate_energy(tokens, CLOUD_PROFILES[profile], latency_s, default_tokens)


def estimate_local_energy(
    tokens: Optional[int],
    profile: LocalProfile,
    *,
    latency_s: Optional[float] = None,
    default_tokens: int = 500,
) -> EnergyEstimate:
    """Estimate energy for a local hardware invocation."""

    return _estimate_energy(tokens, LOCAL_PROFILES[profile], latency_s, default_tokens)


def _estimate_energy(
    tokens: Optional[int],
    profile: EnergyProfile,
    latency_s: Optional[float],
    default_tokens: int,
) -> EnergyEstimate:
    token_count = _resolve_token_count(tokens, default_tokens)
    joules = _joules(profile, token_count)
    wh = joules / JOULES_PER_WH
    kwh = wh / 1000.0

    joules_min = _joules(profile, token_count, use_min=True)
    joules_max = _joules(profile, token_count, use_max=True)

    wh_min = joules_min / JOULES_PER_WH if joules_min is not None else None
    wh_max = joules_max / JOULES_PER_WH if joules_max is not None else None
    kwh_min = wh_min / 1000.0 if wh_min is not None else None
    kwh_max = wh_max / 1000.0 if wh_max is not None else None

    average_power = (joules / latency_s) if latency_s and latency_s > 0 else None

    return EnergyEstimate(
        profile_label=profile.label,
        tokens=token_count,
        joules=joules,
        watt_hours=wh,
        kilowatt_hours=kwh,
        joules_min=joules_min,
        joules_max=joules_max,
        watt_hours_min=wh_min,
        watt_hours_max=wh_max,
        kilowatt_hours_min=kwh_min,
        kilowatt_hours_max=kwh_max,
        average_power_w=average_power,
        source=profile.source,
        note=profile.note,
    )


def _resolve_token_count(tokens: Optional[int], default_tokens: int) -> int:
    if tokens is None or tokens <= 0:
        return max(1, default_tokens)
    return tokens


def _joules(
    profile: EnergyProfile,
    token_count: int,
    *,
    use_min: bool = False,
    use_max: bool = False,
) -> float:
    if use_min and profile.per_token_j_min is not None:
        return profile.per_token_j_min * token_count
    if use_max and profile.per_token_j_max is not None:
        return profile.per_token_j_max * token_count
    if use_min and profile.per_query_wh_min is not None:
        return profile.per_query_wh_min * JOULES_PER_WH
    if use_max and profile.per_query_wh_max is not None:
        return profile.per_query_wh_max * JOULES_PER_WH

    if profile.per_token_j is not None:
        return profile.per_token_j * token_count
    if profile.per_query_wh is not None:
        return profile.per_query_wh * JOULES_PER_WH

    raise ValueError(f"Profile {profile.slug} lacks usable coefficients.")


def describe_profile(profile: EnergyProfile) -> str:
    """Return a human-readable string for CLI/log output."""

    token_descr = (
        f"{profile.per_token_j} J/token"
        if profile.per_token_j is not None
        else "N/A"
    )
    query_descr = (
        f"{profile.per_query_wh} Wh/query"
        if profile.per_query_wh is not None
        else "N/A"
    )
    return f"{profile.label}: {token_descr}, {query_descr} (source: {profile.source})"


def list_cloud_profiles() -> Dict[str, str]:
    """Return slug -> label for quick UI dropdowns."""

    return {profile.slug: profile.label for profile in CLOUD_PROFILES.values()}


def list_local_profiles() -> Dict[str, str]:
    """Return slug -> label for quick UI dropdowns."""

    return {profile.slug: profile.label for profile in LOCAL_PROFILES.values()}


def select_profiles(
    *,
    local: Union[LocalProfile, str, None] = None,
    cloud: Union[CloudProfile, str, None] = None,
    default_local: LocalProfile = DEFAULT_LOCAL_PROFILE,
    default_cloud: CloudProfile = DEFAULT_CLOUD_PROFILE,
) -> Tuple[LocalProfile, CloudProfile]:
    """Convert string or enum inputs into concrete profile selections."""

    return (
        _coerce_local_profile(local, default_local),
        _coerce_cloud_profile(cloud, default_cloud),
    )


def _coerce_local_profile(
    value: Union[LocalProfile, str, None],
    default: LocalProfile,
) -> LocalProfile:
    if isinstance(value, LocalProfile):
        return value
    if isinstance(value, str):
        slug = value.strip().lower()
        return _LOCAL_PROFILE_INDEX.get(slug, default)
    return default


def _coerce_cloud_profile(
    value: Union[CloudProfile, str, None],
    default: CloudProfile,
) -> CloudProfile:
    if isinstance(value, CloudProfile):
        return value
    if isinstance(value, str):
        slug = value.strip().lower()
        return _CLOUD_PROFILE_INDEX.get(slug, default)
    return default


def _demo() -> None:
    """Print sample estimates for manual verification."""

    local = estimate_local_energy(
        tokens=420,
        profile=LocalProfile.NPU_RYZEN_AI,
        latency_s=1.2,
    )
    cloud = estimate_cloud_energy(
        tokens=420,
        profile=CloudProfile.GPT4O_SHORT,
        latency_s=2.4,
    )

    print("=== SEVEN Energy Demo ===")
    print(f"Local ({local.profile_label}): {local.watt_hours * 1000:.2f} mWh")
    print(f"Cloud ({cloud.profile_label}): {cloud.watt_hours * 1000:.2f} mWh")
    delta = cloud.watt_hours - local.watt_hours
    print(f"Estimated savings: {delta * 1000:.2f} mWh per query")


__all__ = [
    "CloudProfile",
    "LocalProfile",
    "EnergyProfile",
    "EnergyEstimate",
    "estimate_cloud_energy",
    "estimate_local_energy",
    "describe_profile",
    "list_cloud_profiles",
    "list_local_profiles",
    "select_profiles",
]


if __name__ == "__main__":
    _demo()
