# assistant_memory.py
# This module provides a simple in-memory storage solution for the assistant.
# It's used to retain information within a single session, such as conversation history,
# user preferences, or cached results from tool calls.

class ShortTermMemory:
    """
    A simple dictionary-based class for short-term memory management.
    This allows the assistant to store and retrieve key-value data during its runtime.
    """
    def __init__(self):
        """
        Initializes the memory as an empty dictionary.
        """
        self.memory = {}

    def update(self, key, value):
        """
        Adds or updates a key-value pair in the memory.

        Args:
            key: The key to store the data under.
            value: The data to be stored.
        """
        self.memory[key] = value

    def get(self, key, default=None):
        """
        Retrieves a value from memory associated with the given key.

        Args:
            key: The key of the data to retrieve.
            default: The value to return if the key is not found.

        Returns:
            The stored value, or the default value if the key does not exist.
        """
        return self.memory.get(key, default)

    def clear(self):
        """
        Resets the memory, clearing all stored data.
        """
        self.memory = {}

    def get_all(self):
        """
        Retrieves the entire memory dictionary.

        Returns:
            A dictionary containing all key-value pairs stored in memory.
        """
        return self.memory
