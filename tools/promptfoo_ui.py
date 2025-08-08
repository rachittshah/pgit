#!/usr/bin/env python
"""Serve prompt evaluation results in a simple web UI."""
import argparse
from pathlib import Path

from flask import Flask, render_template_string

from promptfoo_eval import run_evaluation

app = Flask(__name__)
results = []

HTML = """
<!doctype html>
<title>PGit Prompt Evaluator</title>
<h1>PGit Prompt Evaluator</h1>
<table border="1" cellpadding="4" cellspacing="0">
  <tr>
    <th>Model</th><th>Prompt</th><th>Vars</th><th>Output</th><th>Checks</th><th>Pass</th>
  </tr>
  {% for r in results %}
  <tr>
    <td>{{ r.model }}</td>
    <td>{{ r.prompt | basename }}</td>
    <td>{{ r.vars | fmt_vars }}</td>
    <td style="white-space: pre-wrap">{{ r.output }}</td>
    <td>
      <ul>
      {% for a in r.asserts %}
        <li>{{ a.type }}={{ a.value }} -> {{ '✅' if a.pass else '❌' }}</li>
      {% endfor %}
      </ul>
    </td>
    <td>{{ '✅' if r.pass else ('❌' if r.pass is false else '') }}</td>
  </tr>
  {% endfor %}
</table>
"""


@app.template_filter('basename')
def _basename(path):
    return Path(path).name


@app.template_filter('fmt_vars')
def _fmt_vars(d):
    return ", ".join(f"{k}={v}" for k, v in d.items())


@app.route("/")
def index():
    return render_template_string(HTML, results=results)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve evaluation results in a web UI")
    parser.add_argument("config", help="Path to promptfoo-style YAML config file")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    global results
    results = run_evaluation(args.config)
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
