from app.prompts.base import build_prompt

_SHAPE = """{
  "explanation": "<clear, beginner-friendly explanation of what the code does, step by step, using plain language and simple analogies where useful>",
  "key_concepts": ["<concept a beginner should look up>", ...]
}"""


def explain_prompt(language: str, code: str) -> str:
    instructions = (
        "You are a patient programming teacher explaining this code to a "
        "beginner who is new to programming. Avoid jargon where possible, "
        "and when you must use a technical term, briefly define it."
    )
    return build_prompt(instructions, language, code, _SHAPE)
