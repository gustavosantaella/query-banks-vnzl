
from typing import Union
class Response:

    def __init__(self, status: str = "success", message: str = "", data: Union[dict, str, None] = None, meta: dict = None, code: int = 200):
        self.status = status
        self.message = message
        self.data = data
        self.meta = meta
        self.code = code

    def to_dict(self):
        return {
            "status": self.status,
            "message": self.message,
            "data": self.data,
            "meta": self.meta,
            "code": self.code
        }