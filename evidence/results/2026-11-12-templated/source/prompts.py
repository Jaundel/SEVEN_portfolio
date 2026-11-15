# ============================================================
#  File: prompts.py
#  Project: SEVEN (Sustainable Energy via Efficient Neural-routing)
#  Description: Prompt templates for API synthesis and system instructions.
#  Author(s): Team SEVEN
#  Date: 2025-11-16
# ============================================================
"""Centralized prompt templates for SEVEN's energy-aware routing system.

This module contains all prompt engineering logic, making it easy to:
- Update prompts without touching routing code
- A/B test different prompt strategies
- Maintain consistency across the codebase
"""

from __future__ import annotations


def get_api_synthesis_prompt(api_data: str, user_query: str) -> str:
    """Generate prompt for synthesizing API data with user query.

    Used when real-time data (weather, news, crypto) needs to be
    combined with user's question using the local model.

    Args:
        api_data: Formatted string containing API results (e.g., "Weather: 15 deg C, sunny")
        user_query: Original user question (e.g., "What's the weather in Toronto?")

    Returns:
        Formatted prompt string ready to send to the model.

    Example:
        >>> api_data = "Weather: The weather in Paris is clear with 15 deg C."
        >>> query = "What's the weather in Paris?"
        >>> prompt = get_api_synthesis_prompt(api_data, query)
        >>> # Send prompt to model...
    """
    return f"""Based on this real-time data, answer the user's question naturally.

Real-time data:
{api_data}

User question: {user_query}

Provide a clear, concise answer using the freshest data above."""


def get_system_prompt_local() -> str:
    """System prompt optimized for small local models.

    Note: This is a basic version. For production use, prefer build_local_prompt()
    which includes canon knowledge principles and anti-hallucination safeguards.

    Returns:
        System prompt string for local model initialization.
    """
    return (
        "You are SEVEN Local, an AI assistant focused on energy-efficient routing. "
        "You have strong knowledge of science, math, history, famous people, and general topics. "
        "Answer questions confidently and concisely. "
        'Only say "I\'m not sure" if you truly don\'t know something obscure or very specific.'
    )


def get_system_prompt_cloud() -> str:
    """System prompt for cloud models (OpenAI, Groq).

    Cloud models have more freedom and capacity since we're already
    paying for the inference. They're only called when local models
    can't handle the query or explicitly decline.

    Returns:
        System prompt string for cloud model initialization.
    """
    return (
        "You are SEVEN Cloud (Sustainable Energy Via Efficient Neural-routing for SDG 7). "
        "You are a high-capacity model called when local models decline or for complex queries. "
        "Provide thorough, accurate, and well-structured answers. "
        "You have MORE FREEDOM than local models - you may use multiple paragraphs and detailed explanations when appropriate. "
        "If uncertain, express it clearly, but you're expected to handle queries that smaller models couldn't."
    )


def build_local_prompt(
    user_query: str,
    api_data: str | None = None,
    risk_hint: str | None = None,
    allow_richer_context: bool = False,
    escalate_immediately: bool = False,
) -> str:
    """Construct a context-aware prompt for the local SLM.

    Args:
        user_query: The user's raw query text.
        api_data: Optional block of real-time data to ground the answer.
        risk_hint: Optional note about why this topic is risky (e.g., "pop culture").
        allow_richer_context: When True, permit slightly longer answers (up to 3 sentences).
        escalate_immediately: When True, force the model to decline so heuristics can escalate.

    Returns:
        A formatted prompt string ready to send to the local model.
    """
    if escalate_immediately:
        return (
            "This query exceeds the safe local knowledge boundary.\n"
            'Respond exactly with: "I\'m not sure - please use the cloud model."\n\n'
            f"User question: {user_query}"
        )

    # Build instructions based on context
    instructions: list[str] = []

    # Lead with confidence and encouragement
    instructions.append(
        "You know science, math, history, famous people, and general topics well. "
        "Answer clearly and include relevant context to be helpful. "
        "Keep responses concise but complete."
    )

    # Only add extra caution if there's a specific risk
    if risk_hint:
        instructions.append(
            f"Note: {risk_hint} - only decline if you're genuinely unsure."
        )

    # Simple safety rule
    instructions.append(
        'Only say "I\'m not sure" for truly obscure questions (like someone\'s relatives or niche memes). '
        "Don't decline for well-known topics."
    )

    # Format the guidelines
    guidelines = "\n".join(f"{rule}" for rule in instructions)

    # Add API data block if present
    api_block = ""
    if api_data and api_data.strip():
        api_block = f"\nREAL-TIME DATA (use this to answer):\n{api_data.strip()}\n"

    # Build final prompt (identity is in system_prompt, this is just the user message)
    prompt = (
        f"GUIDELINES:\n{guidelines}\n"
        f"{api_block}\n"
        f"USER QUESTION: {user_query}\n\n"
        f"YOUR RESPONSE:"
    )
    return prompt


def get_fallback_note() -> str:
    """Message to append when APIs are unavailable.

    Returns:
        Note explaining that real-time data isn't available.
    """
    return "(Note: Real-time data APIs were unavailable, responding with general knowledge.)"
