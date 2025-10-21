# generator/llm_client.py
"""
LLM client: uses OpenAI Chat Completions when OPENAI_API_KEY is present.
Keeps a deterministic mock fallback so demos work without a key.

This version is backwards-compatible with openai SDK <1.0 and >=1.0.
"""

import os
import time
from typing import Optional

# Try import openai; keep working if not installed
try:
    import openai
    _OPENAI_AVAILABLE = True
except Exception:
    _OPENAI_AVAILABLE = False

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def _mock_generate(prompt: str, kind: str = "generic") -> str:
    time.sleep(0.25)  # simulate latency
    p = prompt.strip()
    if kind == "title":
        snippet = (p[:60] + "...") if len(p) > 60 else p
        return f"{snippet} — SEO Optimized Title"
    if kind == "meta":
        snippet = (p[:140] + "...") if len(p) > 140 else p
        return f"{snippet} — concise meta description for SEO."
    if kind == "article":
        # a slightly longer mock article to feel realistic
        return (
            f"Intro: {p[:80].strip()}\n\n"
            "This is a demo-generated article used for offline testing. Replace this with a real LLM API call.\n\n"
            "H2: Key points\n- Tip 1\n- Tip 2\n\nConclusion: Short call to action."
        )
    return f"[MOCK OUTPUT] {p[:200]}"


def _build_system_and_user_messages(prompt: str, kind: str) -> list:
    """
    Returns list of messages formatted for chat completions.
    System message sets behavior, user message contains the task.
    """
    sys = "You are an expert SEO content writer. Produce concise, actionable, SEO-friendly content according to the user's instructions."
    user = prompt
    # Small additional instructions for types
    if kind == "title":
        user = f"Write a short, click-enticing SEO title (<= 70 chars). {prompt}"
    elif kind == "meta":
        user = f"Write a concise SEO meta description (<= 160 chars). {prompt}"
    elif kind == "article":
        user = f"Write a helpful SEO-optimized article. Use short paragraphs, H2 headings, and a short conclusion with a call to action. {prompt}"
    return [{"role": "system", "content": sys}, {"role": "user", "content": user}]


def _call_openai_chat(prompt: str, kind: str = "generic", max_tokens: int = 400, temperature: float = 0.7) -> str:
    """
    Call OpenAI ChatCompletion in a backwards-compatible way:
      - tries old SDK style: openai.ChatCompletion.create(...)
      - falls back to new SDK style: OpenAI().chat.completions.create(...)
    """
    if not _OPENAI_AVAILABLE or not OPENAI_API_KEY:
        raise RuntimeError("OpenAI not available or OPENAI_API_KEY missing")

    last_err_old = None

    # try old-style API first (openai.ChatCompletion.create)
    try:
        openai.api_key = OPENAI_API_KEY
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        messages = _build_system_and_user_messages(prompt, kind)
        try:
            resp = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                n=1,
            )
            if hasattr(resp, "choices") and resp.choices:
                choice = resp.choices[0]
                # older returns .message (newer) or .text (older)
                if hasattr(choice, "message"):
                    return choice.message.get("content", "").strip()
                elif hasattr(choice, "text"):
                    return choice.text.strip()
            if isinstance(resp, dict) and "choices" in resp and resp["choices"]:
                item = resp["choices"][0]
                return (item.get("message", {}).get("content") or item.get("text") or "").strip()
        except Exception as inner_old:
            # fall through to new-style call
            last_err_old = inner_old

    except Exception as e_old_top:
        # fall through to try new client
        last_err_old = e_old_top

    # try new OpenAI client (openai>=1.0)
    try:
        # Import the new client class if available
        try:
            from openai import OpenAI as OpenAIClient
        except Exception:
            OpenAIClient = None

        if OpenAIClient is None:
            raise RuntimeError("New OpenAI client not available")

        # Instantiate client (it will read env var or we pass api_key)
        try:
            client = OpenAIClient(api_key=OPENAI_API_KEY)
        except TypeError:
            # some versions accept no arg and rely on env var
            client = OpenAIClient()

        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        messages = _build_system_and_user_messages(prompt, kind)

        # new client API
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            n=1,
        )
        # resp should be a dict-like or object with choices -> message -> content
        if hasattr(resp, "choices") and resp.choices:
            item = resp.choices[0]
            # item may be a mapping
            if hasattr(item, "message"):
                return item.message.get("content", "").strip()
            elif isinstance(item, dict):
                return (item.get("message", {}).get("content") or item.get("text") or "").strip()
        if isinstance(resp, dict) and "choices" in resp and resp["choices"]:
            item = resp["choices"][0]
            return (item.get("message", {}).get("content") or item.get("text") or "").strip()

        # fallback to string conversion
        return str(resp)

    except Exception as e_new:
        # If both styles failed, return helpful error + mock fallback
        return f"[LLM ERROR] old_api_error={repr(last_err_old)[:320]} new_api_error={repr(e_new)[:320]}\n\n" + _mock_generate(prompt, kind)


def generate_from_prompt(prompt: str, kind: str = "generic", max_tokens: int = 400, temperature: float = 0.7) -> str:
    """
    Main helper. Tries OpenAI chat; falls back to deterministic mock.
    """
    # prefer OpenAI chat if available + key present
    if _OPENAI_AVAILABLE and OPENAI_API_KEY:
        try:
            return _call_openai_chat(prompt, kind=kind, max_tokens=max_tokens, temperature=temperature)
        except Exception:
            # if anything goes wrong, fall back to mock
            return _mock_generate(prompt, kind)
    # No OpenAI available or key missing
    return _mock_generate(prompt, kind)


# quick local test when running file directly
if __name__ == "__main__":
    print(generate_from_prompt("Write a short SEO title for a bakery selling sourdough", kind="title"))
    print(generate_from_prompt("Write a short meta description for a bakery selling sourdough", kind="meta"))
    print(generate_from_prompt("Write a 3-paragraph article about small-batch sourdough", kind="article"))
