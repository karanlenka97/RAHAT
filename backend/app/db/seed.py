"""Database seeding infrastructure and development test users."""
import logging
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.user import User
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

# Exact 8 System RBAC Roles defined in specification
SYSTEM_ROLES = [
    {
        "name": "ADMIN",
        "description": "Full system administrative access across state and national levels.",
        "permissions": ["*"],
    },
    {
        "name": "DISTRICT_ADMIN",
        "description": "District-level administrative access, facility management, and referral analytics.",
        "permissions": ["facility:read", "facility:write", "referral:read", "analytics:read", "audit:read"],
    },
    {
        "name": "FACILITY_ADMIN",
        "description": "Facility-level administrative access, live bed capacity, and staff scheduling.",
        "permissions": ["facility:read", "facility:write", "capacity:write", "staff:write", "referral:read"],
    },
    {
        "name": "DOCTOR",
        "description": "Specialist clinical access for patient triage, referral admission, and clinical orders.",
        "permissions": ["patient:read", "patient:write", "care_request:read", "referral:read", "referral:write"],
    },
    {
        "name": "MEDICAL_OFFICER",
        "description": "Primary healthcare center medical officer conducting consultations and referral triage.",
        "permissions": ["patient:read", "patient:write", "care_request:read", "care_request:write", "referral:read", "referral:write"],
    },
    {
        "name": "CHO",
        "description": "Community Health Officer at Health and Wellness Center providing frontline care.",
        "permissions": ["patient:read", "patient:write", "care_request:read", "care_request:write", "referral:read"],
    },
    {
        "name": "ANM",
        "description": "Auxiliary Nurse Midwife providing maternal, child, and village healthcare outreach.",
        "permissions": ["patient:read", "patient:write", "care_request:write", "followup:read", "followup:write"],
    },
    {
        "name": "ASHA",
        "description": "Accredited Social Health Activist conducting home visits, screening, and post-discharge follow-ups.",
        "permissions": ["patient:read", "patient:write", "care_request:write", "followup:write"],
    },
]

# Synthetic Development Users (Default password: RahatDev@2026)
DEV_PASSWORD_PLAIN = "RahatDev@2026"

DEV_USERS = [
    {
        "role_name": "ADMIN",
        "full_name": "System Administrator",
        "phone": "+919000000001",
        "email": "admin@rahat.local",
    },
    {
        "role_name": "DISTRICT_ADMIN",
        "full_name": "District Health Officer",
        "phone": "+919000000002",
        "email": "district.admin@rahat.local",
    },
    {
        "role_name": "FACILITY_ADMIN",
        "full_name": "Facility Superintendent",
        "phone": "+919000000003",
        "email": "facility.admin@rahat.local",
    },
    {
        "role_name": "DOCTOR",
        "full_name": "Dr. Rajesh Varma (Specialist)",
        "phone": "+919000000004",
        "email": "doctor@rahat.local",
    },
    {
        "role_name": "MEDICAL_OFFICER",
        "full_name": "Dr. Sunita Patel (MO)",
        "phone": "+919000000005",
        "email": "medical.officer@rahat.local",
    },
    {
        "role_name": "CHO",
        "full_name": "Pooja Mishra (CHO)",
        "phone": "+919000000006",
        "email": "cho@rahat.local",
    },
    {
        "role_name": "ANM",
        "full_name": "Kavita Devi (ANM)",
        "phone": "+919000000007",
        "email": "anm@rahat.local",
    },
    {
        "role_name": "ASHA",
        "full_name": "Manju Bai (ASHA)",
        "phone": "+919000000008",
        "email": "asha@rahat.local",
    },
]


def seed_roles(db: Session) -> int:
    """Seed the 8 exact RBAC system roles idempotently."""
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
        else:
            # Update permissions & description if changed
            existing.description = role_data["description"]
            existing.permissions = role_data["permissions"]
    db.commit()
    return created_count


def seed_dev_users(db: Session) -> int:
    """Seed synthetic development users for each of the 8 roles."""
    created_count = 0
    hashed_pwd = get_password_hash(DEV_PASSWORD_PLAIN)

    for user_info in DEV_USERS:
        role = db.query(Role).filter(Role.name == user_info["role_name"]).first()
        if not role:
            continue

        existing = db.query(User).filter(
            (User.email == user_info["email"]) | (User.phone == user_info["phone"])
        ).first()

        if not existing:
            new_user = User(
                role_id=role.id,
                full_name=user_info["full_name"],
                phone=user_info["phone"],
                email=user_info["email"],
                hashed_password=hashed_pwd,
                is_active=True,
                is_verified=True,
            )
            db.add(new_user)
            created_count += 1
        else:
            # Ensure role and active status
            existing.role_id = role.id
            existing.is_active = True
            existing.hashed_password = hashed_pwd

    db.commit()
    return created_count


def run_seeds(db: Session) -> dict:
    """Master seeding entry point for roles and dev users."""
    roles_seeded = seed_roles(db)
    users_seeded = seed_dev_users(db)
    logger.info(f"Seeding completed. Roles added/updated: {roles_seeded}, Users added/updated: {users_seeded}")
    return {
        "status": "success",
        "roles_seeded": roles_seeded,
        "users_seeded": users_seeded,
    }
