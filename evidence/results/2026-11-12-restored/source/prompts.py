"""Short, calibrated instructions for SEVEN's local and cloud adapters."""
from __future__ import annotations


def get_system_prompt_local() -> str:
    return 'You are a helpful assistant. Answer accurately and concisely.'



def get_system_prompt_cloud() -> str:
    return ('You are SEVEN Cloud, called for tasks beyond the local model. '
            'Give a clear, accurate answer with enough explanation to check it. '
            'State uncertainty. You have no live data access unless the user supplies current sources.')


def get_api_synthesis_prompt(api_data: str, user_query: str) -> str:
    return f'Answer using only the supplied facts. Preserve units, dates and sources.\nFacts:\n{api_data}\nQuestion: {user_query}'


def build_local_prompt(user_query: str, api_data: str | None = None,
        risk_hint: str | None = None, allow_richer_context: bool = False,
        escalate_immediately: bool = False) -> str:
    if escalate_immediately:
        return f'Respond exactly: "I\'m not sure - please use the cloud model."\nQuestion: {user_query}'
    if api_data:
        return get_api_synthesis_prompt(api_data, user_query)
    return user_query.strip()


def get_fallback_note() -> str:
    return 'Current information could not be retrieved.'
