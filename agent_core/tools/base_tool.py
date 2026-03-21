from abc import ABC, abstractmethod


class BaseTool(ABC):

    name = ""

    @abstractmethod
    async def run(self, **kwargs):
        pass
