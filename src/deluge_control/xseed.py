import aiohttp

xseed_client = None


def get_xseed_client():
    global xseed_client
    if not xseed_client:
        xseed_client = XSeedClient()
    return xseed_client


class XSeedClient:
    @classmethod
    async def cross_seed(torrent):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"http://cross-seed:2468") as response:
                print("Status:", response.status)
                html = await response.text()
