"""Exercise the example through the MCP SDK's real HTTP request path."""

import asyncio
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import httpx
import yaml

import context


ROOT = Path(__file__).resolve().parents[2]
SOURCE = {
    "title": "Free-threaded extensions",
    "url": "https://docs.python.org/3.13/howto/free-threading-extensions.html",
    "excerpts": ["Extension modules need to indicate support for running with the GIL disabled."],
}
REAL_CLIENT = httpx.AsyncClient


class SearchTransport:
    def __init__(self, result=None, failure=None):
        self.result = result if result is not None else {
            "content": [], "structuredContent": {"results": [SOURCE]}, "isError": False,
        }
        self.failure = failure
        self.requests = []
        self.search_started = asyncio.Event()
        self.search_cancelled = False
        self.clients = []

    async def handle(self, request):
        self.requests.append(request)
        if request.method != "POST":
            return httpx.Response(405)
        message = json.loads(request.content)
        method = message["method"]
        if "id" not in message:
            return httpx.Response(202)
        if method == "initialize":
            result = {
                "protocolVersion": message["params"]["protocolVersion"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "search-fixture", "version": "1.0"},
            }
        elif method == "tools/list":
            result = {"tools": [{"name": "web_search", "inputSchema": {"type": "object"}}]}
        elif method == "tools/call":
            self.search_started.set()
            if self.failure == "wait":
                try:
                    await asyncio.Event().wait()
                except asyncio.CancelledError:
                    self.search_cancelled = True
                    raise
            if self.failure == "network":
                raise httpx.ConnectError("connection unavailable", request=request)
            result = self.result
        else:
            raise AssertionError(f"Unexpected MCP method: {method}")
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": message["id"], "result": result})

    def client(self, **kwargs):
        client = REAL_CLIENT(transport=httpx.MockTransport(self.handle), **kwargs)
        self.clients.append(client)
        return client


class SearchTests(unittest.IsolatedAsyncioTestCase):
    async def run_search(self, fixture, timeout=2):
        with patch.object(context.httpx, "AsyncClient", fixture.client):
            return await context.build_request(
                "What changed for extension modules?", ["Python free threading extensions"],
                "pgit-example-test-session", timeout=timeout,
            )

    async def test_request_headers_arguments_and_pgit_consumption(self):
        fixture = SearchTransport()
        payload = await self.run_search(fixture)
        for request in fixture.requests:
            self.assertEqual(str(request.url), context.MCP_URL)
            self.assertEqual(request.headers["user-agent"], context.USER_AGENT)
            self.assertNotIn("authorization", request.headers)
        messages = [json.loads(r.content) for r in fixture.requests if r.method == "POST"]
        call = next(m for m in messages if m["method"] == "tools/call")
        self.assertEqual(call["params"]["name"], "web_search")
        self.assertEqual(call["params"]["arguments"], {
            "objective": "What changed for extension modules?",
            "search_queries": ["Python free threading extensions"],
            "session_id": "pgit-example-test-session",
        })
        # Feed the generated JSON through PGit's actual inference request validator.
        spec = importlib.util.spec_from_file_location("pgit_models", ROOT / "server/models.py")
        models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models)
        request = models.InferenceRequest(**json.loads(json.dumps(payload)))
        for filename in ("qa-with-context-openai.yml", "qa-with-references-openai.yml"):
            prompt = yaml.safe_load((ROOT / "prompts/qa" / filename).read_text())
            models.validate_input_variables(prompt, request.input_variables)
            self.assertEqual(set(prompt["input_variables"]), set(request.input_variables))
        self.assertIn("Document[1]", request.input_variables["documents"])
        self.assertIn(SOURCE["url"], request.input_variables["documents"])
        self.assertIn(SOURCE["excerpts"][0], request.input_variables["documents"])
        self.assertIsNone(request.override_settings)
        self.assertFalse(request.stream)
        self.assertTrue(all(c.is_closed for c in fixture.clients))

    async def test_text_json_response_and_five_source_limit(self):
        fixture = SearchTransport({"content": [{"type": "text", "text": json.dumps({
            "results": [SOURCE] * 7,
        })}]})
        payload = await self.run_search(fixture)
        documents = payload["input_variables"]["documents"]
        self.assertIn("Document[5]", documents)
        self.assertNotIn("Document[6]", documents)

    async def test_empty_sources_fail(self):
        for sources in ([], [{"url": SOURCE["url"], "excerpts": []}]):
            fixture = SearchTransport({"content": [], "structuredContent": {"results": sources}})
            with self.assertRaisesRegex(ValueError, "no source excerpts"):
                await self.run_search(fixture)

    async def test_tool_error_is_not_qa_context(self):
        fixture = SearchTransport({"isError": True, "content": [{
            "type": "text", "text": "Anonymous search quota exceeded",
        }]})
        with self.assertRaisesRegex(ValueError, "quota exceeded"):
            await self.run_search(fixture)

    async def test_malformed_response_fails(self):
        fixture = SearchTransport({"content": [{"type": "text", "text": "invalid JSON"}]})
        with self.assertRaises(json.JSONDecodeError):
            await self.run_search(fixture)

    async def test_network_failure_closes_client(self):
        fixture = SearchTransport(failure="network")
        with self.assertRaises(Exception):
            await self.run_search(fixture)
        self.assertTrue(all(c.is_closed for c in fixture.clients))

    async def test_overall_timeout_cancels_request(self):
        fixture = SearchTransport(failure="wait")
        with self.assertRaises(TimeoutError):
            await self.run_search(fixture, timeout=0.1)
        self.assertTrue(fixture.search_started.is_set())
        self.assertTrue(fixture.search_cancelled)
        self.assertTrue(all(c.is_closed for c in fixture.clients))

    async def test_cancellation_propagates(self):
        fixture = SearchTransport(failure="wait")
        task = asyncio.create_task(self.run_search(fixture))
        await asyncio.wait_for(fixture.search_started.wait(), timeout=2)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(fixture.search_cancelled)
        self.assertTrue(all(c.is_closed for c in fixture.clients))


class CommandTests(unittest.TestCase):
    def test_cli_reports_underlying_network_error(self):
        fixture = SearchTransport(failure="network")
        output, error = io.StringIO(), io.StringIO()
        with patch.object(context.httpx, "AsyncClient", fixture.client), \
                patch.object(sys, "argv", ["context.py", "Question?", "--query", "specific search query",
                                           "--session-id", "stable-test-session"]), \
                redirect_stdout(output), redirect_stderr(error):
            self.assertEqual(context.main(), 1)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("connection unavailable", error.getvalue())

    def test_cli_produces_only_request_json(self):
        fixture = SearchTransport()
        output = io.StringIO()
        with patch.object(context.httpx, "AsyncClient", fixture.client), \
                patch.object(sys, "argv", ["context.py", "Question?", "--query", "specific search query",
                                           "--session-id", "stable-test-session"]), \
                redirect_stdout(output):
            self.assertEqual(context.main(), 0)
        self.assertEqual(json.loads(output.getvalue())["input_variables"]["question"], "Question?")

    def test_cli_failure_does_not_emit_request(self):
        fixture = SearchTransport({"isError": True, "content": [{"type": "text", "text": "Search failed"}]})
        output, error = io.StringIO(), io.StringIO()
        with patch.object(context.httpx, "AsyncClient", fixture.client), \
                patch.object(sys, "argv", ["context.py", "Question?", "--query", "specific search query",
                                           "--session-id", "stable-test-session"]), \
                redirect_stdout(output), redirect_stderr(error):
            self.assertEqual(context.main(), 1)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("Search failed", error.getvalue())


if __name__ == "__main__":
    unittest.main()
