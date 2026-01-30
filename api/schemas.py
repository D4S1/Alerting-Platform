from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal

class ServiceCreate(BaseModel):
    name: str
    IP: str
    frequency_seconds: int
    alerting_window_npings: int
    failure_threshold: int


class ServiceEdit(BaseModel):
    frequency_seconds: int
    alerting_window_npings: int
    failure_threshold: int


class ServiceOut(BaseModel):
    id: int
    name: str
    IP: str
    frequency_seconds: int
    alerting_window_npings: int
    failure_threshold: int

    class Config:
        from_attributes = True


class AdminCreate(BaseModel):
    name: str
    contact_type: str
    contact_value: str


class AdminOut(BaseModel):
    id: int
    name: str
    contact_type: str
    contact_value: str

    class Config:
        from_attributes = True


class AdminContactUpdate(BaseModel):
    contact_type: Optional[str] = None
    contact_value: Optional[str] = None


class ServiceAdminCreate(BaseModel):
    admin_id: int
    role: Literal["primary", "secondary"]


class ServiceAdminUpdate(BaseModel):
    role: Literal["primary", "secondary"]
    new_admin_id: int


class IncidentCreate(BaseModel):
    service_id: int


class IncidentUpdateStatus(BaseModel):
    status: str


class IncidentUpdateEndedAt(BaseModel):
    ended_at: datetime


class ContactAttemptCreate(BaseModel):
    incident_id: int
    admin_id: int
    channel: str
