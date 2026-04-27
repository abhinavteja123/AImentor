"""Bypass SQLAlchemy to isolate whether the failure is asyncpg/network vs config."""

import asyncio
import socket
import ssl
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

HOST = "aws-1-ap-southeast-2.pooler.supabase.com"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 6543
USER = "postgres.imrilpldnvfbsobtxyzo"
PASSWORD = "DadMomand1432"


async def main() -> None:
    # Step 1: DNS
    try:
        infos = socket.getaddrinfo(HOST, PORT, proto=socket.IPPROTO_TCP)
        print("DNS OK:", [(fam.name, addr) for fam, _, _, _, addr in infos])
    except Exception as e:
        print("DNS FAIL:", e)
        return

    # Step 2: Raw TCP connect
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(HOST, PORT), timeout=10
        )
        print("TCP OK")
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print("TCP FAIL:", type(e).__name__, e)
        return

    # Step 3: asyncpg direct
    import asyncpg
    try:
        conn = await asyncpg.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database="postgres",
            ssl="require",
            statement_cache_size=0,
            timeout=15,
        )
        row = await conn.fetchrow("SELECT 1 AS ok, current_user, current_database()")
        print("ASYNCPG OK:", dict(row))
        await conn.close()
    except Exception as e:
        print("ASYNCPG FAIL:", type(e).__name__, repr(e))


asyncio.run(main())
