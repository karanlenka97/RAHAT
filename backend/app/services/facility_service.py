"""Facility & Capability Management service layer with geospatial calculations and audit logging."""
import uuid
import math
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.facility import Facility, FacilityCapability
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.facility import (
    FacilityCreate,
    FacilityUpdate,
    FacilityResponse,
    FacilityListResponse,
    FacilityCapabilityCreate,
    FacilityCapabilityUpdate,
    FacilityCapabilityResponse,
    NearbyFacilityItem,
    NearbyFacilitiesResponse,
)


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Great-Circle distance between two points on Earth in kilometers."""
    r = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 2)


class FacilityService:
    """Handles facility management, capability cataloging, geospatial proximity, and audit logging."""

    @classmethod
    def _format_capability_response(cls, cap: FacilityCapability) -> FacilityCapabilityResponse:
        """Format a FacilityCapability into response schema."""
        return FacilityCapabilityResponse(
            id=cap.id,
            facility_id=cap.facility_id,
            service_name=cap.service_name or cap.name,
            service_category=cap.service_category or cap.capability_type,
            available=cap.available if cap.available is not None else True,
            availability_status=cap.availability_status or cap.current_status,
            capacity=cap.capacity or 50,
            current_load=cap.current_load or 0,
            specialist_required=cap.specialist_required or False,
            diagnostic_required=cap.diagnostic_required or False,
            operating_hours=cap.operating_hours or "24x7",
            created_at=cap.created_at,
            updated_at=cap.updated_at,
        )

    @classmethod
    def _format_facility_response(cls, fac: Facility) -> FacilityResponse:
        """Format a Facility model into comprehensive response schema."""
        capabilities = [
            cls._format_capability_response(cap) for cap in (fac.capabilities or [])
        ]

        return FacilityResponse(
            id=fac.id,
            name=fac.name,
            code=fac.code,
            facility_type=fac.facility_type,
            tier_level=fac.tier_level,
            district=fac.district,
            state=fac.state,
            address=fac.address_line or fac.address,
            pincode=fac.pincode,
            latitude=fac.latitude,
            longitude=fac.longitude,
            phone=fac.contact_phone or fac.phone,
            operating_hours=fac.operating_hours or "24x7",
            is_active=fac.is_active,
            total_beds=fac.total_beds or 0,
            available_beds=fac.available_beds or 0,
            icu_beds=fac.icu_beds or 0,
            available_icu_beds=fac.available_icu_beds or 0,
            capabilities=capabilities,
            created_at=fac.created_at,
            updated_at=fac.updated_at,
        )

    @classmethod
    def create_facility(
        cls,
        db: Session,
        facility_in: FacilityCreate,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> FacilityResponse:
        """Register a new healthcare facility with automatic tier classification."""
        tier_map = {
            "AAM": 1,
            "SUB_CENTER": 1,
            "PHC": 2,
            "CHC": 3,
            "RURAL_HOSPITAL": 4,
            "DISTRICT_HOSPITAL": 4,
            "DIAGNOSTIC_CENTER": 4,
            "SPECIALTY_HOSPITAL": 5,
        }
        tier_level = tier_map.get(facility_in.facility_type.value, 1)

        facility = Facility(
            id=uuid.uuid4(),
            name=facility_in.name.strip(),
            code=facility_in.code.strip() if facility_in.code else None,
            facility_type=facility_in.facility_type.value,
            tier_level=tier_level,
            district=facility_in.district.strip(),
            state=facility_in.state.strip(),
            address_line=facility_in.address.strip() if facility_in.address else None,
            pincode=facility_in.pincode.strip() if facility_in.pincode else None,
            latitude=facility_in.latitude,
            longitude=facility_in.longitude,
            contact_phone=facility_in.phone.strip() if facility_in.phone else None,
            operating_hours=facility_in.operating_hours.strip() if facility_in.operating_hours else "24x7",
            is_active=facility_in.is_active,
            total_beds=facility_in.total_beds,
            available_beds=facility_in.available_beds,
            icu_beds=facility_in.icu_beds,
            available_icu_beds=facility_in.available_icu_beds,
            operational_status="OPERATIONAL" if facility_in.is_active else "INACTIVE",
        )

        db.add(facility)
        db.commit()
        db.refresh(facility)

        # Audit Log Entry
        audit = AuditLog(
            user_id=current_user.id,
            action="FACILITY_CREATED",
            entity_type="Facility",
            entity_id=str(facility.id),
            details={
                "name": facility.name,
                "facility_type": facility.facility_type,
                "district": facility.district,
            },
            ip_address=client_ip,
        )
        db.add(audit)
        db.commit()

        return cls._format_facility_response(facility)

    @classmethod
    def get_facility_by_id(cls, db: Session, facility_id: uuid.UUID) -> FacilityResponse:
        """Retrieve facility profile by UUID."""
        fac = db.query(Facility).filter(Facility.id == facility_id).first()
        if not fac:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facility with ID {facility_id} not found.",
            )
        return cls._format_facility_response(fac)

    @classmethod
    def list_facilities(
        cls,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        facility_type: Optional[str] = None,
        district: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> FacilityListResponse:
        """List facilities with pagination and multi-criteria filtering."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:
            page_size = 100

        query = db.query(Facility)

        if facility_type:
            query = query.filter(Facility.facility_type == facility_type.upper())

        if district:
            query = query.filter(Facility.district.ilike(f"%{district.strip()}%"))

        if is_active is not None:
            query = query.filter(Facility.is_active == is_active)

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Facility.name.ilike(term),
                    Facility.code.ilike(term),
                    Facility.address_line.ilike(term),
                    Facility.district.ilike(term),
                )
            )

        total = query.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        items = (
            query.order_by(Facility.tier_level.desc(), Facility.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        formatted_items = [cls._format_facility_response(fac) for fac in items]

        return FacilityListResponse(
            items=formatted_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @classmethod
    def find_nearby_facilities(
        cls,
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 25.0,
    ) -> NearbyFacilitiesResponse:
        """Find active healthcare facilities within a geographic radius in kilometers."""
        if radius_km <= 0:
            radius_km = 25.0
        if radius_km > 200.0:
            radius_km = 200.0

        active_facilities = db.query(Facility).filter(Facility.is_active == True).all()  # noqa: E712

        nearby_items: List[NearbyFacilityItem] = []
        for fac in active_facilities:
            dist = calculate_haversine_distance(latitude, longitude, fac.latitude, fac.longitude)
            if dist <= radius_km:
                nearby_items.append(
                    NearbyFacilityItem(
                        facility=cls._format_facility_response(fac),
                        distance_km=dist,
                    )
                )

        # Sort purely by distance ascending
        nearby_items.sort(key=lambda item: item.distance_km)

        return NearbyFacilitiesResponse(
            center_latitude=latitude,
            center_longitude=longitude,
            radius_km=radius_km,
            count=len(nearby_items),
            items=nearby_items,
        )

    @classmethod
    def update_facility(
        cls,
        db: Session,
        facility_id: uuid.UUID,
        update_in: FacilityUpdate,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> FacilityResponse:
        """Update facility configuration, beds, or contact parameters."""
        fac = db.query(Facility).filter(Facility.id == facility_id).first()
        if not fac:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facility with ID {facility_id} not found.",
            )

        modified_fields: List[str] = []

        if update_in.name is not None:
            fac.name = update_in.name.strip()
            modified_fields.append("name")

        if update_in.facility_type is not None:
            fac.facility_type = update_in.facility_type.value
            tier_map = {
                "AAM": 1,
                "SUB_CENTER": 1,
                "PHC": 2,
                "CHC": 3,
                "RURAL_HOSPITAL": 4,
                "DISTRICT_HOSPITAL": 4,
                "DIAGNOSTIC_CENTER": 4,
                "SPECIALTY_HOSPITAL": 5,
            }
            fac.tier_level = tier_map.get(update_in.facility_type.value, fac.tier_level)
            modified_fields.append("facility_type")

        if update_in.district is not None:
            fac.district = update_in.district.strip()
            modified_fields.append("district")

        if update_in.state is not None:
            fac.state = update_in.state.strip()
            modified_fields.append("state")

        if update_in.address is not None:
            fac.address_line = update_in.address.strip()
            modified_fields.append("address")

        if update_in.pincode is not None:
            fac.pincode = update_in.pincode.strip()
            modified_fields.append("pincode")

        if update_in.latitude is not None:
            fac.latitude = update_in.latitude
            modified_fields.append("latitude")

        if update_in.longitude is not None:
            fac.longitude = update_in.longitude
            modified_fields.append("longitude")

        if update_in.phone is not None:
            fac.contact_phone = update_in.phone.strip()
            modified_fields.append("phone")

        if update_in.operating_hours is not None:
            fac.operating_hours = update_in.operating_hours.strip()
            modified_fields.append("operating_hours")

        if update_in.is_active is not None:
            fac.is_active = update_in.is_active
            fac.operational_status = "OPERATIONAL" if update_in.is_active else "INACTIVE"
            modified_fields.append("is_active")

        if update_in.total_beds is not None:
            fac.total_beds = update_in.total_beds
            modified_fields.append("total_beds")

        if update_in.available_beds is not None:
            fac.available_beds = update_in.available_beds
            modified_fields.append("available_beds")

        if update_in.icu_beds is not None:
            fac.icu_beds = update_in.icu_beds
            modified_fields.append("icu_beds")

        if update_in.available_icu_beds is not None:
            fac.available_icu_beds = update_in.available_icu_beds
            modified_fields.append("available_icu_beds")

        db.commit()
        db.refresh(fac)

        # Audit Log Entry
        if modified_fields:
            audit = AuditLog(
                user_id=current_user.id,
                action="FACILITY_UPDATED",
                entity_type="Facility",
                entity_id=str(fac.id),
                details={
                    "name": fac.name,
                    "modified_fields": modified_fields,
                },
                ip_address=client_ip,
            )
            db.add(audit)
            db.commit()

        return cls._format_facility_response(fac)

    # -----------------------------------------------------------------------
    # Facility Capability Sub-resources
    # -----------------------------------------------------------------------

    @classmethod
    def create_capability(
        cls,
        db: Session,
        facility_id: uuid.UUID,
        cap_in: FacilityCapabilityCreate,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> FacilityCapabilityResponse:
        """Add a specific capability/service requirement to a facility."""
        facility = db.query(Facility).filter(Facility.id == facility_id).first()
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facility with ID {facility_id} does not exist.",
            )

        capability = FacilityCapability(
            id=uuid.uuid4(),
            facility_id=facility.id,
            service_name=cap_in.service_name.strip(),
            service_category=cap_in.service_category.value,
            available=cap_in.available,
            availability_status=cap_in.availability_status.value,
            capacity=cap_in.capacity,
            current_load=cap_in.current_load,
            specialist_required=cap_in.specialist_required,
            diagnostic_required=cap_in.diagnostic_required,
            operating_hours=cap_in.operating_hours.strip() if cap_in.operating_hours else "24x7",
        )

        db.add(capability)
        db.commit()
        db.refresh(capability)

        # Audit Log
        audit = AuditLog(
            user_id=current_user.id,
            action="CAPABILITY_CREATED",
            entity_type="FacilityCapability",
            entity_id=str(capability.id),
            details={
                "facility_id": str(facility.id),
                "service_name": capability.service_name,
                "service_category": capability.service_category,
            },
            ip_address=client_ip,
        )
        db.add(audit)
        db.commit()

        return cls._format_capability_response(capability)

    @classmethod
    def list_capabilities(cls, db: Session, facility_id: uuid.UUID) -> List[FacilityCapabilityResponse]:
        """List all capabilities of a facility."""
        facility = db.query(Facility).filter(Facility.id == facility_id).first()
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facility with ID {facility_id} not found.",
            )
        caps = db.query(FacilityCapability).filter(FacilityCapability.facility_id == facility_id).all()
        return [cls._format_capability_response(c) for c in caps]

    @classmethod
    def update_capability(
        cls,
        db: Session,
        facility_id: uuid.UUID,
        capability_id: uuid.UUID,
        update_in: FacilityCapabilityUpdate,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> FacilityCapabilityResponse:
        """Update capability attributes, capacity, or availability status."""
        cap = (
            db.query(FacilityCapability)
            .filter(
                FacilityCapability.id == capability_id,
                FacilityCapability.facility_id == facility_id,
            )
            .first()
        )
        if not cap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Capability {capability_id} not found for facility {facility_id}.",
            )

        new_capacity = update_in.capacity if update_in.capacity is not None else cap.capacity
        new_load = update_in.current_load if update_in.current_load is not None else cap.current_load
        if new_capacity is not None and new_load is not None and new_capacity > 0 and new_load > new_capacity:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Current load cannot exceed capability capacity.",
            )

        modified_fields: List[str] = []

        if update_in.service_name is not None:
            cap.service_name = update_in.service_name.strip()
            modified_fields.append("service_name")

        if update_in.service_category is not None:
            cap.service_category = update_in.service_category.value
            modified_fields.append("service_category")

        if update_in.available is not None:
            cap.available = update_in.available
            modified_fields.append("available")

        if update_in.availability_status is not None:
            cap.availability_status = update_in.availability_status.value
            modified_fields.append("availability_status")

        if update_in.capacity is not None:
            cap.capacity = update_in.capacity
            modified_fields.append("capacity")

        if update_in.current_load is not None:
            cap.current_load = update_in.current_load
            modified_fields.append("current_load")

        if update_in.specialist_required is not None:
            cap.specialist_required = update_in.specialist_required
            modified_fields.append("specialist_required")

        if update_in.diagnostic_required is not None:
            cap.diagnostic_required = update_in.diagnostic_required
            modified_fields.append("diagnostic_required")

        if update_in.operating_hours is not None:
            cap.operating_hours = update_in.operating_hours.strip()
            modified_fields.append("operating_hours")

        db.commit()
        db.refresh(cap)

        # Audit Log
        if modified_fields:
            audit = AuditLog(
                user_id=current_user.id,
                action="CAPABILITY_UPDATED",
                entity_type="FacilityCapability",
                entity_id=str(cap.id),
                details={
                    "facility_id": str(facility_id),
                    "modified_fields": modified_fields,
                },
                ip_address=client_ip,
            )
            db.add(audit)
            db.commit()

        return cls._format_capability_response(cap)
