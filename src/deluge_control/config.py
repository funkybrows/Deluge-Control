import profig

cfg = profig.Config("settings.cfg")

def init():
    global cfg

    # Settings
    cfg.init("deluge.host", "127.0.0.1")
    cfg.init("deluge.port", "58846")
    cfg.init("deluge.username", "admin")
    cfg.init("deluge.password", "password")

    cfg.init("tests.root_dir", ".")
    cfg.sync()
    return cfg