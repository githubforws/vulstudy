class VulfocusException(Exception):
    def __init__(self, code: int = 400, message: str = "错误", data=None):
        self.code = code
        self.message = message
        self.data = data or {}
        super().__init__(message)


class PermissionDenied(VulfocusException):
    def __init__(self, message: str = "权限不足"):
        super().__init__(code=403, message=message)


class NotFound(VulfocusException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=404, message=message)


class ValidationError(VulfocusException):
    def __init__(self, message: str = "参数验证失败"):
        super().__init__(code=400, message=message)


class ServerError(VulfocusException):
    def __init__(self, message: str = "服务器内部错误"):
        super().__init__(code=500, message=message)