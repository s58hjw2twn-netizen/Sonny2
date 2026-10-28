"""Actual loopback MCP handshake smoke test; never deploy this server publicly."""
import asyncio
import socket
import subprocess
import sys
import time

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}/mcp"

async def check():
    async with streamablehttp_client(URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert [t.name for t in tools.tools] == ["protocol_status"]
            result = await session.call_tool("protocol_status", {})
            assert not result.isError
            assert result.structuredContent is not None
            assert result.structuredContent["production_ready"] == "false"
            print("MCP initialize, tools/list and tools/call passed over loopback HTTP")

def main():
    with socket.socket() as s:
        assert s.connect_ex((HOST, PORT)) != 0, "Test port already occupied"
    proc = subprocess.Popen(
        [sys.executable, "-m", "sonny.mcp_local_spike"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        for _ in range(60):
            if proc.poll() is not None:
                raise RuntimeError("MCP server exited before startup")
            with socket.socket() as s:
                if s.connect_ex((HOST, PORT)) == 0:
                    break
            time.sleep(0.1)
        else:
            raise RuntimeError("MCP loopback listener did not start")
        asyncio.run(check())
    finally:
        proc.terminate()
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()

if __name__ == "__main__":
    main()
