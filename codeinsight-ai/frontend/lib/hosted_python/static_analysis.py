"""Deterministic, non-executing source analysis with evidence and rule identifiers.

These are high-signal heuristics, not a replacement for full SAST or an audit.
"""
import ast
import re
from typing import Any

RULES = {
    'PY001': ('high', 'Use of eval/exec can execute untrusted input'),
    'PY002': ('high', 'Shell execution with shell=True increases injection risk'),
    'PY003': ('medium', 'Use of pickle deserialization can execute arbitrary code'),
    'PY004': ('medium', 'Bare except can conceal unexpected failures'),
    'PY005': ('medium', 'Mutable default argument can leak state across calls'),
    'JS001': ('high', 'Dynamic code execution through eval'),
    'JS002': ('medium', 'Use of innerHTML can introduce DOM injection'),
    'C001': ('high', 'gets is unsafe and can overflow a buffer'),
}


def _finding(rule: str, line: int, excerpt: str) -> dict[str, Any]:
    severity, message = RULES[rule]
    return {'rule_id': rule, 'severity': severity, 'message': message,
            'line': line, 'evidence': excerpt[:180], 'source': 'static',
            'confidence': 'heuristic'}


def analyze_static(language: str, code: str) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    errors: list[str] = []
    lines = code.splitlines()

    def add(rule: str, line: int) -> None:
        findings.append(_finding(rule, line, lines[line - 1].strip()))

    if language == 'python':
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            errors.append(f'Python syntax error at line {exc.lineno}: {exc.msg}')
        else:
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    fn = node.func
                    if isinstance(fn, ast.Name) and fn.id in {'eval', 'exec'}:
                        add('PY001', node.lineno)
                    if isinstance(fn, ast.Attribute) and fn.attr in {'run', 'Popen', 'call', 'check_output', 'check_call'}:
                        if any(k.arg == 'shell' and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords):
                            add('PY002', node.lineno)
                    if isinstance(fn, ast.Attribute) and fn.attr in {'load', 'loads'} and isinstance(fn.value, ast.Name) and fn.value.id == 'pickle':
                        add('PY003', node.lineno)
                elif isinstance(node, ast.ExceptHandler) and node.type is None:
                    add('PY004', node.lineno)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if any(isinstance(d, (ast.List, ast.Dict, ast.Set)) for d in node.args.defaults):
                        add('PY005', node.lineno)
    elif language in {'javascript', 'typescript'}:
        for n, line in enumerate(lines, 1):
            if re.search(r'\beval\s*\(', line):
                add('JS001', n)
            if re.search(r'\.innerHTML\s*=', line):
                add('JS002', n)
    elif language in {'c', 'cpp'}:
        for n, line in enumerate(lines, 1):
            if re.search(r'\bgets\s*\(', line):
                add('C001', n)

    findings.sort(key=lambda f: (f['line'], f['rule_id']))
    return {'language': language, 'lines_of_code': len(lines),
            'findings': findings, 'finding_count': len(findings),
            'errors': errors, 'engine': 'codeguard-static-v1',
            'disclaimer': 'Heuristic analysis; review findings manually. Source code was not executed.'}
