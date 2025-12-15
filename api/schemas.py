from pydantic import BaseModel
from typing import Optional

class ServiceCreate(BaseModel):
    name: str
    IP: str
    frequency_seconds: int
    alerting_window_seconds: int


class AdminContactUpdate(BaseModel):
    contact_type: Optional[str] = None
    contact_value: Optional[str] = None


class ServiceAdminUpdate(BaseModel):
    admin_id: int
    role: str  # "primary"/"secondary"
