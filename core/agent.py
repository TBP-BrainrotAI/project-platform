from abc import ABC, abstractmethod


class Agent(ABC):

    def __init__(self, name):
        self.name = name
        self.available = True

    @abstractmethod
    def ask(self, prompt):
        pass

    def __str__(self):
        status = "ONLINE" if self.available else "OFFLINE"
        return f"{self.name} [{status}]"