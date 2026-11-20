import unittest
from unittest.mock import MagicMock, patch

import httpx

from modules.inaproc.api.config import GatewayConfig
from modules.inaproc.api.gateway import (
    GatewayAuthError,
    GatewayClientError,
    InaprocGatewayClient,
    redact_token,
)

TOKEN = "super-secret-token-123"

def make_config(**overrides):
    values = {
        "base_url": "https://data.inaproc.id",
        "token": TOKEN,
        "timeout": 5,
        "max_retries": 2,
        "enabled": True,
    }
    values.update(overrides)
    return GatewayConfig(**values)

def json_response(payload, status=200, headers=None):
    return httpx.Response(
        status,
        json=payload,
        headers=headers or {},
        request=httpx.Request("GET", "https://data.inaproc.id/api/v1/test"),
    )

class GatewayConfigTest(unittest.TestCase):
    def test_token_kosong_membuat_disabled(self):
        with patch.dict(
            "os.environ",
            {"INAPROC_API_TOKEN": "", "INAPROC_API_ENABLED": "true"},
            clear=False,
        ):
            config = GatewayConfig.from_env()
        self.assertFalse(config.enabled)

    def test_token_tidak_muncul_di_repr(self):
        config = make_config()
        self.assertNotIn(TOKEN, repr(config))

class GatewayClientTest(unittest.TestCase):
    def test_mengirim_bearer_token(self):
        transport = httpx.MockTransport(lambda request: json_response({"data": []}))
        client = InaprocGatewayClient(make_config(), transport=transport)
        client.get("/api/v1/ekatalog/list-produk-penyedia")

    def test_header_authorization_benar(self):
        seen = {}

        def handler(request):
            seen["auth"] = request.headers.get("authorization")
            seen["method"] = request.method
            return json_response({"data": []})

        client = InaprocGatewayClient(
            make_config(), transport=httpx.MockTransport(handler)
        )
        client.get("/api/v1/ekatalog/list-produk-penyedia")
        self.assertEqual(seen["auth"], f"Bearer {TOKEN}")
        self.assertEqual(seen["method"], "GET")

    def test_hanya_get(self):
        client = InaprocGatewayClient(
            make_config(),
            transport=httpx.MockTransport(lambda request: json_response({"data": []})),
        )
        with self.assertRaises(AttributeError):
            client.post("/api/v1/anything")

    def test_token_kosong_tidak_request(self):
        calls = []
        client = InaprocGatewayClient(
            make_config(token="", enabled=False),
            transport=httpx.MockTransport(lambda request: calls.append(request)),
        )
        with self.assertRaises(GatewayAuthError):
            client.get("/api/v1/ekatalog/list-produk-penyedia")
        self.assertEqual(calls, [])

    def test_retry_429_lalu_sukses(self):
        responses = [
            json_response({}, status=429, headers={"retry-after": "0"}),
            json_response({"data": [{"id": 1}]}),
        ]
        slept = []

        def handler(request):
            return responses.pop(0)

        client = InaprocGatewayClient(
            make_config(max_retries=1),
            transport=httpx.MockTransport(handler),
            sleep=slept.append,
        )
        result = client.get("/api/v1/test")
        self.assertEqual(result["data"][0]["id"], 1)
        self.assertEqual(len(slept), 1)

    def test_retry_5xx_lalu_sukses(self):
        responses = [
            json_response({}, status=503),
            json_response({"data": []}),
        ]
        client = InaprocGatewayClient(
            make_config(max_retries=1),
            transport=httpx.MockTransport(lambda request: responses.pop(0)),
            sleep=lambda _: None,
        )
        self.assertEqual(client.get("/api/v1/test")["data"], [])

    def test_tidak_retry_401(self):
        calls = []

        def handler(request):
            calls.append(request)
            return json_response({"error": "unauthorized"}, status=401)

        client = InaprocGatewayClient(
            make_config(max_retries=3),
            transport=httpx.MockTransport(handler),
            sleep=lambda _: None,
        )
        with self.assertRaises(GatewayAuthError):
            client.get("/api/v1/test")
        self.assertEqual(len(calls), 1)

    def test_tidak_retry_400_403_404(self):
        for status in (400, 403, 404):
            calls = []

            def handler(request, status=status):
                calls.append(request)
                return json_response({}, status=status)

            client = InaprocGatewayClient(
                make_config(max_retries=3),
                transport=httpx.MockTransport(handler),
                sleep=lambda _: None,
            )
            with self.assertRaises(GatewayClientError):
                client.get("/api/v1/test")
            self.assertEqual(len(calls), 1)

    def test_token_tidak_bocor_di_error(self):
        client = InaprocGatewayClient(
            make_config(max_retries=0),
            transport=httpx.MockTransport(
                lambda request: json_response({"detail": f"bad token {TOKEN}"}, status=500)
            ),
            sleep=lambda _: None,
        )
        with self.assertRaises(GatewayClientError) as ctx:
            client.get("/api/v1/test")
        self.assertNotIn(TOKEN, str(ctx.exception))

    def test_redact_token(self):
        self.assertEqual(redact_token(f"Bearer {TOKEN}", TOKEN), "Bearer ***")

    def test_paginate_berhenti_saat_has_more_false(self):
        pages = [
            {"data": [{"id": 1}], "meta": {"has_more": True, "cursor": "c2"}},
            {"data": [{"id": 2}], "meta": {"has_more": False}},
        ]
        seen = []

        def handler(request):
            seen.append(dict(request.url.params))
            return json_response(pages.pop(0))

        client = InaprocGatewayClient(
            make_config(), transport=httpx.MockTransport(handler)
        )
        pages = list(client.paginate("/api/v1/ekatalog/list-produk-penyedia", limit=1))
        self.assertEqual([[row["id"] for row in page] for page in pages], [[1], [2]])
        self.assertEqual(seen[0].get("limit"), "1")
        self.assertEqual(seen[1].get("cursor"), "c2")

    def test_paginate_berhenti_saat_cursor_tidak_berubah(self):
        responses = [
            {"data": [{"id": 1}], "meta": {"has_more": True, "cursor": "same"}},
            {"data": [{"id": 2}], "meta": {"has_more": True, "cursor": "same"}},
        ]
        client = InaprocGatewayClient(
            make_config(),
            transport=httpx.MockTransport(lambda request: json_response(responses.pop(0))),
        )
        pages = list(client.paginate("/api/v1/test", limit=1))
        self.assertEqual([[row["id"] for row in page] for page in pages], [[1], [2]])
        self.assertEqual(responses, [])

    def test_response_bukan_json_ditolak(self):
        client = InaprocGatewayClient(
            make_config(),
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    text="<html>not json</html>",
                    request=httpx.Request("GET", "https://data.inaproc.id/api/v1/test"),
                )
            ),
        )
        with self.assertRaises(GatewayClientError):
            client.get("/api/v1/test")

if __name__ == "__main__":
    unittest.main()
