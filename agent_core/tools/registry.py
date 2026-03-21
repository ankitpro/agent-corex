class ToolRegistry:
    def __init__(self):
        self.tools = []

    def register(self, tool: dict):
        self.tools.append(tool)

    def get_all_tools(self):
        return self.tools