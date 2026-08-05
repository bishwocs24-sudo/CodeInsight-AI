"""
Shared scaffolding for every prompt template.

Every prompt asks the model to return ONLY a JSON object matching a
documented shape. This keeps parsing on the backend simple and
deterministic instead of scraping free-form markdown.
"""

JSON_ONLY_INSTRUCTION = (
    "Respond with ONLY a single valid JSON object. "
    "Do not include markdown code fences, backticks, or any prose "
    "before or after the JSON. The response must be parseable by "
    "json.loads() with no post-processing."
)


def build_prompt(instructions: str, language: str, code: str, json_shape: str) -> str:
    return f"""{instructions}

Language: {language}

Code to analyze:
```{language}
{code}
```

Return a JSON object with exactly this shape:
{json_shape}

{JSON_ONLY_INSTRUCTION}"""
