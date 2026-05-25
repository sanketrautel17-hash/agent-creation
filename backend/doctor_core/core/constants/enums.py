from enum import Enum


class UserRole(str, Enum):
    PATIENT = "patient"
    ADMIN = "admin"


class InviteStatus(str, Enum):
    PENDING = "pending"
    ACTIVATED = "activated"
    EXPIRED = "expired"
    REVOKED = "revoked"


class OtpPurpose(str, Enum):
    SIGNUP = "signup"
    LOGIN = "login"


class AgentType(str, Enum):
    APPOINTMENT = "appointment"
    FOLLOWUP = "followup"
    PRESCRIPTION = "prescription"
