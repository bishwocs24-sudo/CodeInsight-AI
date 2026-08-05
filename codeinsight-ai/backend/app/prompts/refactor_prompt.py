from app.prompts.base import build_prompt

_SHAPE = """{
  "summary": "<what changed and why, 2-3 sentences>",
  "refactored_code": "<the full refactored code as a single string, newlines as \\n>",
  "changes": ["<short bullet describing one change>", ...]
}"""


def refactor_prompt(language: str, code: str) -> str:
    instructions = (
        "You are a senior engineer refactoring this code for readability, "
        "maintainability, and performance, without changing its external "
        "behavior. Preserve functionality exactly."
    )
    return build_prompt(instructions, language, code, _SHAPE)
