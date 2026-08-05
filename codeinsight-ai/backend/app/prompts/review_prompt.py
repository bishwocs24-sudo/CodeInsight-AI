from app.prompts.base import build_prompt

_SHAPE = """{
  "scores": {
    "overall": <0-100 number>,
    "readability": <0-100>,
    "performance": <0-100>,
    "maintainability": <0-100>,
    "security": <0-100>,
    "documentation": <0-100>,
    "code_quality": <0-100>
  },
  "summary": "<2-3 sentence overview>",
  "strengths": ["<string>", ...],
  "weaknesses": ["<string>", ...],
  "bugs": [{"description": "<string>", "line": <int or null>, "severity": "low|medium|high|critical"}],
  "code_smells": ["<string>", ...],
  "best_practices": ["<string>", ...],
  "naming_suggestions": ["<string>", ...],
  "performance_suggestions": ["<string>", ...],
  "memory_suggestions": ["<string>", ...],
  "edge_cases": ["<string>", ...]
}"""


def review_prompt(language: str, code: str) -> str:
    instructions = (
        "You are a senior software engineer performing a thorough, "
        "constructive code review. Evaluate correctness, readability, "
        "performance, maintainability, security, and documentation. "
        "Be specific and reference concrete lines or patterns rather "
        "than generic advice."
    )
    return build_prompt(instructions, language, code, _SHAPE)
