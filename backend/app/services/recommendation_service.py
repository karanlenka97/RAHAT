"""Smart Facility Recommendation Engine service layer.

Deterministic, multi-factor, explainable facility scoring and ranking for clinical care requests.
Zero AI/LLM dependency.
"""
import uuid
import math
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.care_request import CareRequest
from app.models.facility import Facility, FacilityCapability
from app.services.facility_service import calculate_haversine_distance
from app.schemas.recommendation import (
    FactorScores,
    FacilityRecommendationItem,
    RecommendationResponse,
)

# Centralized Deterministic Scoring Weights (Total = 1.00 / 100%)
SERVICE_MATCH_WEIGHT = 0.30
DISTANCE_WEIGHT = 0.20
DIAGNOSTIC_MATCH_WEIGHT = 0.20
SPECIALIST_MATCH_WEIGHT = 0.15
AVAILABILITY_WEIGHT = 0.10
WORKLOAD_WEIGHT = 0.05

# Healthcare Service Domain & Synonym Mapping for Deterministic Matching
SERVICE_DOMAIN_MAP: Dict[str, List[str]] = {
    "CARDIOLOGY": ["cardiology", "cardiac", "heart", "cath lab", "ecg", "troponin", "echo", "echocardiogram"],
    "OBSTETRICS": ["obstetrics", "gynecology", "maternal", "anc", "delivery", "antenatal", "mch", "postnatal", "obstetric", "obstetric ultrasound"],
    "PEDIATRICS": ["pediatrics", "pediatric", "child health", "neonatal", "growth monitoring", "child", "spirometry"],
    "ORTHOPEDICS": ["orthopedics", "orthopedic", "fracture", "bone", "joint", "casting", "polytrauma"],
    "GENERAL_MEDICINE": ["general medicine", "medicine", "internal medicine", "outpatient", "triage", "daycare", "ncd", "primary health", "general", "surgery"],
    "EMERGENCY": ["emergency", "trauma", "casualty", "resuscitation", "critical care"],
    "EYE_CARE": ["eye", "ophthalmology", "ophthalmic", "vision", "refraction", "cataract", "slit lamp", "intraocular", "visual acuity"],
    "ENT": ["ent", "ear", "nose", "throat", "audiometry"],
    "DENTAL": ["dental", "oral", "teeth"],
    "DIALYSIS": ["dialysis", "hemodialysis", "nephrology", "kidney"],
    "MENTAL_HEALTH": ["mental health", "psychiatry", "psychiatric"],
    "LABORATORY": ["laboratory", "pathology", "biochemistry", "blood", "cbc", "urine", "sugar", "glucose", "lipid", "creatinine", "hba1c", "fbs"],
    "X_RAY": ["x-ray", "xray", "radiography", "radiology", "chest x-ray", "digital x-ray"],
    "ULTRASOUND": ["ultrasound", "sonography", "usg", "doppler", "abdominal ultrasound", "obstetric ultrasound"],
    "CT": ["ct", "computed tomography", "ct scan", "128-slice", "mri"],
}

DIAGNOSTIC_KEYWORD_MAP = SERVICE_DOMAIN_MAP

# Care Category to Service Category Mapping
CARE_CATEGORY_TO_DOMAIN_MAP: Dict[str, List[str]] = {
    "GENERAL_MEDICINE": ["GENERAL_MEDICINE"],
    "MATERNAL_HEALTH": ["OBSTETRICS"],
    "CHILD_HEALTH": ["PEDIATRICS"],
    "EMERGENCY": ["EMERGENCY", "CARDIOLOGY"],
    "NCD": ["GENERAL_MEDICINE", "CARDIOLOGY", "DIALYSIS"],
    "MENTAL_HEALTH": ["MENTAL_HEALTH"],
    "EYE_CARE": ["EYE_CARE"],
    "ENT": ["ENT"],
    "DENTAL": ["DENTAL"],
    "DIAGNOSTIC": ["LABORATORY", "X_RAY", "ULTRASOUND", "CT"],
    "OTHER": ["OTHER", "GENERAL_MEDICINE"],
}


class RecommendationEngineService:
    """Smart Facility Recommendation Engine evaluating active health centers for Care Requests."""

    @classmethod
    def _normalize_str(cls, text: Optional[str]) -> str:
        """Clean and normalize string for substring comparison."""
        if not text:
            return ""
        return "".join(c.lower() for c in text if c.isalnum() or c.isspace()).strip()

    @classmethod
    def _normalize_tokens(cls, text: Optional[str]) -> List[str]:
        """Tokenize and clean string for deterministic token matching."""
        if not text:
            return []
        cleaned = "".join(c.lower() if c.isalnum() else " " for c in text)
        return [t for t in cleaned.split() if len(t) > 1]

    @classmethod
    def _calculate_service_match(
        cls,
        care_request: CareRequest,
        capabilities: List[FacilityCapability],
    ) -> Tuple[float, List[FacilityCapability], List[str]]:
        """Calculate Service Match score (0.0 to 100.0) based on required service & care category."""
        req_service_raw = care_request.required_service or ""
        req_service_tokens = cls._normalize_tokens(req_service_raw)
        req_category = (care_request.care_category or "").upper()

        matching_caps: List[FacilityCapability] = []
        matched_service_names: List[str] = []
        best_score = 0.0

        # Determine target domains from required_service
        target_domains: List[str] = []
        if req_service_tokens:
            for domain, keywords in SERVICE_DOMAIN_MAP.items():
                if any(any(kw in tok or tok in kw for kw in keywords) for tok in req_service_tokens):
                    target_domains.append(domain)

        # Fallback target domains from care_category if no specific service domain was resolved
        if not target_domains and req_category in CARE_CATEGORY_TO_DOMAIN_MAP:
            target_domains = CARE_CATEGORY_TO_DOMAIN_MAP[req_category]

        for cap in capabilities:
            if not cap.available or (cap.availability_status or "").upper() == "UNAVAILABLE":
                continue

            cap_cat = (cap.service_category or cap.capability_type or "").upper()
            cap_name_tokens = cls._normalize_tokens(cap.service_name or cap.name or "")

            matched = False
            score = 0.0

            # 1. Direct match on resolved service domain or exact category
            if cap_cat in target_domains:
                score = 100.0
                matched = True
            # 2. Token overlap between requested service and capability name
            elif req_service_tokens and any(t in cap_name_tokens for t in req_service_tokens):
                score = 100.0
                matched = True
            # 3. Broader care_category match
            elif req_category and cap_cat in CARE_CATEGORY_TO_DOMAIN_MAP.get(req_category, []):
                # If specific required_service was given and has target domains, only grant category score if target domains match
                if not req_service_tokens or not target_domains or cap_cat in target_domains:
                    score = 85.0
                    matched = True

            if matched:
                matching_caps.append(cap)
                service_title = cap.service_name or cap.name
                if service_title and service_title not in matched_service_names:
                    matched_service_names.append(service_title)
                if score > best_score:
                    best_score = score

        return best_score, matching_caps, matched_service_names

    @classmethod
    def _calculate_distance_score(
        cls,
        care_request: CareRequest,
        facility: Facility,
    ) -> Tuple[float, Optional[float]]:
        """Calculate distance in km and normalized score (0.0 to 100.0)."""
        # Resolve patient / origin coordinates
        origin_lat = None
        origin_lon = None

        if care_request.village and care_request.village.latitude is not None:
            origin_lat = care_request.village.latitude
            origin_lon = care_request.village.longitude
        elif care_request.patient and care_request.patient.village and care_request.patient.village.latitude is not None:
            origin_lat = care_request.patient.village.latitude
            origin_lon = care_request.patient.village.longitude
        elif care_request.origin_facility and care_request.origin_facility.latitude is not None:
            origin_lat = care_request.origin_facility.latitude
            origin_lon = care_request.origin_facility.longitude

        if origin_lat is None or origin_lon is None or facility.latitude is None or facility.longitude is None:
            # Fallback neutral distance score if coordinates are missing
            return 50.0, None

        dist_km = calculate_haversine_distance(origin_lat, origin_lon, facility.latitude, facility.longitude)

        # Deterministic Distance Decay: Closer facilities score higher
        if dist_km <= 5.0:
            score = 100.0 - (dist_km * 1.0)
        elif dist_km <= 50.0:
            score = max(20.0, 95.0 - ((dist_km - 5.0) * 1.5))
        else:
            score = max(0.0, 20.0 - ((dist_km - 50.0) * 0.4))

        return round(max(0.0, min(100.0, score)), 2), dist_km

    @classmethod
    def _calculate_diagnostic_match(
        cls,
        care_request: CareRequest,
        capabilities: List[FacilityCapability],
    ) -> Tuple[float, List[str]]:
        """Calculate Diagnostic Match score (0.0 to 100.0) based on required tests and equipment."""
        diag_reqs = care_request.diagnostic_requirements or []
        if isinstance(diag_reqs, str):
            diag_reqs = [diag_reqs]

        if not diag_reqs:
            # Neutral / full score when no diagnostics are requested
            return 100.0, []

        available_diags: List[str] = []
        matched_count = 0

        for req in diag_reqs:
            req_norm = cls._normalize_str(req)
            req_matched = False

            for cap in capabilities:
                if not cap.available or (cap.availability_status or "").upper() == "UNAVAILABLE":
                    continue

                cap_name = cls._normalize_str(cap.service_name or cap.name)
                cap_cat = (cap.service_category or cap.capability_type or "").upper()

                # Check if capability name matches diagnostic requirement
                if req_norm in cap_name or cap_name in req_norm:
                    req_matched = True
                    if cap.service_name not in available_diags:
                        available_diags.append(cap.service_name or cap.name)
                    break

                # Check keyword mapping for diagnostic categories
                keywords = DIAGNOSTIC_KEYWORD_MAP.get(cap_cat, [])
                if any(kw in req_norm for kw in keywords):
                    req_matched = True
                    if cap.service_name not in available_diags:
                        available_diags.append(cap.service_name or cap.name)
                    break

            if req_matched:
                matched_count += 1

        score = (matched_count / len(diag_reqs)) * 100.0 if diag_reqs else 100.0
        return round(max(0.0, min(100.0, score)), 2), available_diags

    @classmethod
    def _calculate_specialist_match(
        cls,
        care_request: CareRequest,
        matching_caps: List[FacilityCapability],
        facility: Facility,
    ) -> Tuple[float, bool]:
        """Calculate Specialist Match score (0.0 to 100.0)."""
        if not care_request.specialist_required:
            # Full score when specialist is not required
            return 100.0, False

        # If a specialist is required, check if any matching capability has specialist_required == True
        specialist_available = False
        for cap in matching_caps:
            if cap.specialist_required and cap.available:
                specialist_available = True
                break

        if specialist_available:
            return 100.0, True

        # Tier 4 (District Hospital / Rural Hospital) and Tier 5 (Specialty Hospital) have full medical specialist staff
        if facility.tier_level >= 4:
            return 75.0, True
        elif facility.tier_level == 3:  # CHC with visiting specialists
            return 40.0, False
        else:  # PHC / AAM / Sub-Center
            return 0.0, False

    @classmethod
    def _calculate_availability_score(
        cls,
        matching_caps: List[FacilityCapability],
    ) -> Tuple[float, str]:
        """Calculate Availability Score (0.0 to 100.0) based on capability operational status."""
        if not matching_caps:
            return 0.0, "UNAVAILABLE"

        status_weights = {
            "AVAILABLE": 100.0,
            "LIMITED": 60.0,
            "HIGH_LOAD": 30.0,
            "UNAVAILABLE": 0.0,
        }

        best_score = 0.0
        best_status = "UNAVAILABLE"

        for cap in matching_caps:
            st = (cap.availability_status or cap.current_status or "AVAILABLE").upper()
            score = status_weights.get(st, 50.0)
            if score > best_score:
                best_score = score
                best_status = st

        return best_score, best_status

    @classmethod
    def _calculate_workload_score(
        cls,
        matching_caps: List[FacilityCapability],
    ) -> Tuple[float, int, int]:
        """Calculate Workload score (0.0 to 100.0) where lower utilization yields higher scores."""
        if not matching_caps:
            return 50.0, 0, 0

        # Choose the matching capability with the best capacity headroom
        best_score = 50.0
        selected_capacity = 0
        selected_load = 0

        for cap in matching_caps:
            cap_val = cap.capacity or 0
            load_val = cap.current_load or 0

            if cap_val <= 0:
                score = 50.0
            elif load_val >= cap_val:
                score = 0.0
            else:
                utilization = load_val / cap_val
                score = (1.0 - utilization) * 100.0

            if score >= best_score:
                best_score = score
                selected_capacity = cap_val
                selected_load = load_val

        return round(max(0.0, min(100.0, best_score)), 2), selected_capacity, selected_load

    @classmethod
    def _generate_explanation(
        cls,
        facility: Facility,
        care_request: CareRequest,
        factors: FactorScores,
        distance_km: Optional[float],
        matched_services: List[str],
        specialist_available: bool,
        availability_status: str,
        capacity: int,
        current_load: int,
    ) -> str:
        """Generate a transparent, deterministic explanation string from score factors."""
        service_label = matched_services[0] if matched_services else (care_request.required_service or "required")
        dist_str = f"located {distance_km:.1f} km away" if distance_km is not None else "in network"

        # Diagnostic statement
        if care_request.diagnostic_requirements:
            if factors.diagnostic_match >= 100.0:
                diag_str = "provides all required diagnostic investigations"
            elif factors.diagnostic_match > 0.0:
                diag_str = "provides partial diagnostic investigations"
            else:
                diag_str = "lacks the requested diagnostic testing"
        else:
            diag_str = "requires no additional diagnostic facilities"

        # Specialist statement
        if care_request.specialist_required:
            spec_str = "has certified specialist doctor availability" if specialist_available else "has limited specialist coverage"
        else:
            spec_str = "meets routine clinical requirements"

        # Capacity utilization percentage
        if capacity > 0:
            free_pct = max(0, int(((capacity - current_load) / capacity) * 100))
            load_str = f"{free_pct}% available capacity"
        else:
            load_str = "routine admission capacity"

        return (
            f"Recommended because {facility.name} ({facility.facility_type}) offers {service_label}, "
            f"is {dist_str}, {diag_str}, {spec_str}, and operates with {load_str} ({availability_status})."
        )

    @classmethod
    def get_recommendations_for_care_request(
        cls,
        db: Session,
        care_request_id: uuid.UUID,
        limit: int = 5,
    ) -> RecommendationResponse:
        """Generate ranked healthcare facility recommendations for a specific Care Request."""
        if limit < 1:
            limit = 5
        if limit > 20:
            limit = 20

        care_req = db.query(CareRequest).filter(CareRequest.id == care_request_id).first()
        if not care_req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Care Request with ID {care_request_id} not found.",
            )

        # Hard Filter 1: Retrieve only active facilities
        active_facilities = db.query(Facility).filter(Facility.is_active == True).all()  # noqa: E712

        candidates: List[FacilityRecommendationItem] = []

        for fac in active_facilities:
            capabilities = fac.capabilities or []

            # Factor 1 & Hard Filter 2: Service Match
            service_score, matching_caps, matched_services = cls._calculate_service_match(care_req, capabilities)
            if service_score <= 0.0 or not matching_caps:
                # Hard filter: Facility cannot provide the required service
                continue

            # Factor 2: Distance Score
            dist_score, dist_km = cls._calculate_distance_score(care_req, fac)

            # Factor 3: Diagnostic Match
            diag_score, diag_available = cls._calculate_diagnostic_match(care_req, capabilities)

            # Factor 4: Specialist Match
            spec_score, spec_available = cls._calculate_specialist_match(care_req, matching_caps, fac)

            # Factor 5: Availability Status
            avail_score, avail_status = cls._calculate_availability_score(matching_caps)

            # Factor 6: Workload Score
            workload_score, cap_val, load_val = cls._calculate_workload_score(matching_caps)

            # Weighted Overall Score Calculation
            overall_score = (
                (service_score * SERVICE_MATCH_WEIGHT)
                + (dist_score * DISTANCE_WEIGHT)
                + (diag_score * DIAGNOSTIC_MATCH_WEIGHT)
                + (spec_score * SPECIALIST_MATCH_WEIGHT)
                + (avail_score * AVAILABILITY_WEIGHT)
                + (workload_score * WORKLOAD_WEIGHT)
            )
            overall_score = round(max(0.0, min(100.0, overall_score)), 2)

            factors = FactorScores(
                service_match=service_score,
                distance=dist_score,
                diagnostic_match=diag_score,
                specialist_match=spec_score,
                availability=avail_score,
                workload=workload_score,
            )

            explanation = cls._generate_explanation(
                facility=fac,
                care_request=care_req,
                factors=factors,
                distance_km=dist_km,
                matched_services=matched_services,
                specialist_available=spec_available,
                availability_status=avail_status,
                capacity=cap_val,
                current_load=load_val,
            )

            candidates.append(
                FacilityRecommendationItem(
                    facility_id=fac.id,
                    facility_name=fac.name,
                    facility_code=fac.code,
                    facility_type=fac.facility_type,
                    tier_level=fac.tier_level,
                    district=fac.district,
                    state=fac.state,
                    address=fac.address_line or fac.address,
                    phone=fac.contact_phone or fac.phone,
                    distance_km=dist_km,
                    overall_score=overall_score,
                    factors=factors,
                    matched_services=matched_services,
                    availability_status=avail_status,
                    specialist_available=spec_available,
                    diagnostics_available=diag_available,
                    capacity=cap_val,
                    current_load=load_val,
                    explanation=explanation,
                )
            )

        # Deterministic Ranking: Overall score DESC, then distance_km ASC (None treated as infinity)
        candidates.sort(
            key=lambda item: (-item.overall_score, item.distance_km if item.distance_km is not None else float("inf"))
        )

        top_recommendations = candidates[:limit]

        patient_name = care_req.patient.full_name if care_req.patient else "Registered Citizen"

        return RecommendationResponse(
            care_request_id=care_req.id,
            patient_id=care_req.patient_id,
            patient_name=patient_name,
            care_category=care_req.care_category,
            required_service=care_req.required_service,
            urgency=care_req.urgency_level or "LOW",
            diagnostic_requirements=care_req.diagnostic_requirements or [],
            specialist_required=care_req.specialist_required or False,
            total_candidates=len(candidates),
            recommendations=top_recommendations,
            generated_at=datetime.now(timezone.utc),
        )
