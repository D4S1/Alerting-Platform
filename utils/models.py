from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, CheckConstraint, func
)
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    IP = Column(String, nullable=False)
    frequency_seconds = Column(Integer, nullable=False)
    alerting_window_npings = Column(Integer, nullable=False)
    failure_threshold = Column(Integer, nullable=False, default=3)
    next_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now(timezone.utc) + timedelta(seconds=60),
    )

    # Cascade delete incidents and service_admins when service is deleted
    incidents = relationship(
        "Incident",
        back_populates="service",
        cascade="all, delete-orphan"
    )
    admins = relationship(
        "ServiceAdmin",
        back_populates="service",
        cascade="all, delete-orphan"
    )


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact_type = Column(String, nullable=False)
    contact_value = Column(String, nullable=False)

    services = relationship("ServiceAdmin", back_populates="admin")
    contact_attempts = relationship(
        "ContactAttempt",
        back_populates="admin",
        cascade="all, delete-orphan"
    )


class ServiceAdmin(Base):
    __tablename__ = "service_admins"

    service_id = Column(Integer, ForeignKey("services.id"), primary_key=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), primary_key=True)
    role = Column(String, nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('primary', 'secondary')"),
    )

    service = relationship("Service", back_populates="admins")
    admin = relationship("Admin", back_populates="services")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)

    started_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        server_default=func.now()
    )

    ended_at = Column(DateTime)

    status = Column(
        String,
        nullable=False,
        default="registered",
        server_default="registered"
    )

    __table_args__ = (
        CheckConstraint("status IN ('registered', 'acknowledged', 'resolved')"),
    )

    service = relationship("Service", back_populates="incidents")
    contact_attempts = relationship(
        "ContactAttempt",
        back_populates="incident",
        cascade="all, delete-orphan"
    )


class ContactAttempt(Base):
    __tablename__ = "contact_attempts"

    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False)

    attempted_at = Column(DateTime, nullable=False)
    channel = Column(String, nullable=False)
    result = Column(String)
    response_at = Column(DateTime)

    incident = relationship("Incident", back_populates="contact_attempts")
    admin = relationship("Admin", back_populates="contact_attempts")


class PingFailure(Base):
    __tablename__ = "ping_failures"

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id"), index=True)
    failed_at = Column(DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc))
