from __future__ import annotations

import json
import os
import subprocess
import tempfile
from typing import Any


TIMEOUT_SECONDS = 4
MEMORY_LIMIT_BYTES = 256 * 1024 * 1024
DISALLOWED_PATTERNS = {
    "python": ["import os", "import subprocess", "import socket", "open(", "exec(", "eval(", "__import__", "input("],
    "java": ["Runtime.getRuntime", "ProcessBuilder", "java.io.", "java.nio.", "java.net.", "System.exit", "Files."],
}


def _limit_resources():
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT_SECONDS, TIMEOUT_SECONDS))
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
    except Exception:
        return


def _normalize_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_normalize_value(item) for item in value]
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    return value


def _contains_disallowed_pattern(code: str, language: str) -> str | None:
    lowered = code.lower()
    for pattern in DISALLOWED_PATTERNS.get(language, []):
        if pattern.lower() in lowered:
            return pattern
    return None


def _python_driver(question: dict) -> str:
    payload = json.dumps(question["test_cases"])
    function_name = question["function_name"]
    return f"""import importlib.util
import json
import traceback

TEST_CASES = json.loads({payload!r})

def normalize(value):
    if isinstance(value, tuple):
        return [normalize(item) for item in value]
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value

spec = importlib.util.spec_from_file_location("solution", "solution.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

fn = getattr(module, "{function_name}", None)
if fn is None:
    raise AttributeError("Expected function '{function_name}' was not found.")

results = []
for index, case in enumerate(TEST_CASES, start=1):
    try:
        actual = normalize(fn(*case["input"]))
        expected = normalize(case["expected"])
        passed = actual == expected
        results.append({{"case": index, "passed": passed, "expected": expected, "actual": actual}})
    except Exception as exc:
        results.append({{"case": index, "passed": False, "error": str(exc), "traceback": traceback.format_exc()}})

summary = {{
    "passed": all(item.get("passed", False) for item in results),
    "passed_tests": sum(1 for item in results if item.get("passed")),
    "total_tests": len(results),
    "results": results,
}}
print(json.dumps(summary))
"""


def _java_literal(value: Any, value_type: str) -> str:
    if value_type == "int":
        return str(int(value))
    if value_type == "boolean":
        return "true" if value else "false"
    if value_type == "String":
        escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if value_type == "int[]":
        return "new int[]{" + ", ".join(str(int(item)) for item in value) + "}"
    if value_type == "String[]":
        return "new String[]{" + ", ".join(_java_literal(item, "String") for item in value) + "}"
    raise ValueError(f"Unsupported Java type: {value_type}")


def _java_compare_expression(return_type: str, actual_name: str, expected_name: str) -> str:
    if return_type == "int[]":
        return f"java.util.Arrays.equals({actual_name}, {expected_name})"
    if return_type == "String":
        return f"java.util.Objects.equals({actual_name}, {expected_name})"
    return f"{actual_name} == {expected_name}"


def _java_result_expression(return_type: str, value_name: str) -> str:
    if return_type == "int[]":
        return f"java.util.Arrays.toString({value_name})"
    if return_type == "String":
        return value_name
    if return_type == "boolean":
        return f"String.valueOf({value_name})"
    return f"String.valueOf({value_name})"


def _java_runner(question: dict) -> str:
    lines = [
        "import java.util.*;",
        "public class Runner {",
        "    public static void main(String[] args) {",
        "        int passedTests = 0;",
        f"        int totalTests = {len(question['test_cases'])};",
        "        List<String> results = new ArrayList<>();",
    ]

    for index, case in enumerate(question["test_cases"], start=1):
        arg_literals = [
            _java_literal(value, value_type)
            for value, value_type in zip(case["input"], question["param_types"], strict=False)
        ]
        expected_literal = _java_literal(case["expected"], question["return_type"])
        compare_expr = _java_compare_expression(question["return_type"], "actual", "expected")
        actual_display = _java_result_expression(question["return_type"], "actual")
        expected_display = _java_result_expression(question["return_type"], "expected")
        lines.extend([
            "        try {",
            f"            {question['return_type']} actual = Solution.{question['function_name']}({', '.join(arg_literals)});",
            f"            {question['return_type']} expected = {expected_literal};",
            f"            boolean passed = {compare_expr};",
            "            if (passed) { passedTests++; }",
            f"            results.add(\"case {index}:\" + (passed ? \"PASS\" : \"FAIL\") + \"|expected=\" + {expected_display} + \"|actual=\" + {actual_display});",
            "        } catch (Throwable exc) {",
            f"            results.add(\"case {index}:ERROR|\" + exc.getClass().getSimpleName() + \":\" + exc.getMessage());",
            "        }",
        ])

    lines.extend([
        "        boolean passed = passedTests == totalTests;",
        "        StringBuilder out = new StringBuilder();",
        "        out.append('{');",
        "        out.append(\"\\\"passed\\\":\").append(passed);",
        "        out.append(',').append(\"\\\"passed_tests\\\":\").append(passedTests);",
        "        out.append(',').append(\"\\\"total_tests\\\":\").append(totalTests);",
        "        out.append(',').append(\"\\\"results\\\":[\");",
        "        for (int i = 0; i < results.size(); i++) {",
        "            if (i > 0) out.append(',');",
        "            out.append('\"').append(results.get(i).replace(\"\\\\\", \"\\\\\\\\\").replace(\"\\\"\", \"\\\\\\\"\")).append('\"');",
        "        }",
        "        out.append(']');",
        "        out.append('}');",
        "        System.out.println(out);",
        "    }",
        "}",
    ])
    return "\n".join(lines)


def _run_subprocess(command: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        preexec_fn=_limit_resources if os.name != "nt" else None,
    )


def execute_code_submission(question: dict, code: str, language: str) -> dict[str, Any]:
    language = (language or "").strip().lower()
    if language not in {"python", "java"}:
        return {"passed": False, "passed_tests": 0, "total_tests": len(question["test_cases"]), "error_message": "Unsupported language selected."}

    blocked = _contains_disallowed_pattern(code, language)
    if blocked:
        return {
            "passed": False,
            "passed_tests": 0,
            "total_tests": len(question["test_cases"]),
            "error_message": f"Disallowed code pattern detected: {blocked}",
        }

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            if language == "python":
                with open(os.path.join(tmpdir, "solution.py"), "w", encoding="utf-8") as solution_file:
                    solution_file.write(code)
                with open(os.path.join(tmpdir, "runner.py"), "w", encoding="utf-8") as runner_file:
                    runner_file.write(_python_driver(question))
                result = _run_subprocess(["python3", "-I", "runner.py"], tmpdir)
                if result.returncode != 0:
                    return {
                        "passed": False,
                        "passed_tests": 0,
                        "total_tests": len(question["test_cases"]),
                        "error_message": result.stderr.strip() or result.stdout.strip() or "Python execution failed.",
                    }
                return json.loads(result.stdout.strip())

            with open(os.path.join(tmpdir, "Solution.java"), "w", encoding="utf-8") as solution_file:
                solution_file.write(code)
            with open(os.path.join(tmpdir, "Runner.java"), "w", encoding="utf-8") as runner_file:
                runner_file.write(_java_runner(question))

            compile_result = _run_subprocess(["javac", "Solution.java", "Runner.java"], tmpdir)
            if compile_result.returncode != 0:
                return {
                    "passed": False,
                    "passed_tests": 0,
                    "total_tests": len(question["test_cases"]),
                    "error_message": compile_result.stderr.strip() or compile_result.stdout.strip() or "Java compilation failed.",
                }

            run_result = _run_subprocess(["java", "Runner"], tmpdir)
            if run_result.returncode != 0:
                return {
                    "passed": False,
                    "passed_tests": 0,
                    "total_tests": len(question["test_cases"]),
                    "error_message": run_result.stderr.strip() or run_result.stdout.strip() or "Java execution failed.",
                }
            return json.loads(run_result.stdout.strip())
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "passed_tests": 0,
            "total_tests": len(question["test_cases"]),
            "error_message": "Code execution timed out.",
        }
    except Exception as exc:
        return {
            "passed": False,
            "passed_tests": 0,
            "total_tests": len(question["test_cases"]),
            "error_message": str(exc),
        }
