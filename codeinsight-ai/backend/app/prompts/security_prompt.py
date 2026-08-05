from app.prompts.base import build_prompt

_SHAPE = """{
  "scores": {
    "overall": <0-100, this is the security score repeated across all fields>,
    "readability": <0-100>,
    "performance": <0-100>,
    "maintainability": <0-100>,
    "security": <0-100>,
    "documentation": <0-100>,
    "code_quality": <0-100>
  },
  "summary": "<2-3 sentence security posture overview>",
  "security_issues": [
    {
      "title": "<short name, e.g. 'SQL Injection'>",
      "description": "<what's wrong and why it matters>",
      "line": <int or null>,
      "severity": "low|medium|high|critical",
      "cwe": "<CWE id if applicable, else null>",
      "remediation": "<how to fix it>"
    }
  ],
  "best_practices": ["<security best-practice suggestions>", ...]
}"""


def security_prompt(language: str, code: str) -> str:
    instructions = (
        "You are an application security engineer performing a security "
        "review. Look for injection flaws, auth/authorization issues, "
        "unsafe deserialization, secrets in code, unsafe input handling, "
        "insecure crypto, and other OWASP-style vulnerabilities. "
        "Only report issues you can actually justify from the code shown."
    )
    return build_prompt(instructions, language, code, _SHAPE)
