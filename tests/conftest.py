"""Offline tests cannot accidentally open a Python network socket."""

import socket

import httpx
import pytest


@pytest.fixture(autouse=True)
def no_accidental_network(request, monkeypatch):
    if request.node.get_closest_marker("live"):
        return

    def blocked(*args, **kwargs):
        raise AssertionError("Outbound socket use is forbidden in offline tests")

    # Windows asyncio implements its self-pipe with a loopback socket pair.
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def connect(sock, address):
        if isinstance(address, tuple) and address[0] in {
            "127.0.0.1",
            "::1",
            "localhost",
        }:
            return original_connect(sock, address)
        return blocked()

    def connect_ex(sock, address):
        if isinstance(address, tuple) and address[0] in {
            "127.0.0.1",
            "::1",
            "localhost",
        }:
            return original_connect_ex(sock, address)
        return blocked()

    async def async_blocked(*args, **kwargs):
        return blocked()

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
    # In particular, no accidental Bifrost request can spend money through loopback.
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", async_blocked)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked)
