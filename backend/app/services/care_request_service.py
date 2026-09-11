"""Care Request Management service layer."""
import uuid
import math
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.care_request import CareRequest
from app.models.patient import Patient
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.care_request import (
    CareRequestCreate,
    CareRequestUpdate,
    CareRequestResponse,
    CareRequestListResponse,
    PatientCareRequestSummary,
    CreatorSummary,
)
from app.schemas.patient import VillageSummary


class CareRequestService:
    """Handles business logic, code generation, authorization validation, and audit trails for Care Requests."""

    @staticmethod
    def generate_request_number(db: Session) -> str:
        """Generate a unique human-readable Care Request code (e.g. CR-RAHAT-000001)."""
        count = db.query(func.count(CareRequest.id)).scalar() or 0
        sequence = count + 1

        while True:
            candidate = f"CR-RAHAT-{sequence:06d}"
            exists = db.query(CareRequest.id).filter(CareRequest.request_number == candidate).first()
            if not exists:
                return candidate
            sequence += 1

    @classmethod
    def _format_care_request_response(cls, care_req: CareRequest) -> CareRequestResponse:
        """Format a CareRequest model into a comprehensive response schema."""
        patient_summary = None
        if care_req.patient:
            village_summary = None
            if care_req.patient.village:
                village_summary = VillageSummary(
                    id=care_req.patient.village.id,
                    name=care_req.patient.village.name,
                    district=care_req.patient.village.district,
                    state=care_req.patient.village.state,
                    pincode=care_req.patient.village.pincode,
                )
            patient_summary = PatientCareRequestSummary(
                id=care_req.patient.id,
                patient_code=care_req.patient.anonymous_patient_code,
                full_name=care_req.patient.full_name,
                age=care_req.patient.age,
                gender=care_req.patient.gender,
                phone=care_req.patient.phone,
                village=village_summary,
            )

        creator_summary = None
        if care_req.created_by_user:
            role_name = care_req.created_by_user.role.name if care_req.created_by_user.role else "USER"
            creator_summary = CreatorSummary(
                id=care_req.created_by_user.id,
                full_name=care_req.created_by_user.full_name,
                phone=care_req.created_by_user.phone,
                role=role_name,
            )

        return CareRequestResponse(
            id=care_req.id,
            request_number=care_req.request_number,
            patient_id=care_req.patient_id,
            patient=patient_summary,
            created_by=care_req.created_by_user_id,
            creator=creator_summary,
            care_category=care_req.care_category or "GENERAL_MEDICINE",
            required_service=care_req.required_service or "General Medicine",
            urgency=care_req.urgency_level,
            symptoms_summary=care_req.chief_complaint,
            diagnostic_requirements=care_req.diagnostic_requirements or [],
            specialist_required=care_req.specialist_required or False,
            status=care_req.status,
            notes=care_req.notes,
            created_at=care_req.created_at,
            updated_at=care_req.updated_at,
        )

    @classmethod
    def create_care_request(
        cls,
        db: Session,
        request_in: CareRequestCreate,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> CareRequestResponse:
        """Create a care request for an existing patient."""
        patient = db.query(Patient).filter(Patient.id == request_in.patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {request_in.patient_id} does not exist.",
            )

        request_number = cls.generate_request_number(db)

        care_req = CareRequest(
            id=uuid.uuid4(),
            request_number=request_number,
            patient_id=patient.id,
            village_id=patient.village_id,
            created_by_user_id=current_user.id,
            care_category=request_in.care_category.value,
            required_service=request_in.required_service.strip(),
            urgency_level=request_in.urgency.value,
            chief_complaint=request_in.symptoms_summary.strip(),
            diagnostic_requirements=request_in.diagnostic_requirements,
            specialist_required=request_in.specialist_required,
            notes=request_in.notes.strip() if request_in.notes else None,
            status="SUBMITTED",
        )

        db.add(care_req)
        db.commit()
        db.refresh(care_req)

        # Audit Log Entry
        audit = AuditLog(
            user_id=current_user.id,
            action="CARE_REQUEST_CREATED",
            entity_type="CareRequest",
            entity_id=str(care_req.id),
            details={
                "request_number": care_req.request_number,
                "patient_id": str(care_req.patient_id),
                "care_category": care_req.care_category,
                "urgency": care_req.urgency_level,
                "specialist_required": care_req.specialist_required,
            },
            ip_address=client_ip,
        )
        db.add(audit)
        db.commit()

        return cls._format_care_request_response(care_req)

    @classmethod
    def get_care_request_by_id(
        cls,
        db: Session,
        care_request_id: uuid.UUID,
    ) -> CareRequestResponse:
        """Retrieve a specific care request by UUID."""
        care_req = db.query(CareRequest).filter(CareRequest.id == care_request_id).first()
        if not care_req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Care Request with ID {care_request_id} not found.",
            )
        return cls._format_care_request_response(care_req)

    @classmethod
    def list_care_requests(
        cls,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        patient_id: Optional[uuid.UUID] = None,
        urgency: Optional[str] = None,
        care_category: Optional[str] = None,
        required_service: Optional[str] = None,
        search: Optional[str] = None,
    ) -> CareRequestListResponse:
        """List care requests with pagination, status filters, and multi-field search."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:
            page_size = 100

        query = db.query(CareRequest).join(Patient, CareRequest.patient_id == Patient.id)

        if patient_id:
            query = query.filter(CareRequest.patient_id == patient_id)

        if urgency:
            query = query.filter(CareRequest.urgency_level == urgency.upper())

        if care_category:
            query = query.filter(CareRequest.care_category == care_category.upper())

        if required_service:
            query = query.filter(CareRequest.required_service.ilike(f"%{required_service.strip()}%"))

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    CareRequest.request_number.ilike(term),
                    CareRequest.chief_complaint.ilike(term),
                    CareRequest.required_service.ilike(term),
                    Patient.full_name.ilike(term),
                    Patient.anonymous_patient_code.ilike(term),
                )
            )

        total = query.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        items = (
            query.order_by(CareRequest.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        formatted_items = [cls._format_care_request_response(req) for req in items]

        return CareRequestListResponse(
            items=formatted_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @classmethod
    def update_care_request(
        cls,
        db: Session,
        care_request_id: uuid.UUID,
        update_in: CareRequestUpdate,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> CareRequestResponse:
        """Update permitted clinical and service fields of a care request."""
        care_req = db.query(CareRequest).filter(CareRequest.id == care_request_id).first()
        if not care_req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Care Request with ID {care_request_id} not found.",
            )

        modified_fields: List[str] = []

        if update_in.care_category is not None:
            care_req.care_category = update_in.care_category.value
            modified_fields.append("care_category")

        if update_in.required_service is not None:
            care_req.required_service = update_in.required_service.strip()
            modified_fields.append("required_service")

        if update_in.urgency is not None:
            care_req.urgency_level = update_in.urgency.value
            modified_fields.append("urgency")

        if update_in.symptoms_summary is not None:
            care_req.chief_complaint = update_in.symptoms_summary.strip()
            modified_fields.append("symptoms_summary")

        if update_in.diagnostic_requirements is not None:
            care_req.diagnostic_requirements = update_in.diagnostic_requirements
            modified_fields.append("diagnostic_requirements")

        if update_in.specialist_required is not None:
            care_req.specialist_required = update_in.specialist_required
            modified_fields.append("specialist_required")

        if update_in.notes is not None:
            care_req.notes = update_in.notes.strip() if update_in.notes else None
            modified_fields.append("notes")

        db.commit()
        db.refresh(care_req)

        # Audit Log Entry
        if modified_fields:
            audit = AuditLog(
                user_id=current_user.id,
                action="CARE_REQUEST_UPDATED",
                entity_type="CareRequest",
                entity_id=str(care_req.id),
                details={
                    "request_number": care_req.request_number,
                    "modified_fields": modified_fields,
                },
                ip_address=client_ip,
            )
            db.add(audit)
            db.commit()

        return cls._format_care_request_response(care_req)
