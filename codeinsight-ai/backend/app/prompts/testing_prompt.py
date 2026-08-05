from app.prompts.base import build_prompt

_SHAPE = """{
  "summary": "<what the tests cover, 1-2 sentences>",
  "unit_tests": "<complete, runnable unit test code as a single string, newlines as \\n>",
  "edge_cases": ["<edge case a test covers>", ...],
  "framework": "<the testing framework/library used, e.g. pytest, jest>"
}"""


def testing_prompt(language: str, code: str) -> str:
    instructions = (
        "You are a senior engineer writing unit tests for this code. "
        "Use the idiomatic, most widely-used testing framework for the "
        "given language (e.g. pytest for Python, Jest for JS/TS, JUnit "
        "for Java). Cover normal cases, edge cases, and error cases."
    )
    return build_prompt(instructions, language, code, _SHAPE)
