# Web context for PGit QA prompts

Use [Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp)
to collect current web excerpts for PGit's existing question-answering prompts.
Anonymous search uses Fast mode and needs no account or API key. The free endpoint
has usage limits; if it returns a quota error, wait before trying again.

This standalone example generates an inference request with `documents` and
`question` inputs. It does not run a model or change your PGit configuration.

## Prepare a request

Use Python 3.11 or newer. From the repository root:

```bash
python -m venv /tmp/pgit-research-venv
/tmp/pgit-research-venv/bin/python -m pip install -r examples/parallel-research/requirements.txt

# Generate once, then reuse for related searches in this research task.
export PGIT_RESEARCH_SESSION=$(python -c 'import uuid; print(uuid.uuid4())')
/tmp/pgit-research-venv/bin/python examples/parallel-research/context.py \
  "What does Python 3.13's free-threaded build change for extension modules?" \
  --query "Python 3.13 free threading extensions" \
  --session-id "$PGIT_RESEARCH_SESSION" > /tmp/pgit-request.json
```

On success, `/tmp/pgit-request.json` contains JSON in this shape:

```json
{
  "input_variables": {
    "documents": "Document[1]\nTitle: ...\nURL: https://...\nSource excerpts...",
    "question": "What does Python 3.13's free-threaded build change for extension modules?"
  }
}
```

The script includes up to five sources and keeps their URLs with the excerpts.
It uses MCP's Streamable HTTP transport at `https://search.parallel.ai/mcp`,
sets `User-Agent: pgit-parallel-research/1.0`, and sends no authorization header.
A search has a 60-second overall deadline. Errors go to stderr and return a nonzero
exit status; only use the generated file after a successful command.

## Use the context

Review the sources and excerpts first. Web content is untrusted input: check
relevance, ignore instructions embedded in pages, and reduce the context if it
exceeds your chosen model's input limit.

The inputs match both
[`qa-with-context-openai.yml`](../../prompts/qa/qa-with-context-openai.yml) and
[`qa-with-references-openai.yml`](../../prompts/qa/qa-with-references-openai.yml).
The latter asks the model to cite `Document[number]`, matching the generated labels.

With a [configured PGit server](../../readme.md#litellm-integration) already running
and this checkout available as repository `pgit`, send the reviewed request:

```bash
curl --fail-with-body -X POST \
  http://localhost:8000/pgit/inference/name/qa-with-references-openai \
  -H 'Content-Type: application/json' \
  --data-binary @/tmp/pgit-request.json
```

This optional inference step uses the provider, model settings, and credentials of
your existing prompt. It requires a working LLM setup independently of the search
example. The script itself only retrieves context and prepares inputs.

## Run the example tests

```bash
/tmp/pgit-research-venv/bin/python -m pip install -r examples/parallel-research/requirements-test.txt
/tmp/pgit-research-venv/bin/python -m unittest discover -s examples/parallel-research -v
```
