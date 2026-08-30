"""User persistence for the permission system (Road_Map Step 24)."""

from typing import ClassVar, Optional

from open_notebook.domain.base import ObjectModel


class User(ObjectModel):
    """A user account with a role (admin or member)."""

    table_name: ClassVar[str] = "user"
    email: Optional[str] = None
    role: Optional[str] = None
    password_hash: Optional[str] = None
