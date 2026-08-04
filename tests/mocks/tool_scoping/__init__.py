class PermissionLevel:
    READ = "read"
    WRITE = "write"


class ToolScopeManager:
    def __init__(self, *args, **kwargs):
        pass

    def grant_permission(self, user_id, tool, permission_level):
        pass

    def check_permission(self, user_id, tool):
        return (True, "mock_context")
