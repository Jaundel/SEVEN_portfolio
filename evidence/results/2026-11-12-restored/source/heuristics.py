# ============================================================
#  File: heuristics.py
#  Project: SEVEN (Sustainable Energy via Efficient Neural-routing)
#  Description: Zero-cost routing heuristics and validators.
#  Author(s): Team SEVEN
#  Date: 2025-11-16
# ============================================================
"""Zero-cost heuristics for intelligent query routing.

This module contains all classification logic that doesn't require
model inference. Makes it easy to tune, test, and iterate on routing
strategies without touching the orchestration code.

All heuristics are based on:
- Keyword matching (real-time data detection)
- Pattern matching (complexity markers)
- Simple metrics (word count, text analysis)
"""

from __future__ import annotations

import re
from typing import Optional

# Support both package and direct script execution
try:
    from .local_model import LocalModelResponse
except ImportError:
    from local_model import LocalModelResponse

# ============================================================
# Tunable Constants
# ============================================================

# Keywords indicating need for real-time data (weather, news, crypto)
API_INTENT_KEYWORDS = {
    "weather": [
        "weather",
        "temperature",
        "forecast",
        "rain",
        "snow",
        "humidity",
        "wind",
    ],
    "crypto": [
        "crypto",
        "bitcoin",
        "btc",
        "ethereum",
        "eth",
        "solana",
        "sol",
        "dogecoin",
        "doge",
        "token",
        "coin",
    ],
    "news": [
        "news",
        "headline",
        "breaking",
        "latest news",
        "today's news",
        "current events",
    ],
}

# Add time-sensitive phrases on top of explicit API keywords
REALTIME_KEYWORDS = sorted(
    {
        "current",
        "latest",
        "today",
        "now",
        "right now",
        "this week",
        "this month",
        "recent",
        "trading",
        "market cap",
        "stock",
    }
    | {keyword for keywords in API_INTENT_KEYWORDS.values() for keyword in keywords}
)

# Phrases indicating query is too complex for small models
COMPLEX_MARKERS = [
    # Long-form content requests
    "write a detailed", "write an essay", "write a report",
    "write a paper", "write an article", "draft a",

    # Analysis requests
    "comprehensive analysis", "detailed analysis", "in-depth analysis",
    "analyze in detail", "deep dive into",

    # Comparison requests
    "compare and contrast", "compare all", "differences between",
    "similarities and differences",

    # Multi-step/tutorial requests
    "step-by-step tutorial", "step by step", "walk me through",
    "guide me through", "explain step by step",

    # Depth markers
    "explain in depth", "explain thoroughly", "explain comprehensively",
    "provide a detailed explanation", "go into detail",

    # Domain-specific complexity (advanced topics)
    "quantum", "derive the", "prove that", "proof of",
    "theorem", "algorithm analysis", "big o notation",
    "differential equation", "integral of",

    # Enumeration/listing (exhaustive)
    "list all", "enumerate all", "every single", "all possible",

    # Creative/subjective tasks
    "write a story", "write a poem", "create a narrative",

    # Research-oriented
    "research on", "literature review", "survey of",
]

# Domain-specific markers that indicate specialized knowledge
# (May be beyond small model capability)
SPECIALIZED_DOMAINS = [
    # Advanced sciences
    "quantum chromodynamics", "string theory", "general relativity",
    "thermodynamics", "organic chemistry",

    # Advanced math
    "topology", "number theory", "abstract algebra",
    "differential geometry", "complex analysis",

    # Specialized technical
    "blockchain consensus", "zero-knowledge proof",
    "compiler optimization", "kernel development",
]

# Phrases indicating model doesn't know the answer
UNCERTAINTY_PHRASES = [
    # Only catch explicit uncertainty - be lenient
    "i don't know",
    "i'm not sure",
    "i not sure",  # Catch grammatical errors
    "i cannot answer",
]

# Maximum words before considering query too complex
MAX_LOCAL_WORD_COUNT = 150


def matches_phrase(text: str, phrase: str) -> bool:
    """Match complete words, including multiword markers and asset symbols."""
    return re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text, re.IGNORECASE) is not None

# ============================================================
# Pre-routing Classification
# ============================================================


def classify_query_type(prompt: str) -> dict[str, str]:
    """Classify query using fast heuristics to determine routing.

    Performs zero-cost (no model inference) classification using
    keyword matching and simple rules. Optimized for energy efficiency.

    Args:
        prompt: User's input query to classify.

    Returns:
        Dictionary with 'route' and 'reason' keys:
            - route: One of 'API_CHECK', 'CLOUD', or 'LOCAL'
            - reason: Human-readable explanation for the decision

    Examples:
        >>> classify_query_type("What's the weather in Paris?")
        {'route': 'API_CHECK', 'reason': 'needs_realtime_data'}

        >>> classify_query_type("What is Python?")
        {'route': 'LOCAL', 'reason': 'default_energy_saving'}

        >>> classify_query_type("Write a comprehensive analysis of AI ethics")
        {'route': 'CLOUD', 'reason': 'too_complex_for_small_model'}

        >>> classify_query_type("Explain quantum chromodynamics")
        {'route': 'CLOUD', 'reason': 'specialized_domain'}
    """
    if not prompt or not prompt.strip():
        return {"route": "LOCAL", "reason": "empty_prompt"}

    lowered = prompt.lower()
    word_count = len(prompt.split())

    # Check 1: Real-time data requirements (highest priority)
    if any(matches_phrase(lowered, keyword) for keyword in REALTIME_KEYWORDS):
        return {"route": "API_CHECK", "reason": "needs_realtime_data"}

    # Check 2: Specialized domain knowledge
    if any(matches_phrase(lowered, domain) for domain in SPECIALIZED_DOMAINS):
        return {"route": "CLOUD", "reason": "specialized_domain"}

    # Check 3: Obviously too complex for small models
    if any(matches_phrase(lowered, marker) for marker in COMPLEX_MARKERS):
        return {"route": "CLOUD", "reason": "too_complex_for_small_model"}

    # Check 4: Length-based complexity
    if word_count > MAX_LOCAL_WORD_COUNT:
        return {"route": "CLOUD", "reason": "prompt_too_long"}

    # Default: Try local (energy-efficient)
    return {"route": "LOCAL", "reason": "default_energy_saving"}


def detect_api_intent(prompt: str) -> Optional[str]:
    """Determine which real-time API (weather/news/crypto) best suits the prompt."""
    if not prompt or not prompt.strip():
        return None

    lowered = prompt.lower()
    for intent, keywords in API_INTENT_KEYWORDS.items():
        if any(matches_phrase(lowered, keyword) for keyword in keywords):
            return intent
    return None


# ============================================================
# Post-routing Validation
# ============================================================


def response_shows_uncertainty(response: LocalModelResponse) -> bool:
    """Detect if model explicitly expressed uncertainty in its response.

    Analyzes response text for explicit uncertainty markers like
    "I don't know" or "I'm not sure". Does not penalize short but
    correct answers.

    Args:
        response: LocalModelResponse object from ask_local().

    Returns:
        True if the model admitted it doesn't know the answer.

    Examples:
        >>> from local_model import LocalModelResponse
        >>> resp = LocalModelResponse(text="I don't know about that.", ...)
        >>> response_shows_uncertainty(resp)
        True

        >>> resp = LocalModelResponse(text="Python is a language.", ...)
        >>> response_shows_uncertainty(resp)
        False

        >>> resp = LocalModelResponse(text="Paris", ...)  # Short but valid
        >>> response_shows_uncertainty(resp)
        False
    """
    text = response.text.lower().strip()

    # Empty response is a sign of failure
    if not text:
        return True

    # Check for explicit uncertainty markers
    return any(phrase in text for phrase in UNCERTAINTY_PHRASES)
