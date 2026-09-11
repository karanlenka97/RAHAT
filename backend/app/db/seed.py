"""Database seeding infrastructure: RBAC roles, test users, sample villages, and synthetic patients."""
import logging
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.user import User
from app.models.village import Village
from app.models.patient import Patient
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
        "permissions": ["facility:read", "facility:write", "patient:read", "patient:write", "referral:read", "analytics:read", "audit:read"],
    },
    {
        "name": "FACILITY_ADMIN",
        "description": "Facility-level administrative access, live bed capacity, and staff scheduling.",
        "permissions": ["facility:read", "facility:write", "capacity:write", "staff:write", "patient:read", "patient:write", "referral:read"],
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

# Synthetic Villages
SAMPLE_VILLAGES = [
    {
        "name": "Kansbahal",
        "code": "VIL-OR-SNG-001",
        "sub_district_tehsil": "Lathikata",
        "district": "Sundargarh",
        "state": "Odisha",
        "pincode": "770034",
        "population": 4200,
        "latitude": 22.18,
        "longitude": 84.73,
    },
    {
        "name": "Lathikata",
        "code": "VIL-OR-SNG-002",
        "sub_district_tehsil": "Lathikata",
        "district": "Sundargarh",
        "state": "Odisha",
        "pincode": "770037",
        "population": 6800,
        "latitude": 22.15,
        "longitude": 84.82,
    },
    {
        "name": "Birkera",
        "code": "VIL-OR-SNG-003",
        "sub_district_tehsil": "Rourkela",
        "district": "Sundargarh",
        "state": "Odisha",
        "pincode": "769012",
        "population": 3500,
        "latitude": 22.25,
        "longitude": 84.89,
    },
]

# Synthetic Patients
SAMPLE_PATIENTS = [
    {
        "patient_code": "RAHAT-P-000001",
        "full_name": "Aarav Sharma (Demo)",
        "age": 42,
        "gender": "MALE",
        "phone": "+919800000001",
        "village_code": "VIL-OR-SNG-001",
        "address": "House 12, Main Basti, Kansbahal",
        "emergency_contact_name": "Sunita Sharma",
        "emergency_contact_phone": "+919800000011",
        "abha_reference": "91-1001-2002-3001",
        "blood_group": "B+",
        "chronic_conditions": ["Hypertension"],
        "allergies": ["Penicillin"],
    },
    {
        "patient_code": "RAHAT-P-000002",
        "full_name": "Priya Patel (Demo)",
        "age": 28,
        "gender": "FEMALE",
        "phone": "+919800000002",
        "village_code": "VIL-OR-SNG-001",
        "address": "Near Panchayat Bhawan, Kansbahal",
        "emergency_contact_name": "Ramesh Patel",
        "emergency_contact_phone": "+919800000012",
        "abha_reference": "91-1001-2002-3002",
        "blood_group": "O+",
        "chronic_conditions": ["Gestational Diabetes"],
        "allergies": [],
    },
    {
        "patient_code": "RAHAT-P-000003",
        "full_name": "Rohan Das (Demo)",
        "age": 65,
        "gender": "MALE",
        "phone": "+919800000003",
        "village_code": "VIL-OR-SNG-002",
        "address": "Station Road, Lathikata",
        "emergency_contact_name": "Deepak Das",
        "emergency_contact_phone": "+919800000013",
        "abha_reference": "91-1001-2002-3003",
        "blood_group": "A+",
        "chronic_conditions": ["COPD", "Type 2 Diabetes"],
        "allergies": ["Sulfa drugs"],
    },
    {
        "patient_code": "RAHAT-P-000004",
        "full_name": "Meena Nayak (Demo)",
        "age": 34,
        "gender": "FEMALE",
        "phone": "+919800000004",
        "village_code": "VIL-OR-SNG-002",
        "address": "Bazaar Para, Lathikata",
        "emergency_contact_name": "Bijay Nayak",
        "emergency_contact_phone": "+919800000014",
        "abha_reference": "91-1001-2002-3004",
        "blood_group": "AB+",
        "chronic_conditions": [],
        "allergies": [],
    },
    {
        "patient_code": "RAHAT-P-000005",
        "full_name": "Sunil Majhi (Demo)",
        "age": 19,
        "gender": "MALE",
        "phone": "+919800000005",
        "village_code": "VIL-OR-SNG-003",
        "address": "Colony No. 4, Birkera",
        "emergency_contact_name": "Karan Majhi",
        "emergency_contact_phone": "+919800000015",
        "abha_reference": "91-1001-2002-3005",
        "blood_group": "O-",
        "chronic_conditions": ["Asthma"],
        "allergies": ["Aspirin"],
    },
    {
        "patient_code": "RAHAT-P-000006",
        "full_name": "Anita Sahu (Demo)",
        "age": 51,
        "gender": "FEMALE",
        "phone": "+919800000006",
        "village_code": "VIL-OR-SNG-003",
        "address": "Near High School, Birkera",
        "emergency_contact_name": "Prabhat Sahu",
        "emergency_contact_phone": "+919800000016",
        "abha_reference": "91-1001-2002-3006",
        "blood_group": "B-",
        "chronic_conditions": ["Hypertension"],
        "allergies": [],
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
            existing.role_id = role.id
            existing.is_active = True
            existing.hashed_password = hashed_pwd

    db.commit()
    return created_count


def seed_villages(db: Session) -> int:
    """Seed sample synthetic villages for patient registration."""
    created_count = 0
    for v_data in SAMPLE_VILLAGES:
        existing = db.query(Village).filter(Village.code == v_data["code"]).first()
        if not existing:
            village = Village(
                name=v_data["name"],
                code=v_data["code"],
                sub_district_tehsil=v_data["sub_district_tehsil"],
                district=v_data["district"],
                state=v_data["state"],
                pincode=v_data["pincode"],
                population=v_data["population"],
                latitude=v_data["latitude"],
                longitude=v_data["longitude"],
            )
            db.add(village)
            created_count += 1
    db.commit()
    return created_count


def seed_synthetic_patients(db: Session) -> int:
    """Seed 6 synthetic demo patients associated with sample villages."""
    created_count = 0
    for p_data in SAMPLE_PATIENTS:
        existing = db.query(Patient).filter(Patient.anonymous_patient_code == p_data["patient_code"]).first()
        if not existing:
            village = db.query(Village).filter(Village.code == p_data["village_code"]).first()
            patient = Patient(
                anonymous_patient_code=p_data["patient_code"],
                full_name=p_data["full_name"],
                age=p_data["age"],
                gender=p_data["gender"],
                phone=p_data["phone"],
                village_id=village.id if village else None,
                address_line=p_data["address"],
                emergency_contact_name=p_data["emergency_contact_name"],
                emergency_contact_phone=p_data["emergency_contact_phone"],
                abha_id=p_data["abha_reference"],
                blood_group=p_data["blood_group"],
                chronic_conditions=p_data["chronic_conditions"],
                allergies=p_data["allergies"],
            )
            db.add(patient)
            created_count += 1
    db.commit()
    return created_count


def run_seeds(db: Session) -> dict:
    """Master seeding entry point for roles, users, villages, and demo patients."""
    roles_seeded = seed_roles(db)
    users_seeded = seed_dev_users(db)
    villages_seeded = seed_villages(db)
    patients_seeded = seed_synthetic_patients(db)

    logger.info(
        f"Seeding completed. Roles: {roles_seeded}, Users: {users_seeded}, "
        f"Villages: {villages_seeded}, Patients: {patients_seeded}"
    )
    return {
        "status": "success",
        "roles_seeded": roles_seeded,
        "users_seeded": users_seeded,
        "villages_seeded": villages_seeded,
        "patients_seeded": patients_seeded,
    }
