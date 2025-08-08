#!/usr/bin/env python
"""Evaluate prompts defined in a Promptfoo-style config using LiteLLM.

Config YAML example::

    models:
      - openai/gpt-3.5-turbo
    prompts:
      - file: prompts/qa/basic.yaml
    tests:
      - vars: { animal: cat }
        assert:
          - type: equals
            value: "The capital of France is Paris."

This script loads each prompt, fills variables via Jinja2 templates, queries
each model using LiteLLM, evaluates the results against a series of simple
assertions, and prints a table summarizing the outcomes. Results can optionally
be written to a JSON file for consumption by a small web UI.
"""
import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

import yaml
from jinja2 import Template
from litellm import completion
from rich.console import Console
from rich.table import Table


def load_prompt(file: str) -> str:
    with open(file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("prompt", "")


def _run_assert(output: str, assertion: dict[str, Any]) -> bool:
    """Return True if *output* satisfies *assertion*."""
    a_type = assertion.get("type", "equals")
    value = assertion.get("value", "")
    if a_type == "equals":
        return output.strip() == value.strip()
    if a_type == "contains":
        return value in output
    if a_type == "regex":
        return re.search(value, output) is not None
    if a_type == "startsWith":
        return output.startswith(value)
    if a_type == "endsWith":
        return output.endswith(value)
    return False


def run_evaluation(config_file: str) -> list[dict[str, Any]]:
    """Evaluate *config_file* and return a list of result dictionaries."""
    with open(config_file, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    models: list[str] = cfg.get("models", [])
    prompts: list[dict[str, Any]] = cfg.get("prompts", [])
    tests: list[dict[str, Any]] = cfg.get("tests", [])

    results = []
    for prompt_entry in prompts:
        prompt_file = prompt_entry["file"]
        template_text = load_prompt(prompt_file)
        for test in tests:
            vars_ = test.get("vars", {})
            tpl = Template(template_text)
            text = tpl.render(**vars_)
            assertions: Iterable[dict[str, Any]] = test.get("assert", [])
            if not assertions and (expected := test.get("expected")) is not None:
                assertions = [{"type": "equals", "value": expected}]
            for model in models:
                resp = completion(model=model, messages=[{"role": "user", "content": text}])
                output = resp["choices"][0]["message"]["content"].strip()
                assert_results = [
                    {"type": a["type"], "value": a.get("value", ""), "pass": _run_assert(output, a)}
                    for a in assertions
                ]
                passed = all(a["pass"] for a in assert_results) if assert_results else None
                results.append({
                    "model": model,
                    "prompt": prompt_file,
                    "vars": vars_,
                    "output": output,
                    "asserts": assert_results,
                    "pass": passed,
                })
    return results


def _render_table(results: list[dict[str, Any]]) -> None:
    table = Table(title="Promptfoo-style evaluation")
    table.add_column("Model")
    table.add_column("Prompt")
    table.add_column("Vars")
    table.add_column("Output")
    table.add_column("Checks", overflow="fold")
    table.add_column("Pass")

    for r in results:
        checks = ", ".join(
            f"{a['type']}={a['value']}:{'✅' if a['pass'] else '❌'}" for a in r["asserts"]
        )
        table.add_row(
            r["model"],
            Path(r["prompt"]).name,
            ", ".join(f"{k}={v}" for k, v in r["vars"].items()),
            r["output"],
            checks,
            "\u2705" if r["pass"] else ("\u274c" if r["pass"] is False else ""),
        )

    Console().print(table)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Promptfoo-style evaluations with LiteLLM"
    )
    parser.add_argument("config", help="Path to promptfoo-style YAML config file")
    parser.add_argument(
        "--json-out",
        dest="json_out",
        help="Optional path to write results JSON",
    )
    args = parser.parse_args()

    results = run_evaluation(args.config)
    _render_table(results)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
