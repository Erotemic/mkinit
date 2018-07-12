class SimpleLog(object):
    """
    Simple logger that does not interact with Python's logger by default, but
    could be monkey patched to do so.
    """
    def __init__(self):
        self.enabled = False
        self.backend = print

    def info(self, msg):
        if self.enabled:
            self.backend(msg)

    def debug(self, msg):
        if self.enabled:
            self.backend(msg)
