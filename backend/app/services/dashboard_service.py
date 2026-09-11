"""Dashboard Service Layer for High-Performance Operational Analytics and Reporting."""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import func, or_, and_, case, distinct
from sqlalchemy.orm import Session, joinedload

from app.models.user import User
from app.models.patient import Patient
from app.models.village import Village
from app.models.facility import Facility, FacilityCapability
from app.models.care_request import CareRequest
from app.models.referral import Referral, ReferralEvent
from app.schemas.dashboard import (
    FrontlineActionItem,
    FrontlineRecentActivity,
    FrontlineDashboardResponse,
    FacilityCapabilityMetric,
    FacilityReferralQueueItem,
    FacilityStatusBreakdown,
    FacilityDashboardResponse,
    FacilityPerformanceSummary,
    DistrictDashboardResponse,
    FunnelStageItem,
    ReferralFunnelResponse,
    CareCompletionByGroup,
    CareCompletionResponse,
)


def _get_time_cutoff(time_range: str) -> Optional[datetime]:
    """Parse time range string and return UTC datetime cutoff or None for 'all'."""
    now = datetime.now(timezone.utc)
    if time_range == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == "7d":
        return now - timedelta(days=7)
    elif time_range == "30d":
        return now - timedelta(days=30)
    return None


class DashboardService:
    """Consolidated operational aggregation engine for Frontline, Facility, and District tiers."""

    @staticmethod
    def get_frontline_dashboard(db: Session, current_user: User) -> FrontlineDashboardResponse:
        """Aggregate operational queue and clinical metrics for frontline community workers."""
        user_role = current_user.role.name if current_user.role else "ASHA"
        is_global = user_role in ("ADMIN", "MEDICAL_OFFICER")

        # 1. Total Accessible Patients
        patient_query = db.query(func.count(Patient.id))
        if not is_global and current_user.facility_id:
            # Patients in villages served by the user's facility or created by user
            patient_query = patient_query.outerjoin(Village, Patient.village_id == Village.id).filter(
                or_(
                    Village.assigned_phc_facility_id == current_user.facility_id,
                    Patient.care_requests.any(CareRequest.created_by_user_id == current_user.id),
                )
            )
        total_patients = patient_query.scalar() or 0

        # 2. Care Requests Summary
        cr_base = db.query(CareRequest)
        if not is_global:
            cr_base = cr_base.filter(
                or_(
                    CareRequest.created_by_user_id == current_user.id,
                    CareRequest.origin_facility_id == current_user.facility_id,
                )
            )

        active_cr_count = cr_base.filter(CareRequest.status.in_(["SUBMITTED", "TRIAGED"])).count()
        urgent_cr_count = cr_base.filter(
            CareRequest.urgency_level.in_(["HIGH", "EMERGENCY"]),
            CareRequest.status.in_(["SUBMITTED", "TRIAGED", "REFERRED"]),
        ).count()

        # 3. Referral Metrics
        ref_base = db.query(Referral)
        if not is_global:
            ref_base = ref_base.filter(
                or_(
                    Referral.referred_by_user_id == current_user.id,
                    Referral.origin_facility_id == current_user.facility_id,
                )
            )

        pending_referrals_count = ref_base.filter(Referral.status == "PENDING_ACCEPTANCE").count()
        in_transit_referrals_count = ref_base.filter(Referral.status == "DEPARTED").count()
        completed_referrals_count = ref_base.filter(Referral.status.in_(["COMPLETED", "BACK_REFERRED"])).count()

        # 4. Frontline Action Queue
        # Identify care requests and referrals needing action
        action_items: List[FrontlineActionItem] = []
        now = datetime.now(timezone.utc)

        # 4a. Care requests needing referral creation / triage
        actionable_crs = (
            cr_base.options(
                joinedload(CareRequest.patient),
                joinedload(CareRequest.village),
            )
            .filter(CareRequest.status.in_(["SUBMITTED", "TRIAGED"]))
            .order_by(CareRequest.created_at.desc())
            .limit(50)
            .all()
        )

        for cr in actionable_crs:
            created_ts = cr.created_at if cr.created_at.tzinfo else cr.created_at.replace(tzinfo=timezone.utc)
            elapsed = (now - created_ts).total_seconds() / 3600.0
            p_name = cr.patient.full_name if cr.patient else "Unknown Patient"
            p_code = cr.patient.anonymous_patient_code if cr.patient else "N/A"
            v_name = cr.village.name if cr.village else None

            action_desc = "Triage Assessment & Referral Required" if cr.status == "SUBMITTED" else "Referral Dispatch Required"

            action_items.append(
                FrontlineActionItem(
                    id=str(cr.id),
                    item_type="CARE_REQUEST",
                    patient_id=str(cr.patient_id),
                    patient_name=p_name,
                    patient_code=p_code,
                    urgency=cr.urgency_level or "MEDIUM",
                    status=cr.status,
                    action_required=action_desc,
                    facility_name=None,
                    village_name=v_name,
                    elapsed_hours=round(elapsed, 1),
                    created_at=created_ts,
                    updated_at=cr.updated_at,
                    deep_link=f"/care-requests/{cr.id}",
                )
            )

        # 4b. Referrals needing attention
        actionable_refs = (
            ref_base.options(
                joinedload(Referral.patient),
                joinedload(Referral.destination_facility),
            )
            .filter(Referral.status.in_(["PENDING_ACCEPTANCE", "ACCEPTED", "PATIENT_NOTIFIED", "DEPARTED", "ARRIVED"]))
            .order_by(Referral.created_at.desc())
            .limit(50)
            .all()
        )

        for ref in actionable_refs:
            created_ts = ref.created_at if ref.created_at.tzinfo else ref.created_at.replace(tzinfo=timezone.utc)
            elapsed = (now - created_ts).total_seconds() / 3600.0
            p_name = ref.patient.full_name if ref.patient else "Unknown Patient"
            p_code = ref.patient.anonymous_patient_code if ref.patient else "N/A"
            dest_name = ref.destination_facility.name if ref.destination_facility else None

            if ref.status == "PENDING_ACCEPTANCE":
                action_desc = f"Awaiting Acceptance by {dest_name or 'Facility'}"
            elif ref.status == "ACCEPTED":
                action_desc = "Notify Patient & Arrange Transport"
            elif ref.status == "PATIENT_NOTIFIED":
                action_desc = "Confirm Journey Departure"
            elif ref.status == "DEPARTED":
                action_desc = "Track Transit & Confirm Arrival"
            elif ref.status == "ARRIVED":
                action_desc = "Awaiting Facility Service Intake"
            else:
                action_desc = "Review Status"

            action_items.append(
                FrontlineActionItem(
                    id=str(ref.id),
                    item_type="REFERRAL",
                    patient_id=str(ref.patient_id),
                    patient_name=p_name,
                    patient_code=p_code,
                    urgency=ref.priority or "MEDIUM",
                    status=ref.status,
                    action_required=action_desc,
                    facility_name=dest_name,
                    village_name=None,
                    elapsed_hours=round(elapsed, 1),
                    created_at=created_ts,
                    updated_at=ref.updated_at,
                    deep_link=f"/referrals/{ref.id}",
                )
            )

        # Sort Action Queue:
        # Priority map: EMERGENCY -> 4, HIGH -> 3, MEDIUM -> 2, LOW -> 1
        urgency_weight = {"EMERGENCY": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        action_items.sort(
            key=lambda item: (
                urgency_weight.get(item.urgency.upper(), 1),
                item.elapsed_hours,
            ),
            reverse=True,
        )

        # 5. Recent Activity Feed
        recent_activity: List[FrontlineRecentActivity] = []
        recent_events = (
            db.query(ReferralEvent)
            .join(Referral, ReferralEvent.referral_id == Referral.id)
            .options(
                joinedload(ReferralEvent.referral).joinedload(Referral.patient),
            )
            .order_by(ReferralEvent.event_timestamp.desc())
            .limit(10)
            .all()
        )

        for ev in recent_events:
            if not ev.referral or not ev.referral.patient:
                continue
            ts = ev.event_timestamp if ev.event_timestamp.tzinfo else ev.event_timestamp.replace(tzinfo=timezone.utc)
            recent_activity.append(
                FrontlineRecentActivity(
                    id=str(ev.id),
                    item_type="REFERRAL_EVENT",
                    patient_name=ev.referral.patient.full_name,
                    patient_code=ev.referral.patient.anonymous_patient_code,
                    action_description=f"Status transitioned from {ev.from_status or 'INIT'} to {ev.to_status}",
                    timestamp=ts,
                    deep_link=f"/referrals/{ev.referral_id}",
                )
            )

        return FrontlineDashboardResponse(
            role=user_role,
            user_name=current_user.full_name,
            total_patients=total_patients,
            active_care_requests=active_cr_count,
            urgent_care_requests=urgent_cr_count,
            pending_referrals=pending_referrals_count,
            action_required_count=len(action_items),
            in_transit_referrals=in_transit_referrals_count,
            completed_referrals=completed_referrals_count,
            action_queue=action_items[:30],  # Top 30 prioritized items
            recent_activity=recent_activity,
        )

    @staticmethod
    def get_facility_dashboard(
        db: Session,
        current_user: User,
        facility_id: Optional[uuid.UUID] = None,
    ) -> FacilityDashboardResponse:
        """Aggregate operational queue, live bed occupancy, and capacity status for a healthcare facility."""
        user_role = current_user.role.name if current_user.role else "DOCTOR"
        is_admin = user_role in ("ADMIN", "DISTRICT_ADMIN")

        # Enforce Facility Scoping / Isolation
        target_facility_id = facility_id or current_user.facility_id
        if not target_facility_id:
            # For admin without specified facility, pick first active facility
            first_fac = db.query(Facility).filter(Facility.is_active == True).first()
            if not first_fac:
                raise ValueError("No healthcare facilities registered in system.")
            target_facility_id = first_fac.id

        # Non-admins cannot access foreign facilities
        if not is_admin and current_user.facility_id and str(current_user.facility_id) != str(target_facility_id):
            raise PermissionError("Access denied to foreign facility operational dashboard.")

        facility = db.query(Facility).filter(Facility.id == target_facility_id).first()
        if not facility:
            raise ValueError("Facility not found.")

        # 1. Live Bed Tracking and Safe Utilization
        total_beds = facility.total_beds or 0
        available_beds = facility.available_beds or 0
        occupied_beds = max(0, total_beds - available_beds)
        bed_util_pct = round((occupied_beds / total_beds) * 100.0, 1) if total_beds > 0 else 0.0

        icu_total = facility.icu_beds or 0
        icu_avail = facility.available_icu_beds or 0
        icu_occupied = max(0, icu_total - icu_avail)
        icu_util_pct = round((icu_occupied / icu_total) * 100.0, 1) if icu_total > 0 else 0.0

        # 2. Status Breakdown for Inbound / Destination Referrals
        status_counts = dict(
            db.query(Referral.status, func.count(Referral.id))
            .filter(Referral.destination_facility_id == facility.id)
            .group_by(Referral.status)
            .all()
        )

        status_breakdown = FacilityStatusBreakdown(
            pending_acceptance=status_counts.get("PENDING_ACCEPTANCE", 0),
            accepted=status_counts.get("ACCEPTED", 0),
            patient_notified=status_counts.get("PATIENT_NOTIFIED", 0),
            in_transit=status_counts.get("DEPARTED", 0),
            arrived=status_counts.get("ARRIVED", 0),
            in_service=status_counts.get("IN_SERVICE", 0),
            completed=status_counts.get("COMPLETED", 0),
            back_referred=status_counts.get("BACK_REFERRED", 0),
            rejected=status_counts.get("REJECTED", 0),
            rerouted=status_counts.get("REROUTED", 0),
        )

        active_count = (
            status_breakdown.pending_acceptance
            + status_breakdown.accepted
            + status_breakdown.patient_notified
            + status_breakdown.in_transit
            + status_breakdown.arrived
            + status_breakdown.in_service
        )

        # 3. Operational Queue
        operational_refs = (
            db.query(Referral)
            .options(
                joinedload(Referral.patient),
                joinedload(Referral.origin_facility),
            )
            .filter(
                Referral.destination_facility_id == facility.id,
                Referral.status.in_([
                    "PENDING_ACCEPTANCE",
                    "ACCEPTED",
                    "PATIENT_NOTIFIED",
                    "DEPARTED",
                    "ARRIVED",
                    "IN_SERVICE",
                ]),
            )
            .order_by(Referral.created_at.desc())
            .limit(50)
            .all()
        )

        now = datetime.now(timezone.utc)
        operational_queue: List[FacilityReferralQueueItem] = []
        for ref in operational_refs:
            init_ts = ref.initiated_at if ref.initiated_at.tzinfo else ref.initiated_at.replace(tzinfo=timezone.utc)
            elapsed = (now - init_ts).total_seconds() / 3600.0
            p_name = ref.patient.full_name if ref.patient else "Unknown"
            p_code = ref.patient.anonymous_patient_code if ref.patient else "N/A"
            orig_name = ref.origin_facility.name if ref.origin_facility else "Community Intake"

            operational_queue.append(
                FacilityReferralQueueItem(
                    referral_id=str(ref.id),
                    referral_code=ref.referral_code,
                    care_request_id=str(ref.care_request_id),
                    patient_id=str(ref.patient_id),
                    patient_name=p_name,
                    patient_code=p_code,
                    origin_facility_name=orig_name,
                    priority=ref.priority or "MEDIUM",
                    status=ref.status,
                    transport_mode=ref.transport_mode,
                    expected_arrival_time=ref.expected_arrival_time,
                    initiated_at=init_ts,
                    elapsed_hours=round(elapsed, 1),
                    deep_link=f"/referrals/{ref.id}",
                )
            )

        # Sort queue: PENDING_ACCEPTANCE first, then EMERGENCY, then arrival time
        status_priority = {
            "PENDING_ACCEPTANCE": 6,
            "ARRIVED": 5,
            "DEPARTED": 4,
            "IN_SERVICE": 3,
            "PATIENT_NOTIFIED": 2,
            "ACCEPTED": 1,
        }
        urgency_priority = {"EMERGENCY": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

        operational_queue.sort(
            key=lambda x: (
                status_priority.get(x.status, 0),
                urgency_priority.get(x.priority.upper(), 1),
                -x.elapsed_hours,
            ),
            reverse=True,
        )

        # 4. Capabilities Metrics
        caps = db.query(FacilityCapability).filter(FacilityCapability.facility_id == facility.id).all()
        cap_metrics: List[FacilityCapabilityMetric] = []
        avail_cnt = 0
        limit_cnt = 0
        unavail_cnt = 0

        for c in caps:
            cap_val = c.capacity or 0
            load_val = c.current_load or 0
            util = round((load_val / cap_val) * 100.0, 1) if cap_val > 0 else 0.0

            status_str = c.availability_status or "AVAILABLE"
            if status_str == "AVAILABLE":
                avail_cnt += 1
            elif status_str == "LIMITED":
                limit_cnt += 1
            else:
                unavail_cnt += 1

            cap_metrics.append(
                FacilityCapabilityMetric(
                    capability_id=str(c.id),
                    service_name=c.service_name,
                    service_category=c.service_category,
                    availability_status=status_str,
                    capacity=cap_val,
                    current_load=load_val,
                    utilization_percent=util,
                    specialist_required=c.specialist_required,
                    diagnostic_required=c.diagnostic_required,
                    operating_hours=c.operating_hours or "24x7",
                )
            )

        return FacilityDashboardResponse(
            facility_id=str(facility.id),
            facility_name=facility.name,
            facility_type=facility.facility_type,
            tier_level=facility.tier_level,
            district=facility.district,
            state=facility.state,
            operational_status=facility.operational_status,
            total_beds=total_beds,
            available_beds=available_beds,
            occupied_beds=occupied_beds,
            bed_utilization_percent=bed_util_pct,
            icu_beds_total=icu_total,
            icu_beds_available=icu_avail,
            icu_beds_occupied=icu_occupied,
            icu_utilization_percent=icu_util_pct,
            oxygen_supported_beds=facility.oxygen_supported_beds or 0,
            available_oxygen_beds=facility.available_oxygen_beds or 0,
            ventilators_count=facility.ventilators_count or 0,
            available_ventilators=facility.available_ventilators or 0,
            active_referrals_count=active_count,
            status_breakdown=status_breakdown,
            operational_queue=operational_queue,
            total_capabilities_count=len(caps),
            available_capabilities_count=avail_cnt,
            limited_capabilities_count=limit_cnt,
            unavailable_capabilities_count=unavail_cnt,
            capabilities=cap_metrics,
        )

    @staticmethod
    def get_district_dashboard(
        db: Session,
        current_user: User,
        district: Optional[str] = None,
        time_range: str = "all",
    ) -> DistrictDashboardResponse:
        """Aggregate district-level KPIs, care completion rates, and facility performance."""
        user_role = current_user.role.name if current_user.role else "DISTRICT_ADMIN"
        is_admin = user_role == "ADMIN"

        # District isolation
        target_district = district
        if not target_district:
            # If user has assigned facility, use its district
            if current_user.facility and current_user.facility.district:
                target_district = current_user.facility.district
            else:
                # Default to first district found in DB
                first_fac = db.query(Facility.district).filter(Facility.district.isnot(None)).first()
                target_district = first_fac[0] if first_fac else "Cuttack"

        # Time range cutoff
        cutoff = _get_time_cutoff(time_range)

        # 1. Total Care Requests in District
        cr_query = (
            db.query(CareRequest)
            .outerjoin(Village, CareRequest.village_id == Village.id)
            .outerjoin(Facility, CareRequest.origin_facility_id == Facility.id)
            .filter(
                or_(
                    Village.district == target_district,
                    Facility.district == target_district,
                )
            )
        )
        if cutoff:
            cr_query = cr_query.filter(CareRequest.created_at >= cutoff)

        total_crs = cr_query.count()

        # Care Requests by Category
        cr_cat_rows = (
            cr_query.with_entities(
                func.coalesce(CareRequest.care_category, "GENERAL").label("cat"),
                func.count(CareRequest.id),
            )
            .group_by("cat")
            .all()
        )
        crs_by_category = {row[0]: row[1] for row in cr_cat_rows}

        # Care Requests by Urgency
        cr_urg_rows = (
            cr_query.with_entities(
                func.coalesce(CareRequest.urgency_level, "MEDIUM").label("urg"),
                func.count(CareRequest.id),
            )
            .group_by("urg")
            .all()
        )
        crs_by_urgency = {row[0]: row[1] for row in cr_urg_rows}

        # 2. Referrals in District (destined for or originating in district)
        ref_query = (
            db.query(Referral)
            .join(Facility, Referral.destination_facility_id == Facility.id)
            .filter(Facility.district == target_district)
        )
        if cutoff:
            ref_query = ref_query.filter(Referral.initiated_at >= cutoff)

        total_refs = ref_query.count()

        ref_status_rows = (
            ref_query.with_entities(Referral.status, func.count(Referral.id))
            .group_by(Referral.status)
            .all()
        )
        refs_by_status = {row[0]: row[1] for row in ref_status_rows}

        accepted_refs = refs_by_status.get("ACCEPTED", 0) + sum(
            refs_by_status.get(s, 0)
            for s in ["PATIENT_NOTIFIED", "DEPARTED", "ARRIVED", "IN_SERVICE", "COMPLETED", "BACK_REFERRED"]
        )
        rejected_refs = refs_by_status.get("REJECTED", 0)
        completed_refs = refs_by_status.get("COMPLETED", 0) + refs_by_status.get("BACK_REFERRED", 0)
        active_refs = sum(
            refs_by_status.get(s, 0)
            for s in ["PENDING_ACCEPTANCE", "ACCEPTED", "PATIENT_NOTIFIED", "DEPARTED", "ARRIVED", "IN_SERVICE"]
        )

        urgent_emergency_count = (
            crs_by_urgency.get("EMERGENCY", 0)
            + crs_by_urgency.get("HIGH", 0)
        )

        # 3. Care Completion Rate Calculation
        # Definition: Completed Care Requests / Eligible Referred Care Requests * 100
        # Referred care requests = care requests that have an associated referral
        referred_cr_ids = (
            db.query(Referral.care_request_id)
            .join(Facility, Referral.destination_facility_id == Facility.id)
            .filter(Facility.district == target_district)
        )
        if cutoff:
            referred_cr_ids = referred_cr_ids.filter(Referral.initiated_at >= cutoff)

        eligible_referred_count = db.query(func.count(distinct(Referral.care_request_id))).join(
            Facility, Referral.destination_facility_id == Facility.id
        ).filter(Facility.district == target_district)
        if cutoff:
            eligible_referred_count = eligible_referred_count.filter(Referral.initiated_at >= cutoff)
        eligible_count = eligible_referred_count.scalar() or 0

        # Completed care requests count
        completed_cr_query = db.query(func.count(distinct(Referral.care_request_id))).join(
            Facility, Referral.destination_facility_id == Facility.id
        ).filter(
            Facility.district == target_district,
            Referral.status.in_(["COMPLETED", "BACK_REFERRED", "CLOSED"]),
        )
        if cutoff:
            completed_cr_query = completed_cr_query.filter(Referral.completed_at >= cutoff)
        completed_count = completed_cr_query.scalar() or 0

        care_completion_rate = (
            round((completed_count / eligible_count) * 100.0, 1)
            if eligible_count > 0
            else 0.0
        )

        # 4. Average Referral Completion Time (hours)
        completed_referrals = (
            ref_query.filter(
                Referral.status.in_(["COMPLETED", "BACK_REFERRED", "CLOSED"]),
                Referral.completed_at.isnot(None),
            ).all()
        )
        if completed_referrals:
            total_duration_hours = 0.0
            valid_durations = 0
            for r in completed_referrals:
                if r.completed_at and r.initiated_at:
                    init_t = r.initiated_at if r.initiated_at.tzinfo else r.initiated_at.replace(tzinfo=timezone.utc)
                    comp_t = r.completed_at if r.completed_at.tzinfo else r.completed_at.replace(tzinfo=timezone.utc)
                    dur = (comp_t - init_t).total_seconds() / 3600.0
                    if dur >= 0:
                        total_duration_hours += dur
                        valid_durations += 1
            avg_comp_hours = round(total_duration_hours / valid_durations, 1) if valid_durations > 0 else None
        else:
            avg_comp_hours = None

        # 5. Facility Performance Summary Table
        district_facilities = (
            db.query(Facility)
            .filter(Facility.district == target_district, Facility.is_active == True)
            .order_by(Facility.tier_level.desc(), Facility.name.asc())
            .all()
        )

        facility_perf_list: List[FacilityPerformanceSummary] = []
        for fac in district_facilities:
            f_ref_query = db.query(Referral).filter(Referral.destination_facility_id == fac.id)
            if cutoff:
                f_ref_query = f_ref_query.filter(Referral.initiated_at >= cutoff)

            f_counts = dict(
                f_ref_query.with_entities(Referral.status, func.count(Referral.id))
                .group_by(Referral.status)
                .all()
            )

            rec = sum(f_counts.values())
            acc = f_counts.get("ACCEPTED", 0) + sum(
                f_counts.get(s, 0)
                for s in ["PATIENT_NOTIFIED", "DEPARTED", "ARRIVED", "IN_SERVICE", "COMPLETED", "BACK_REFERRED"]
            )
            rej = f_counts.get("REJECTED", 0)
            comp = f_counts.get("COMPLETED", 0) + f_counts.get("BACK_REFERRED", 0)
            act = sum(
                f_counts.get(s, 0)
                for s in ["PENDING_ACCEPTANCE", "ACCEPTED", "PATIENT_NOTIFIED", "DEPARTED", "ARRIVED", "IN_SERVICE"]
            )
            acc_rate = round((acc / rec) * 100.0, 1) if rec > 0 else 0.0

            # Facility avg completion hours
            f_comp_refs = f_ref_query.filter(
                Referral.status.in_(["COMPLETED", "BACK_REFERRED", "CLOSED"]),
                Referral.completed_at.isnot(None),
            ).all()
            f_avg_hrs = None
            if f_comp_refs:
                f_dur = 0.0
                f_valid = 0
                for r in f_comp_refs:
                    if r.completed_at and r.initiated_at:
                        it = r.initiated_at if r.initiated_at.tzinfo else r.initiated_at.replace(tzinfo=timezone.utc)
                        ct = r.completed_at if r.completed_at.tzinfo else r.completed_at.replace(tzinfo=timezone.utc)
                        d = (ct - it).total_seconds() / 3600.0
                        if d >= 0:
                            f_dur += d
                            f_valid += 1
                if f_valid > 0:
                    f_avg_hrs = round(f_dur / f_valid, 1)

            t_beds = fac.total_beds or 0
            a_beds = fac.available_beds or 0
            u_beds = max(0, t_beds - a_beds)
            f_util = round((u_beds / t_beds) * 100.0, 1) if t_beds > 0 else 0.0
            avail_caps = db.query(func.count(FacilityCapability.id)).filter(
                FacilityCapability.facility_id == fac.id,
                FacilityCapability.availability_status == "AVAILABLE",
            ).scalar() or 0

            facility_perf_list.append(
                FacilityPerformanceSummary(
                    facility_id=str(fac.id),
                    facility_name=fac.name,
                    facility_type=fac.facility_type,
                    tier_level=fac.tier_level,
                    referrals_received=rec,
                    referrals_accepted=acc,
                    referrals_rejected=rej,
                    referrals_completed=comp,
                    active_referrals=act,
                    acceptance_rate=acc_rate,
                    avg_completion_hours=f_avg_hrs,
                    available_services_count=avail_caps,
                    total_beds=t_beds,
                    available_beds=a_beds,
                    bed_utilization_percent=f_util,
                )
            )

        return DistrictDashboardResponse(
            district_name=target_district,
            time_range=time_range,
            total_care_requests=total_crs,
            total_referrals=total_refs,
            accepted_referrals=accepted_refs,
            rejected_referrals=rejected_refs,
            completed_referrals=completed_refs,
            active_referrals=active_refs,
            urgent_emergency_count=urgent_emergency_count,
            care_completion_rate=care_completion_rate,
            avg_referral_completion_hours=avg_comp_hours,
            care_requests_by_category=crs_by_category,
            care_requests_by_urgency=crs_by_urgency,
            referrals_by_status=refs_by_status,
            facility_performance=facility_perf_list,
        )

    @staticmethod
    def get_referral_funnel(
        db: Session,
        current_user: User,
        district: Optional[str] = None,
        facility_id: Optional[uuid.UUID] = None,
        time_range: str = "all",
    ) -> ReferralFunnelResponse:
        """Calculate sequential lifecycle drop-off funnel."""
        cutoff = _get_time_cutoff(time_range)

        query = db.query(Referral)
        if facility_id:
            query = query.filter(Referral.destination_facility_id == facility_id)
        elif district:
            query = query.join(Facility, Referral.destination_facility_id == Facility.id).filter(
                Facility.district == district
            )
        if cutoff:
            query = query.filter(Referral.initiated_at >= cutoff)

        status_counts = dict(
            query.with_entities(Referral.status, func.count(Referral.id))
            .group_by(Referral.status)
            .all()
        )

        # Calculate cumulative progression through the 8 stages
        # A referral in COMPLETED has passed through all previous stages
        s_completed = status_counts.get("COMPLETED", 0) + status_counts.get("BACK_REFERRED", 0) + status_counts.get("CLOSED", 0)
        s_in_service = status_counts.get("IN_SERVICE", 0) + s_completed
        s_arrived = status_counts.get("ARRIVED", 0) + s_in_service
        s_departed = status_counts.get("DEPARTED", 0) + s_arrived
        s_notified = status_counts.get("PATIENT_NOTIFIED", 0) + s_departed
        s_accepted = status_counts.get("ACCEPTED", 0) + s_notified
        s_pending = status_counts.get("PENDING_ACCEPTANCE", 0) + s_accepted
        s_created = sum(status_counts.values())

        stage_defs = [
            ("CREATED", "Created / Initiated", s_created),
            ("PENDING_ACCEPTANCE", "Pending Acceptance", s_pending),
            ("ACCEPTED", "Accepted by Facility", s_accepted),
            ("PATIENT_NOTIFIED", "Patient Notified", s_notified),
            ("DEPARTED", "Departed / In Transit", s_departed),
            ("ARRIVED", "Arrived at Facility", s_arrived),
            ("IN_SERVICE", "In Service / Care Active", s_in_service),
            ("COMPLETED", "Care Completed", s_completed),
        ]

        total_init = s_created
        stages: List[FunnelStageItem] = []

        for i, (key, name, count) in enumerate(stage_defs):
            pct = round((count / total_init) * 100.0, 1) if total_init > 0 else 0.0
            drop_off = 0
            drop_rate = 0.0
            if i < len(stage_defs) - 1:
                next_count = stage_defs[i + 1][2]
                drop_off = max(0, count - next_count)
                drop_rate = round((drop_off / count) * 100.0, 1) if count > 0 else 0.0

            stages.append(
                FunnelStageItem(
                    stage_key=key,
                    stage_name=name,
                    count=count,
                    percentage_of_total=pct,
                    drop_off_count=drop_off,
                    drop_off_rate=drop_rate,
                )
            )

        side_branches = {
            "REJECTED": status_counts.get("REJECTED", 0),
            "REROUTED": status_counts.get("REROUTED", 0),
            "CANCELLED": status_counts.get("CANCELLED", 0),
        }

        return ReferralFunnelResponse(
            district=district,
            facility_id=str(facility_id) if facility_id else None,
            time_range=time_range,
            total_initiated=total_init,
            stages=stages,
            side_branches=side_branches,
        )

    @staticmethod
    def get_care_completion(
        db: Session,
        current_user: User,
        district: Optional[str] = None,
        time_range: str = "all",
    ) -> CareCompletionResponse:
        """Detailed breakdown of Care Completion KPI across categories and urgency tiers."""
        cutoff = _get_time_cutoff(time_range)

        # Base query for care requests
        base_cr = db.query(CareRequest)
        if district:
            base_cr = base_cr.outerjoin(Village, CareRequest.village_id == Village.id).outerjoin(
                Facility, CareRequest.origin_facility_id == Facility.id
            ).filter(
                or_(
                    Village.district == district,
                    Facility.district == district,
                )
            )
        if cutoff:
            base_cr = base_cr.filter(CareRequest.created_at >= cutoff)

        total_crs = base_cr.count()

        # Referred care requests in scope
        referred_cr_query = base_cr.filter(
            CareRequest.referral.has()
        )
        referred_count = referred_cr_query.count()

        # Completed care requests
        completed_cr_query = base_cr.filter(
            or_(
                CareRequest.status == "RESOLVED",
                CareRequest.referral.has(Referral.status.in_(["COMPLETED", "BACK_REFERRED", "CLOSED"])),
            )
        )
        completed_count = completed_cr_query.count()

        overall_rate = round((completed_count / referred_count) * 100.0, 1) if referred_count > 0 else 0.0

        # Breakdown by Urgency
        urgencies = ["EMERGENCY", "HIGH", "MEDIUM", "LOW"]
        by_urgency: List[CareCompletionByGroup] = []
        for urg in urgencies:
            u_total = base_cr.filter(CareRequest.urgency_level == urg).count()
            u_ref = base_cr.filter(CareRequest.urgency_level == urg, CareRequest.referral.has()).count()
            u_comp = base_cr.filter(
                CareRequest.urgency_level == urg,
                or_(
                    CareRequest.status == "RESOLVED",
                    CareRequest.referral.has(Referral.status.in_(["COMPLETED", "BACK_REFERRED", "CLOSED"])),
                ),
            ).count()
            u_rate = round((u_comp / u_ref) * 100.0, 1) if u_ref > 0 else 0.0
            by_urgency.append(
                CareCompletionByGroup(
                    group_name=urg,
                    total_care_requests=u_total,
                    referred_care_requests=u_ref,
                    completed_care_requests=u_comp,
                    completion_rate=u_rate,
                )
            )

        # Breakdown by Category
        categories = ["EMERGENCY", "MATERNAL_HEALTH", "GENERAL_MEDICINE", "NCD", "PEDIATRICS", "SURGERY"]
        by_category: List[CareCompletionByGroup] = []
        for cat in categories:
            c_total = base_cr.filter(CareRequest.care_category == cat).count()
            c_ref = base_cr.filter(CareRequest.care_category == cat, CareRequest.referral.has()).count()
            c_comp = base_cr.filter(
                CareRequest.care_category == cat,
                or_(
                    CareRequest.status == "RESOLVED",
                    CareRequest.referral.has(Referral.status.in_(["COMPLETED", "BACK_REFERRED", "CLOSED"])),
                ),
            ).count()
            c_rate = round((c_comp / c_ref) * 100.0, 1) if c_ref > 0 else 0.0
            by_category.append(
                CareCompletionByGroup(
                    group_name=cat,
                    total_care_requests=c_total,
                    referred_care_requests=c_ref,
                    completed_care_requests=c_comp,
                    completion_rate=c_rate,
                )
            )

        return CareCompletionResponse(
            district=district,
            time_range=time_range,
            total_care_requests=total_crs,
            referred_care_requests=referred_count,
            completed_care_requests=completed_count,
            overall_completion_rate=overall_rate,
            formula_definition="(Completed Care Requests / Eligible Referred Care Requests) * 100",
            by_urgency=by_urgency,
            by_category=by_category,
        )
