"""User management API for the permission system (Road_Map Step 24).

This is the foundational account layer (email + role). Password hashing and
per-resource data scoping are deliberately separate hardening steps.
"""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from open_notebook.domain.user import User
from open_notebook.exceptions import InvalidInputError

router = APIRouter()

_ROLES = {"admin", "member"}


class UserCreate(BaseModel):
    email: str
    role: str = "member"


class UserResponse(BaseModel):
    id: Optional[str]
    email: Optional[str]
    role: Optional[str]


def _to_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, role=user.role)


@router.get("/users", response_model=list[UserResponse])
async def list_users() -> list[UserResponse]:
    users = await User.get_all(order_by="updated desc")
    return [_to_response(user) for user in users]


@router.post("/users", response_model=UserResponse)
async def create_user(request: UserCreate) -> UserResponse:
    email = request.email.strip()
    if not email:
        raise InvalidInputError("User email cannot be empty.")
    if request.role not in _ROLES:
        raise InvalidInputError(f"Invalid role: {request.role}")

    user = User(email=email, role=request.role)
    await user.save()
    return _to_response(user)


@router.delete("/users/{user_id}")
async def delete_user(user_id: str) -> dict[str, bool]:
    user = await User.get(user_id)
    await user.delete()
    return {"deleted": True}
