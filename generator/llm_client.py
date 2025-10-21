# generator/llm_client.py
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_from_prompt(prompt: str, kind: str = "general", max_tokens: int = 500, temperature: float = 0.7):
    """
    Generate SEO text using the OpenAI API.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are an SEO expert helping with {kind} generation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,        # ✅ fixed argument name
            temperature=temperature
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"[LLM ERROR] {e}\n\n(This is a demo fallback output.)"
