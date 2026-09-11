"""Patient management business logic, code generator, and audit logging."""
import math
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.models.patient import Patient
from app.models.village import Village
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse, VillageSummary


def generate_unique_patient_code(db: Session) -> str:
    """Generate a sequential, collision-free unique patient code (e.g. RAHAT-P-000001)."""
    count = db.query(func.count(Patient.id)).scalar() or 0
    seq = count + 1
    while True:
        candidate_code = f"RAHAT-P-{seq:06d}"
        exists = db.query(Patient.id).filter(Patient.anonymous_patient_code == candidate_code).first()
        if not exists:
            return candidate_code
        seq += 1


def create_patient(
    db: Session,
    patient_in: PatientCreate,
    current_user: User,
) -> Patient:
    """Register a new patient, generate patient code, and record audit log."""
    # Validate village if provided
    if patient_in.village_id:
        village = db.query(Village).filter(Village.id == patient_in.village_id).first()
        if not village:
            raise ValueError(f"Referenced Village with ID '{patient_in.village_id}' does not exist.")

    patient_code = generate_unique_patient_code(db)

    new_patient = Patient(
        anonymous_patient_code=patient_code,
        full_name=patient_in.full_name.strip(),
        age=patient_in.age,
        gender=patient_in.gender,
        blood_group=patient_in.blood_group,
        phone=patient_in.phone.strip() if patient_in.phone else None,
        emergency_contact_name=patient_in.emergency_contact_name.strip() if patient_in.emergency_contact_name else None,
        emergency_contact_phone=patient_in.emergency_contact_phone.strip() if patient_in.emergency_contact_phone else None,
        village_id=patient_in.village_id,
        address_line=patient_in.address.strip() if patient_in.address else None,
        chronic_conditions=patient_in.chronic_conditions or [],
        allergies=patient_in.allergies or [],
        abha_id=patient_in.abha_reference.strip() if patient_in.abha_reference else None,
    )

    db.add(new_patient)
    db.flush()

    # Record Audit Log
    audit = AuditLog(
        user_id=current_user.id,
        action="PATIENT_CREATED",
        entity_type="Patient",
        entity_id=str(new_patient.id),
        details={
            "patient_code": new_patient.anonymous_patient_code,
            "created_by_role": current_user.role.name if current_user.role else "UNKNOWN",
        },
    )
    db.add(audit)

    db.commit()
    db.refresh(new_patient)
    return new_patient


def get_patients(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
) -> Tuple[List[Patient], int, int]:
    """Retrieve paginated patient list with optional search filter."""
    page = max(1, page)
    page_size = min(100, max(1, page_size))

    query = db.query(Patient)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Patient.full_name.ilike(term),
                Patient.anonymous_patient_code.ilike(term),
                Patient.phone.ilike(term),
                Patient.abha_id.ilike(term),
            )
        )

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1

    items = (
        query.order_by(Patient.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return items, total, total_pages


def get_patient_by_id(db: Session, patient_id: uuid.UUID) -> Optional[Patient]:
    """Retrieve patient record by primary key."""
    return db.query(Patient).filter(Patient.id == patient_id).first()


def update_patient(
    db: Session,
    patient: Patient,
    update_data: PatientUpdate,
    current_user: User,
) -> Patient:
    """Update allowed demographic and clinical index fields."""
    update_dict = update_data.model_dump(exclude_unset=True)

    # Validate village if being changed
    if "village_id" in update_dict and update_dict["village_id"] is not None:
        village = db.query(Village).filter(Village.id == update_dict["village_id"]).first()
        if not village:
            raise ValueError(f"Referenced Village with ID '{update_dict['village_id']}' does not exist.")

    # Apply permitted field updates
    field_mappings = {
        "full_name": "full_name",
        "age": "age",
        "gender": "gender",
        "phone": "phone",
        "village_id": "village_id",
        "address": "address_line",
        "emergency_contact_name": "emergency_contact_name",
        "emergency_contact_phone": "emergency_contact_phone",
        "abha_reference": "abha_id",
        "blood_group": "blood_group",
        "chronic_conditions": "chronic_conditions",
        "allergies": "allergies",
    }

    modified_fields = []
    for schema_key, model_attr in field_mappings.items():
        if schema_key in update_dict:
            val = update_dict[schema_key]
            if isinstance(val, str):
                val = val.strip()
            setattr(patient, model_attr, val)
            modified_fields.append(schema_key)

    # Record Audit Log
    audit = AuditLog(
        user_id=current_user.id,
        action="PATIENT_UPDATED",
        entity_type="Patient",
        entity_id=str(patient.id),
        details={
            "patient_code": patient.anonymous_patient_code,
            "modified_fields": modified_fields,
            "updated_by_role": current_user.role.name if current_user.role else "UNKNOWN",
        },
    )
    db.add(audit)

    db.commit()
    db.refresh(patient)
    return patient


def format_patient_response(patient: Patient) -> PatientResponse:
    """Format a Patient model into a PatientResponse Pydantic schema."""
    village_summary = None
    if patient.village:
        village_summary = VillageSummary(
            id=patient.village.id,
            name=patient.village.name,
            district=patient.village.district,
            state=patient.village.state,
            pincode=patient.village.pincode,
        )

    return PatientResponse(
        id=patient.id,
        patient_code=patient.anonymous_patient_code,
        full_name=patient.full_name,
        age=patient.age,
        gender=patient.gender,
        phone=patient.phone,
        village_id=patient.village_id,
        village=village_summary,
        address=patient.address_line,
        emergency_contact_name=patient.emergency_contact_name,
        emergency_contact_phone=patient.emergency_contact_phone,
        emergency_contact=patient.emergency_contact,
        abha_reference=patient.abha_id,
        blood_group=patient.blood_group,
        chronic_conditions=patient.chronic_conditions or [],
        allergies=patient.allergies or [],
        created_at=patient.created_at,
        updated_at=patient.updated_at,
    )
