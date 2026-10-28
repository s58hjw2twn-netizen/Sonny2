"""Verify the protected ASGI wrapper forwards real server lifespan events.

The production entrypoint must initialize and close the MCP session manager
through ASGI lifespan rather than relying on test-only manual setup.
"""
import asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from sonny.mcp_protected_local import build_app
from sonny.mcp_resource_auth import ResourceAuthConfig


def test_protected_app_lifespan_startup_and_shutdown():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    config = ResourceAuthConfig(
        "https://issuer.example", "https://sonny.example/mcp", public_key
    )
    app = build_app(config, resource_url=config.audience)

    async def run():
        incoming = asyncio.Queue()
        outgoing = asyncio.Queue()

        async def receive():
            return await incoming.get()

        async def send(message):
            await outgoing.put(message)

        task = asyncio.create_task(app({"type": "lifespan"}, receive, send))
        try:
            await incoming.put({"type": "lifespan.startup"})
            started = await asyncio.wait_for(outgoing.get(), timeout=5)
            assert started["type"] == "lifespan.startup.complete", started
            await incoming.put({"type": "lifespan.shutdown"})
            stopped = await asyncio.wait_for(outgoing.get(), timeout=5)
            assert stopped["type"] == "lifespan.shutdown.complete", stopped
            await asyncio.wait_for(task, timeout=5)
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)

    asyncio.run(run())
