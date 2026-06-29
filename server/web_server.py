"""
Keep-alive web server (for Render free tier + UptimeRobot)
"""

import os
from aiohttp import web

async def ping_handler(request):
    return web.Response(text="Bot is alive ✅")


async def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    web_app = web.Application()
    web_app.router.add_get("/", ping_handler)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Keep-alive web server running on port {port}")
