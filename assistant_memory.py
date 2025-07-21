# assistant_memory.py
class ShortTermMemory:
    def __init__(self):
        self.memory = {}

    def update(self, key, value):
        self.memory[key] = value

    def get(self, key, default=None):
        return self.memory.get(key, default)

    def clear(self):
        self.memory = {}

    def get_all(self):
        return self.memory
