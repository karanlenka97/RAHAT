"""Database seeding infrastructure: RBAC roles, test users, sample villages, and synthetic patients."""
import logging
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.user import User
from app.models.village import Village
from app.models.patient import Patient
from app.models.care_request import CareRequest
from app.models.facility import Facility, FacilityCapability
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


SAMPLE_CARE_REQUESTS = [
    {
        "request_number": "CR-RAHAT-000001",
        "patient_code": "RAHAT-P-000001",
        "creator_email": "asha@rahat.local",
        "care_category": "GENERAL_MEDICINE",
        "required_service": "General Medicine",
        "urgency_level": "LOW",
        "chief_complaint": "Persistent dry cough and mild evening fever for 4 days with throat irritation",
        "diagnostic_requirements": ["CBC", "Chest X-Ray"],
        "specialist_required": False,
        "notes": "Patient reported no hemoptysis or breathing difficulty. Routine sub-center observation advised.",
    },
    {
        "request_number": "CR-RAHAT-000002",
        "patient_code": "RAHAT-P-000002",
        "creator_email": "anm@rahat.local",
        "care_category": "MATERNAL_HEALTH",
        "required_service": "Obstetrics & Gynecology",
        "urgency_level": "MEDIUM",
        "chief_complaint": "Third-trimester pregnancy with borderline elevated fasting glucose readings",
        "diagnostic_requirements": ["Fasting Blood Sugar", "Obstetric Ultrasound", "Urine Routine"],
        "specialist_required": True,
        "notes": "High-risk pregnancy protocol. Specialist obstetric consultation requested at CHC.",
    },
    {
        "request_number": "CR-RAHAT-000003",
        "patient_code": "RAHAT-P-000003",
        "creator_email": "cho@rahat.local",
        "care_category": "EMERGENCY",
        "required_service": "Cardiology",
        "urgency_level": "EMERGENCY",
        "chief_complaint": "Acute crushing retrosternal chest pain radiating to left shoulder and arm with profuse diaphoresis",
        "diagnostic_requirements": ["12-Lead ECG", "Troponin I", "CBC", "Echocardiogram"],
        "specialist_required": True,
        "notes": "Emergency triage initiated. Sublingual nitrate and aspirin given. Immediate emergency transfer recommended.",
    },
    {
        "request_number": "CR-RAHAT-000004",
        "patient_code": "RAHAT-P-000004",
        "creator_email": "doctor@rahat.local",
        "care_category": "NCD",
        "required_service": "Endocrinology",
        "urgency_level": "LOW",
        "chief_complaint": "Quarterly chronic disease review and diabetic neuropathy screening",
        "diagnostic_requirements": ["HbA1c", "Lipid Profile", "Serum Creatinine"],
        "specialist_required": False,
        "notes": "Medication compliance satisfactory. Continued dietary guidance provided.",
    },
    {
        "request_number": "CR-RAHAT-000005",
        "patient_code": "RAHAT-P-000005",
        "creator_email": "asha@rahat.local",
        "care_category": "CHILD_HEALTH",
        "required_service": "Pediatrics",
        "urgency_level": "MEDIUM",
        "chief_complaint": "Recurrent wheezing exacerbations triggered by seasonal temperature changes",
        "diagnostic_requirements": ["Chest X-Ray", "Spirometry"],
        "specialist_required": True,
        "notes": "Assess pediatric meter-dose inhaler spacer technique with guardian.",
    },
    {
        "request_number": "CR-RAHAT-000006",
        "patient_code": "RAHAT-P-000006",
        "creator_email": "anm@rahat.local",
        "care_category": "EYE_CARE",
        "required_service": "Ophthalmology",
        "urgency_level": "LOW",
        "chief_complaint": "Progressive painless diminution of distant vision with difficulty in nocturnal navigation",
        "diagnostic_requirements": ["Visual Acuity Test", "Slit Lamp Examination", "Intraocular Pressure"],
        "specialist_required": True,
        "notes": "Suspected bilateral senile nuclear cataract. Scheduled for elective ophthalmic triage.",
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


def seed_synthetic_care_requests(db: Session) -> int:
    """Seed 6 synthetic demo care requests associated with sample patients."""
    created_count = 0
    for cr_data in SAMPLE_CARE_REQUESTS:
        existing = db.query(CareRequest).filter(CareRequest.request_number == cr_data["request_number"]).first()
        if not existing:
            patient = db.query(Patient).filter(Patient.anonymous_patient_code == cr_data["patient_code"]).first()
            user = db.query(User).filter(User.email == cr_data["creator_email"]).first()
            if not patient or not user:
                continue

            care_req = CareRequest(
                request_number=cr_data["request_number"],
                patient_id=patient.id,
                village_id=patient.village_id,
                created_by_user_id=user.id,
                care_category=cr_data["care_category"],
                required_service=cr_data["required_service"],
                urgency_level=cr_data["urgency_level"],
                chief_complaint=cr_data["chief_complaint"],
                diagnostic_requirements=cr_data["diagnostic_requirements"],
                specialist_required=cr_data["specialist_required"],
                notes=cr_data["notes"],
                status="SUBMITTED",
            )
            db.add(care_req)
            created_count += 1
    db.commit()
    return created_count


# Synthetic Healthcare Facilities & Capabilities
SAMPLE_FACILITIES = [
    {
        "name": "Ayushman Arogya Mandir - Kansbahal",
        "code": "FAC-OR-SNG-AAM01",
        "facility_type": "AAM",
        "tier_level": 1,
        "district": "Sundargarh",
        "state": "Odisha",
        "address_line": "Near Gram Panchayat Office, Kansbahal",
        "pincode": "770034",
        "latitude": 22.1812,
        "longitude": 84.7315,
        "contact_phone": "+916624200001",
        "operating_hours": "09:00 - 17:00",
        "is_active": True,
        "total_beds": 2,
        "available_beds": 2,
        "icu_beds": 0,
        "available_icu_beds": 0,
        "capabilities": [
            {
                "service_name": "Primary Healthcare & NCD Screening",
                "service_category": "GENERAL_MEDICINE",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 30,
                "current_load": 12,
                "specialist_required": False,
                "diagnostic_required": False,
                "operating_hours": "09:00 - 17:00",
            },
            {
                "service_name": "Maternal & Child Health Immunization",
                "service_category": "OBSTETRICS",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 20,
                "current_load": 8,
                "specialist_required": False,
                "diagnostic_required": False,
                "operating_hours": "09:00 - 17:00",
            },
        ],
    },
    {
        "name": "Health Sub-Center - Birkera",
        "code": "FAC-OR-SNG-SC01",
        "facility_type": "SUB_CENTER",
        "tier_level": 1,
        "district": "Sundargarh",
        "state": "Odisha",
        "address_line": "Main Village Square, Birkera",
        "pincode": "769012",
        "latitude": 22.2534,
        "longitude": 84.8890,
        "contact_phone": "+916624200002",
        "operating_hours": "09:00 - 16:00",
        "is_active": True,
        "total_beds": 4,
        "available_beds": 3,
        "icu_beds": 0,
        "available_icu_beds": 0,
        "capabilities": [
            {
                "service_name": "General Outpatient & Triage",
                "service_category": "GENERAL_MEDICINE",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 25,
                "current_load": 10,
                "specialist_required": False,
                "diagnostic_required": False,
                "operating_hours": "09:00 - 16:00",
            },
            {
                "service_name": "Basic Antenatal Checkup",
                "service_category": "OBSTETRICS",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 15,
                "current_load": 5,
                "specialist_required": False,
                "diagnostic_required": False,
                "operating_hours": "09:00 - 16:00",
            },
        ],
    },
    {
        "name": "Primary Health Centre - Lathikata",
        "code": "FAC-OR-SNG-PHC01",
        "facility_type": "PHC",
        "tier_level": 2,
        "district": "Sundargarh",
        "state": "Odisha",
        "address_line": "Block HQ Road, Lathikata",
        "pincode": "770037",
        "latitude": 22.1520,
        "longitude": 84.8210,
        "contact_phone": "+916624200003",
        "operating_hours": "24x7",
        "is_active": True,
        "total_beds": 12,
        "available_beds": 7,
        "icu_beds": 0,
        "available_icu_beds": 0,
        "capabilities": [
            {
                "service_name": "General Medical Consultation & Daycare",
                "service_category": "GENERAL_MEDICINE",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 60,
                "current_load": 28,
                "specialist_required": False,
                "diagnostic_required": False,
                "operating_hours": "24x7",
            },
            {
                "service_name": "Normal Delivery & Postnatal Care",
                "service_category": "OBSTETRICS",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 15,
                "current_load": 6,
                "specialist_required": False,
                "diagnostic_required": False,
                "operating_hours": "24x7",
            },
            {
                "service_name": "Essential Diagnostic Laboratory",
                "service_category": "LABORATORY",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 50,
                "current_load": 22,
                "specialist_required": False,
                "diagnostic_required": True,
                "operating_hours": "08:00 - 20:00",
            },
            {
                "service_name": "Pediatric Outpatient & Growth Monitoring",
                "service_category": "PEDIATRICS",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 30,
                "current_load": 14,
                "specialist_required": False,
                "diagnostic_required": False,
                "operating_hours": "09:00 - 17:00",
            },
        ],
    },
    {
        "name": "Community Health Centre - Rajgangpur",
        "code": "FAC-OR-SNG-CHC01",
        "facility_type": "CHC",
        "tier_level": 3,
        "district": "Sundargarh",
        "state": "Odisha",
        "address_line": "Hospital Road, Rajgangpur",
        "pincode": "770017",
        "latitude": 22.1980,
        "longitude": 84.5860,
        "contact_phone": "+916624200004",
        "operating_hours": "24x7",
        "is_active": True,
        "total_beds": 35,
        "available_beds": 14,
        "icu_beds": 2,
        "available_icu_beds": 1,
        "capabilities": [
            {
                "service_name": "24x7 Emergency & Trauma Stabilization",
                "service_category": "EMERGENCY",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 40,
                "current_load": 15,
                "specialist_required": False,
                "diagnostic_required": False,
                "operating_hours": "24x7",
            },
            {
                "service_name": "Comprehensive Emergency Obstetric Care",
                "service_category": "OBSTETRICS",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 25,
                "current_load": 18,
                "specialist_required": True,
                "diagnostic_required": True,
                "operating_hours": "24x7",
            },
            {
                "service_name": "Digital X-Ray & Radiography",
                "service_category": "X_RAY",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 40,
                "current_load": 20,
                "specialist_required": False,
                "diagnostic_required": True,
                "operating_hours": "08:00 - 20:00",
            },
            {
                "service_name": "Dental Care & Minor Oral Procedures",
                "service_category": "DENTAL",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 20,
                "current_load": 11,
                "specialist_required": True,
                "diagnostic_required": False,
                "operating_hours": "09:00 - 16:00",
            },
            {
                "service_name": "Ophthalmic Screening & Refraction",
                "service_category": "EYE_CARE",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 25,
                "current_load": 9,
                "specialist_required": True,
                "diagnostic_required": False,
                "operating_hours": "09:00 - 15:00",
            },
        ],
    },
    {
        "name": "Sub-Divisional Rural Hospital - Panposh",
        "code": "FAC-OR-SNG-RH01",
        "facility_type": "RURAL_HOSPITAL",
        "tier_level": 4,
        "district": "Sundargarh",
        "state": "Odisha",
        "address_line": "Panposh Chowk, Rourkela Sub-division",
        "pincode": "769004",
        "latitude": 22.2350,
        "longitude": 84.8120,
        "contact_phone": "+916624200005",
        "operating_hours": "24x7",
        "is_active": True,
        "total_beds": 80,
        "available_beds": 29,
        "icu_beds": 6,
        "available_icu_beds": 2,
        "capabilities": [
            {
                "service_name": "Orthopedic Fracture Management & Casting",
                "service_category": "ORTHOPEDICS",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 35,
                "current_load": 22,
                "specialist_required": True,
                "diagnostic_required": True,
                "operating_hours": "09:00 - 18:00",
            },
            {
                "service_name": "Diagnostic Ultrasound & Doppler",
                "service_category": "ULTRASOUND",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 30,
                "current_load": 19,
                "specialist_required": True,
                "diagnostic_required": True,
                "operating_hours": "09:00 - 17:00",
            },
            {
                "service_name": "General Surgery & Minor OT",
                "service_category": "GENERAL_MEDICINE",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 20,
                "current_load": 12,
                "specialist_required": True,
                "diagnostic_required": True,
                "operating_hours": "24x7",
            },
        ],
    },
    {
        "name": "District Headquarters Hospital - Sundargarh",
        "code": "FAC-OR-SNG-DHH01",
        "facility_type": "DISTRICT_HOSPITAL",
        "tier_level": 4,
        "district": "Sundargarh",
        "state": "Odisha",
        "address_line": "Hospital Road, Sundargarh Town",
        "pincode": "770001",
        "latitude": 22.1200,
        "longitude": 84.0300,
        "contact_phone": "+916622200006",
        "operating_hours": "24x7",
        "is_active": True,
        "total_beds": 250,
        "available_beds": 82,
        "icu_beds": 24,
        "available_icu_beds": 7,
        "capabilities": [
            {
                "service_name": "Emergency Critical Care & Resuscitation",
                "service_category": "EMERGENCY",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 50,
                "current_load": 32,
                "specialist_required": True,
                "diagnostic_required": True,
                "operating_hours": "24x7",
            },
            {
                "service_name": "Multi-slice Computed Tomography (CT)",
                "service_category": "CT",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 25,
                "current_load": 14,
                "specialist_required": True,
                "diagnostic_required": True,
                "operating_hours": "24x7",
            },
            {
                "service_name": "Hemodialysis Unit",
                "service_category": "DIALYSIS",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 16,
                "current_load": 12,
                "specialist_required": True,
                "diagnostic_required": True,
                "operating_hours": "07:00 - 21:00",
            },
            {
                "service_name": "Inpatient & Outpatient Mental Health Unit",
                "service_category": "MENTAL_HEALTH",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 20,
                "current_load": 8,
                "specialist_required": True,
                "diagnostic_required": False,
                "operating_hours": "09:00 - 17:00",
            },
            {
                "service_name": "ENT Specialist Clinic & Audiometry",
                "service_category": "ENT",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 30,
                "current_load": 15,
                "specialist_required": True,
                "diagnostic_required": False,
                "operating_hours": "09:00 - 16:00",
            },
        ],
    },
    {
        "name": "Ispat Super Specialty Hospital - Rourkela",
        "code": "FAC-OR-SNG-SSH01",
        "facility_type": "SPECIALTY_HOSPITAL",
        "tier_level": 5,
        "district": "Sundargarh",
        "state": "Odisha",
        "address_line": "Sector 19, Rourkela",
        "pincode": "769005",
        "latitude": 22.2600,
        "longitude": 84.8540,
        "contact_phone": "+916612400007",
        "operating_hours": "24x7",
        "is_active": True,
        "total_beds": 400,
        "available_beds": 110,
        "icu_beds": 48,
        "available_icu_beds": 14,
        "capabilities": [
            {
                "service_name": "Cardiology & Cath Lab Interventions",
                "service_category": "CARDIOLOGY",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 40,
                "current_load": 29,
                "specialist_required": True,
                "diagnostic_required": True,
                "operating_hours": "24x7",
            },
            {
                "service_name": "Advanced Nephrology & Continuous Dialysis",
                "service_category": "DIALYSIS",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 30,
                "current_load": 22,
                "specialist_required": True,
                "diagnostic_required": True,
                "operating_hours": "24x7",
            },
            {
                "service_name": "Polytrauma & Joint Replacement Surgery",
                "service_category": "ORTHOPEDICS",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 50,
                "current_load": 34,
                "specialist_required": True,
                "diagnostic_required": True,
                "operating_hours": "24x7",
            },
            {
                "service_name": "High-Definition 128-Slice CT & MRI",
                "service_category": "CT",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 45,
                "current_load": 31,
                "specialist_required": True,
                "diagnostic_required": True,
                "operating_hours": "24x7",
            },
        ],
    },
    {
        "name": "Sundargarh Advanced Diagnostic & Imaging Centre",
        "code": "FAC-OR-SNG-DIAG01",
        "facility_type": "DIAGNOSTIC_CENTER",
        "tier_level": 4,
        "district": "Sundargarh",
        "state": "Odisha",
        "address_line": "Civil Township, Rourkela",
        "pincode": "769004",
        "latitude": 22.2420,
        "longitude": 84.8620,
        "contact_phone": "+916612400008",
        "operating_hours": "07:00 - 22:00",
        "is_active": True,
        "total_beds": 0,
        "available_beds": 0,
        "icu_beds": 0,
        "available_icu_beds": 0,
        "capabilities": [
            {
                "service_name": "Fully Automated Pathology & Biochemistry",
                "service_category": "LABORATORY",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 150,
                "current_load": 68,
                "specialist_required": False,
                "diagnostic_required": True,
                "operating_hours": "07:00 - 22:00",
            },
            {
                "service_name": "High-Resolution Diagnostic Ultrasound",
                "service_category": "ULTRASOUND",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 50,
                "current_load": 26,
                "specialist_required": True,
                "diagnostic_required": True,
                "operating_hours": "08:00 - 20:00",
            },
            {
                "service_name": "High-Resolution Digital X-Ray",
                "service_category": "X_RAY",
                "available": True,
                "availability_status": "AVAILABLE",
                "capacity": 80,
                "current_load": 35,
                "specialist_required": False,
                "diagnostic_required": True,
                "operating_hours": "07:00 - 22:00",
            },
        ],
    },
]


def seed_facilities(db: Session) -> dict:
    """Seed synthetic healthcare facilities and their respective capabilities."""
    import uuid
    facilities_created = 0
    capabilities_created = 0

    for fac_data in SAMPLE_FACILITIES:
        existing = db.query(Facility).filter(Facility.code == fac_data["code"]).first()
        if not existing:
            facility = Facility(
                id=uuid.uuid4(),
                name=fac_data["name"],
                code=fac_data["code"],
                facility_type=fac_data["facility_type"],
                tier_level=fac_data["tier_level"],
                district=fac_data["district"],
                state=fac_data["state"],
                address_line=fac_data["address_line"],
                pincode=fac_data["pincode"],
                latitude=fac_data["latitude"],
                longitude=fac_data["longitude"],
                contact_phone=fac_data["contact_phone"],
                operating_hours=fac_data["operating_hours"],
                is_active=fac_data["is_active"],
                total_beds=fac_data["total_beds"],
                available_beds=fac_data["available_beds"],
                icu_beds=fac_data["icu_beds"],
                available_icu_beds=fac_data["available_icu_beds"],
                operational_status="OPERATIONAL" if fac_data["is_active"] else "INACTIVE",
            )
            db.add(facility)
            db.flush()
            facilities_created += 1

            for cap_data in fac_data.get("capabilities", []):
                capability = FacilityCapability(
                    id=uuid.uuid4(),
                    facility_id=facility.id,
                    service_name=cap_data["service_name"],
                    service_category=cap_data["service_category"],
                    available=cap_data["available"],
                    availability_status=cap_data["availability_status"],
                    capacity=cap_data["capacity"],
                    current_load=cap_data["current_load"],
                    specialist_required=cap_data["specialist_required"],
                    diagnostic_required=cap_data["diagnostic_required"],
                    operating_hours=cap_data["operating_hours"],
                )
                db.add(capability)
                capabilities_created += 1

    db.commit()
    return {"facilities_seeded": facilities_created, "capabilities_seeded": capabilities_created}


def run_seeds(db: Session) -> dict:
    """Master seeding entry point for roles, users, villages, demo patients, care requests, and facilities."""
    roles_seeded = seed_roles(db)
    users_seeded = seed_dev_users(db)
    villages_seeded = seed_villages(db)
    patients_seeded = seed_synthetic_patients(db)
    care_requests_seeded = seed_synthetic_care_requests(db)
    fac_result = seed_facilities(db)

    logger.info(
        f"Seeding completed. Roles: {roles_seeded}, Users: {users_seeded}, "
        f"Villages: {villages_seeded}, Patients: {patients_seeded}, "
        f"Care Requests: {care_requests_seeded}, "
        f"Facilities: {fac_result['facilities_seeded']}, "
        f"Capabilities: {fac_result['capabilities_seeded']}"
    )
    return {
        "status": "success",
        "roles_seeded": roles_seeded,
        "users_seeded": users_seeded,
        "villages_seeded": villages_seeded,
        "patients_seeded": patients_seeded,
        "care_requests_seeded": care_requests_seeded,
        "facilities_seeded": fac_result["facilities_seeded"],
        "capabilities_seeded": fac_result["capabilities_seeded"],
    }

