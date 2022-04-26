from pydantic import BaseModel


class APIKeyAndSalt(BaseModel):
    api_key: bytes
    salt: bytes
