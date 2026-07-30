from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


class UserRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: SecretStr = Field(min_length=15, max_length=128)


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str = Field(repr=False)
    token_type: Literal["bearer"] = "bearer"


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detail: str
