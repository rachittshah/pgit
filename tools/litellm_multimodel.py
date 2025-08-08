#!/usr/bin/env python
"""Run a prompt across multiple models using LiteLLM.

This utility loads a prompt from a PGit YAML file and queries a list of
models using the LiteLLM library. Results can optionally be written to a
directory, allowing git-based tracking of model outputs.
"""
import argparse
from pathlib import Path

import yaml
from git import Repo
from litellm import completion


def run(prompt_file: str, models: list[str], save_dir: str | None = None) -> None:
    """Execute *prompt_file* against each model in *models*.

    If *save_dir* is provided, a text file per model is written and added to
    the repository, enabling git-based history of model responses.
    """
    with open(prompt_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    prompt_text = data.get("prompt", "")

    repo = Repo(Path(prompt_file).resolve().parent, search_parent_directories=True)

    for model in models:
        resp = completion(model=model, messages=[{"role": "user", "content": prompt_text}])
        content = resp["choices"][0]["message"]["content"].strip()
        print(f"\n### {model}\n{content}\n")

        if save_dir:
            out_dir = Path(save_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{Path(prompt_file).stem}_{model.replace('/', '_')}.txt"
            out_file.write_text(content, encoding="utf-8")
            repo.git.add(str(out_file))
            repo.index.commit(f"Add {model} result for {Path(prompt_file).name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query multiple models with LiteLLM")
    parser.add_argument("prompt_file", help="Path to a PGit YAML prompt file")
    parser.add_argument("models", nargs="+", help="List of model identifiers")
    parser.add_argument("--save", dest="save_dir", help="Directory to store and commit results")
    args = parser.parse_args()
    run(args.prompt_file, args.models, args.save_dir)


if __name__ == "__main__":
    main()
