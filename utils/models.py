from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, CheckConstraint, func
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    IP = Column(String, nullable=False)
    frequency_seconds = Column(Integer, nullable=False)
    alerting_window_npings = Column(Integer, nullable=False)

    incidents = relationship("Incident", back_populates="service")
    admins = relationship("ServiceAdmin", back_populates="service")


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact_type = Column(String, nullable=False)
    contact_value = Column(String, nullable=False)

    services = relationship("ServiceAdmin", back_populates="admin")
    contact_attempts = relationship("ContactAttempt", back_populates="admin")


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
    contact_attempts = relationship("ContactAttempt", back_populates="incident")


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
