class SlowDatabase:
    def __init__(self):
        self.data = {}

    def seed(self, entries):
        self.data.update(entries)
