#!/usr/bin/env python3
"""Prepare PGit QA inputs with anonymous Parallel Search MCP results."""

import argparse
import asyncio
import json
import sys

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import Implementation


MCP_URL = "https://search.parallel.ai/mcp"
USER_AGENT = "pgit-parallel-research/1.0"


def documents_from_result(result):
    """Keep source URLs alongside excerpts, suitable for PGit's documents input."""
    text = "\n".join(block.text for block in result.content if block.type == "text")
    if result.isError:
        raise ValueError(text or "Parallel search returned an error")
    data = result.structuredContent
    if data is None:
        data = json.loads(text)
    documents = []
    for source in data.get("results", [])[:5]:
        excerpts = "\n".join(source.get("excerpts", []))
        if not source.get("url") or not excerpts.strip():
            continue
        documents.append(
            f"Document[{len(documents) + 1}]\n"
            f"Title: {source.get('title') or source['url']}\n"
            f"URL: {source['url']}\n{excerpts}"
        )
    if not documents:
        raise ValueError("Search returned no source excerpts; try a more specific query")
    return "\n\n".join(documents)


async def build_request(question, queries, session_id, timeout=60):
    """Search once and return an inference request, without calling an LLM."""
    async with asyncio.timeout(timeout):
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=httpx.Timeout(30, read=timeout),
        ) as client:
            async with streamable_http_client(MCP_URL, http_client=client) as (read, write, _):
                async with ClientSession(
                    read, write,
                    client_info=Implementation(name="pgit-parallel-research", version="1.0"),
                ) as session:
                    await session.initialize()
                    result = await session.call_tool("web_search", {
                        "objective": question,
                        "search_queries": queries,
                        "session_id": session_id,
                    })
    return {"input_variables": {
        "documents": documents_from_result(result),
        "question": question,
    }}


def nonempty(value):
    if not value.strip():
        raise argparse.ArgumentTypeError("must not be empty")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", type=nonempty)
    parser.add_argument("--query", action="append", required=True, type=nonempty,
                        help="Search query (3-6 words); repeat for related queries")
    parser.add_argument("--session-id", required=True, type=nonempty,
                        help="Reuse one identifier (up to 100 characters) for a research task")
    args = parser.parse_args()
    if len(args.session_id) > 100:
        parser.error("--session-id must be at most 100 characters")
    try:
        request = asyncio.run(build_request(args.question, args.query, args.session_id))
    except Exception as error:
        print(f"Search failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(request, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
