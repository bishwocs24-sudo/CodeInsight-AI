import unittest
from app.services.static_analysis import analyze_static

class StaticAnalysisTests(unittest.TestCase):
    def test_python_risky_calls(self):
        code = 'import subprocess\neval("1")\nsubprocess.run("ls", shell=True)\n'
        result = analyze_static('python', code)
        self.assertEqual([f['rule_id'] for f in result['findings']], ['PY001', 'PY002'])
        self.assertEqual([f['line'] for f in result['findings']], [2, 3])

    def test_syntax_error(self):
        result = analyze_static('python', 'def broken(:')
        self.assertEqual(result['finding_count'], 0)
        self.assertTrue(result['errors'])

    def test_mutable_defaults(self):
        result = analyze_static('python', 'def f(items=[]):\n    return items')
        self.assertEqual(result['findings'][0]['rule_id'], 'PY005')

    def test_js_rules(self):
        result = analyze_static('javascript', 'eval(input);\nel.innerHTML = value;')
        self.assertEqual(result['finding_count'], 2)

    def test_c_rule(self):
        result = analyze_static('c', 'gets(buffer);')
        self.assertEqual(result['findings'][0]['rule_id'], 'C001')

    def test_no_execution(self):
        result = analyze_static('python', '__import__("os").system("echo dangerous")')
        self.assertEqual(result['finding_count'], 0)
        self.assertIn('not executed', result['disclaimer'])

if __name__ == '__main__':
    unittest.main()
