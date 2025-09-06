from pydantic import BaseModel, EmailStr, Field
from typing_extensions import Optional, TypedDict
from uuid import UUID
from enum import Enum


class AuthResponse(BaseModel):
    """
    Represents a response to an authentication request.

    Contains the following information:
    - success: Whether the authentication succeeded.
    - accessToken: The JWT access token.
    """

    success: bool = Field(..., description="Whether the authentication succeeded")
    accessToken: str = Field(..., alias="accessToken", description="JWT access Token")


class RegisterRequest(BaseModel):
    """
    Represents a request to register a new user.

    Contains the following information:
    - name: The user's name.
    - email: The user's email address.
    - password: The user's password.
    """

    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """
    Represents a request to log in a user.

    Contains the following information:
    - email: The user's email address.
    - password: The user's password.
    """

    email: EmailStr
    password: str


class ClientMeta(BaseModel):
    user_agent: Optional[str]
    ip_address: Optional[str]


class RegisterData(ClientMeta):
    """
    Represents a request to register a new user.

    Contains the following information:
    - name: The user's name.
    - email: The user's email address.
    - password: The user's password.
    - user_agent: The user's user agent.
    - ip_address: The user's IP address.
    """

    name: str
    email: EmailStr
    password: str


class LoginData(ClientMeta):
    """
    Represents a request to log in a user.

    Contains the following information:
    - email: The user's email address.
    - password: The user's password.
    - user_agent: The user's user agent.
    - ip_address: The user's IP address.
    """

    email: EmailStr
    password: str


class AuthGuard(BaseModel):
    """
    Represents a request to log in a user.

    Contains the following information:
    - user_id: The user's ID.
    - session_id: The user's session ID.
    """

    user_id: UUID
    session_id: UUID


class payloadToken(TypedDict):
    user_id: str
    session_id: str
    iat: int
    exp: int


class AuthProvider(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"


class UserMe(BaseModel):
    """
    name: str
    profilePic: Optional[str]
    """

    name: str
    profilePic: Optional[str] = Field(None, alias="profilePic")
