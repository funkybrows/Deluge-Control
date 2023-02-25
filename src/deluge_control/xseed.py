xseed_client = None


def get_xseed_client():
    global xseed_client
    if not xseed_client:
        xseed_client = XSeedClient()
    return xseed_client


class XSeedClient:
    @classmethod
    def cross_seed(torrent):
        pass
