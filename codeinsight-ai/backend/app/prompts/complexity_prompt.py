from app.prompts.base import build_prompt

_SHAPE = """{
  "time_complexity": "<big-O, e.g. O(n log n)>",
  "space_complexity": "<big-O, e.g. O(n)>",
  "explanation": "<why these bounds apply, referencing the loops/recursion/data structures involved>",
  "bottlenecks": ["<specific line or pattern that dominates the cost>", ...],
  "optimization_suggestions": ["<concrete idea to reduce time or space cost>", ...]
}"""


def complexity_prompt(language: str, code: str) -> str:
    instructions = (
        "You are an algorithms expert analyzing the time and space "
        "complexity of this code. Be precise about worst-case Big-O "
        "bounds and justify them with reference to the actual code."
    )
    return build_prompt(instructions, language, code, _SHAPE)
