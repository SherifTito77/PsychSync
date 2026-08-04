class ApprovalRequest:
    def __init__(self, id):
        self.request_id = id


class ApprovalWorkflow:
    def __init__(self, *args, **kwargs):
        pass

    async def request_approval(self, *args, **kwargs):
        return True

    def create_approval_request(self, *args, **kwargs):
        return ApprovalRequest(id="mock_id")
