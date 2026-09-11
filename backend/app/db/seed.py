"""Database seeding infrastructure and core system role initializers."""
import logging
from sqlalchemy.orm import Session
from app.models.role import Role

logger = logging.getLogger(__name__)

# Standard System RBAC Roles
SYSTEM_ROLES = [
    {
        "name": "SUPER_ADMIN",
        "description": "State and national platform super administrator with global visibility and access.",
        "permissions": ["*"],
    },
    {
        "name": "DISTRICT_OFFICER",
        "description": "District medical and health officer managing regional facilities and referral performance.",
        "permissions": ["facility:read", "referral:read", "analytics:read", "audit:read"],
    },
    {
        "name": "FACILITY_ADMIN",
        "description": "Hospital administrator managing bed capacity, resources, and clinical staff.",
        "permissions": ["facility:write", "capacity:write", "staff:write", "referral:read", "referral:write"],
    },
    {
        "name": "DOCTOR",
        "description": "Specialist and general medical officers evaluating care requests and admitting referrals.",
        "permissions": ["patient:read", "patient:write", "care_request:read", "referral:read", "referral:write"],
    },
    {
        "name": "NURSE",
        "description": "Staff nurse updating live patient vitals, bed allocation, and inpatient tracking.",
        "permissions": ["patient:read", "capacity:write", "care_request:read", "referral:read"],
    },
    {
        "name": "ASHA_WORKER",
        "description": "Accredited Social Health Activist conducting village screenings and follow-ups.",
        "permissions": ["patient:read", "patient:write", "care_request:write", "followup:write"],
    },
    {
        "name": "PARAMEDIC",
        "description": "Emergency transport and 108/102 ambulance staff tracking en-route transit.",
        "permissions": ["referral:read", "transport:write"],
    },
    {
        "name": "PATIENT",
        "description": "Citizen / Patient portal access for personal referral status and prescriptions.",
        "permissions": ["self:read"],
    },
]


def seed_roles(db: Session) -> int:
    """Seed foundational system roles idempotently."""
    created_count = 0
    for role_data in SYSTEM_ROLES:
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing:
            new_role = Role(
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
            )
            db.add(new_role)
            created_count += 1
    db.commit()
    return created_count


def run_seeds(db: Session) -> dict:
    """Master seeding entry point for initial database foundation."""
    roles_seeded = seed_roles(db)
    logger.info(f"Seeding completed. Roles added: {roles_seeded}")
    return {
        "status": "success",
        "roles_seeded": roles_seeded,
    }
