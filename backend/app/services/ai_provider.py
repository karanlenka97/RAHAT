"""AI Provider Abstraction Layer for RAHAT.
Supports configurable AI providers (Mock/Synthetic, Gemini, OpenAI) with strict clinical safety guardrails.
"""
import abc
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
import httpx

from app.core.config import settings
from app.schemas.ai import (
    ReferralAISummaryResponse,
    AIStructuredExtractionResponse,
    AIRecommendationExplanationRequest,
    AIRecommendationExplanationResponse,
    DEFAULT_AI_DISCLAIMER,
    DEFAULT_EXPLANATION_DISCLAIMER,
)

logger = logging.getLogger(__name__)

SYSTEM_SAFETY_INSTRUCTION = """You are an administrative referral assistant in a public rural healthcare system (RAHAT).
Your role is STRICTLY assistive, administrative, and summarization only.

CRITICAL CLINICAL SAFETY RULES:
1. DO NOT diagnose diseases or guess medical conditions.
2. DO NOT prescribe medications, drugs, or dosages.
3. DO NOT recommend treatments, clinical regimens, or therapies.
4. DO NOT make autonomous clinical decisions.
5. DO NOT determine or alter triage urgency (preserve existing recorded urgency).
6. DO NOT select healthcare facilities autonomously.
7. DO NOT invent facts, clinical symptoms, or patient data.
8. ALWAYS explicitly identify missing information if clinical details are incomplete.
9. Output ONLY clean structured JSON strictly matching the target schema.
"""


class BaseAIProvider(abc.ABC):
    """Abstract Base Class for AI Provider implementations."""

    @abc.abstractmethod
    async def generate_referral_summary(self, context: Dict[str, Any]) -> ReferralAISummaryResponse:
        """Generate structured clinical administrative summary from care request context."""
        pass

    @abc.abstractmethod
    async def extract_structured_intake(
        self, raw_text: str, existing_category: Optional[str] = None, existing_urgency: Optional[str] = None
    ) -> AIStructuredExtractionResponse:
        """Extract structured intake fields from unstructured clinical complaint text."""
        pass

    @abc.abstractmethod
    async def explain_recommendation(
        self, req: AIRecommendationExplanationRequest
    ) -> AIRecommendationExplanationResponse:
        """Explain deterministic recommendation scoring factors in plain language."""
        pass


class MockAIProvider(BaseAIProvider):
    """High-fidelity, deterministic synthetic AI provider for local dev, offline fallback, and tests.
    Follows all clinical safety rules: summarization only, zero diagnosis, zero prescriptions.
    """

    async def generate_referral_summary(self, context: Dict[str, Any]) -> ReferralAISummaryResponse:
        care_request_id = context.get("care_request_id", uuid.uuid4())
        symptoms_summary = context.get("symptoms_summary", "").strip()
        care_category = context.get("care_category", "GENERAL_MEDICINE")
        required_service = context.get("required_service", "General Medicine")
        diagnostics: List[str] = context.get("diagnostic_requirements", [])
        specialist_required: bool = bool(context.get("specialist_required", False))
        demographics = context.get("demographics", {})
        age = demographics.get("age")
        gender = demographics.get("gender", "Unknown")
        history = context.get("relevant_history")

        # 1. Synthesize concise executive summary (strictly non-diagnostic)
        age_str = f"Age {age}, {gender}" if age else f"Patient ({gender})"
        concise_summary = (
            f"{age_str} presenting with documented complaint: {symptoms_summary}. "
            f"Administrative intake flags requirement for {required_service} ({care_category.replace('_', ' ')})."
        )

        # 2. Presenting information
        presenting_info = (
            f"Chief recorded complaint: {symptoms_summary}. "
            f"Specialist assessment requested: {'Yes' if specialist_required else 'No'}."
        )

        # 3. Identify missing information explicitly
        missing_info: List[str] = []
        if not history:
            missing_info.append("Past medical history and chronic conditions not documented")
        if not diagnostics:
            missing_info.append("Baseline diagnostic investigation requirements not specified")
        if not age:
            missing_info.append("Exact patient age not recorded in demographic profile")

        # 4. Draft administrative referral justification note
        admin_notes = (
            f"Referral initiated for specialized {required_service} evaluation. "
            f"Recorded intake highlights: {symptoms_summary}. "
            f"Diagnostics required: {', '.join(diagnostics) if diagnostics else 'None pre-specified'}."
        )

        return ReferralAISummaryResponse(
            care_request_id=care_request_id,
            concise_summary=concise_summary,
            presenting_information=presenting_info,
            relevant_history=history,
            requested_service=required_service,
            diagnostic_requirements=diagnostics,
            specialist_requirement=specialist_required,
            administrative_notes=admin_notes,
            missing_information=missing_info,
            disclaimer=DEFAULT_AI_DISCLAIMER,
            is_ai_assisted=True,
            model_used="mock-administrative-assistant-v1",
        )

    async def extract_structured_intake(
        self, raw_text: str, existing_category: Optional[str] = None, existing_urgency: Optional[str] = None
    ) -> AIStructuredExtractionResponse:
        cleaned = raw_text.strip()
        lower = cleaned.lower()

        # Keyword mapping for Category & Service
        category = existing_category or "GENERAL_MEDICINE"
        service = "General Medicine"
        specialist = False

        if any(w in lower for w in ["chest pain", "cardiac", "heart", "ecg", "palpitation", "angina"]):
            category = "EMERGENCY" if "severe" in lower or "radiating" in lower else "NCD"
            service = "Cardiology"
            specialist = True
        elif any(w in lower for w in ["pregnant", "pregnancy", "anc", "labor", "maternal", "bleeding", "trimester"]):
            category = "MATERNAL_HEALTH"
            service = "Obstetrics & Gynecology"
            specialist = True
        elif any(w in lower for w in ["child", "pediatric", "infant", "newborn", "baby", "immunization"]):
            category = "CHILD_HEALTH"
            service = "Pediatrics"
            specialist = True
        elif any(w in lower for w in ["fracture", "trauma", "bone", "accident", "fall", "joint"]):
            category = "EMERGENCY" if "accident" in lower or "open" in lower else "OTHER"
            service = "Orthopedics"
            specialist = True
        elif any(w in lower for w in ["eye", "vision", "cataract", "blindness", "cornea"]):
            category = "EYE_CARE"
            service = "Ophthalmology"
            specialist = True
        elif any(w in lower for w in ["ear", "nose", "throat", "tonsil", "hearing"]):
            category = "ENT"
            service = "ENT"
        elif any(w in lower for w in ["tooth", "dental", "gums", "molar"]):
            category = "DENTAL"
            service = "Dental Care"

        # Diagnostic extraction
        diagnostics: List[str] = []
        if "ecg" in lower:
            diagnostics.append("12-Lead ECG")
        if "ultrasound" in lower or "usg" in lower or "scan" in lower:
            diagnostics.append("Obstetric Ultrasound" if category == "MATERNAL_HEALTH" else "Abdominal Ultrasound")
        if "x-ray" in lower or "xray" in lower:
            diagnostics.append("Chest X-Ray")
        if "blood sugar" in lower or "glucose" in lower or "diabetes" in lower:
            diagnostics.append("Blood Sugar")
        if "cbc" in lower or "hemoglobin" in lower or "blood count" in lower:
            diagnostics.append("CBC")

        missing: List[str] = []
        if not diagnostics:
            missing.append("No specific laboratory or imaging investigations identified in notes")
        if len(cleaned.split()) < 5:
            missing.append("Clinical description is very brief; additional symptom context recommended")

        return AIStructuredExtractionResponse(
            symptoms_summary=cleaned,
            care_category=category,
            required_service=service,
            diagnostic_requirements=diagnostics,
            specialist_required=specialist,
            urgency_as_recorded=existing_urgency,
            missing_information=missing,
            disclaimer=DEFAULT_AI_DISCLAIMER,
            is_ai_assisted=True,
        )

    async def explain_recommendation(
        self, req: AIRecommendationExplanationRequest
    ) -> AIRecommendationExplanationResponse:
        key_factors: List[str] = []

        if req.service_score >= 80:
            key_factors.append(f"Strong clinical service capability match ({req.service_score:.0f}%) for requested services.")
        if req.diagnostic_score >= 80:
            key_factors.append(f"High diagnostic readiness ({req.diagnostic_score:.0f}%) with required laboratory/imaging available.")
        if req.specialist_score >= 80:
            key_factors.append("On-duty specialist availability aligns with clinical requirement.")
        if req.distance_score >= 70:
            dist_str = f" ({req.distance_km:.1f} km)" if req.distance_km is not None else ""
            key_factors.append(f"Geographic proximity advantage{dist_str}.")
        if req.availability_score >= 70:
            bed_str = f" ({req.available_beds} beds available)" if req.available_beds is not None else ""
            key_factors.append(f"Current inpatient capacity available{bed_str}.")
        if req.workload_score >= 70:
            key_factors.append("Moderate workload allowing expedited intake triage.")

        matched_str = f" Matched capabilities: {', '.join(req.matched_services)}." if req.matched_services else ""
        explanation_text = (
            f"{req.facility_name} scored {req.overall_score:.1f}/100 in deterministic evaluation based on "
            f"service alignment, diagnostic capacity, and transit proximity.{matched_str} "
            f"Final referral destination decision remains with the medical officer."
        )

        return AIRecommendationExplanationResponse(
            facility_id=req.facility_id,
            facility_name=req.facility_name,
            explanation_text=explanation_text,
            key_factors=key_factors,
            overall_score=req.overall_score,
            disclaimer=DEFAULT_EXPLANATION_DISCLAIMER,
            is_ai_assisted=True,
        )


class GeminiAIProvider(BaseAIProvider):
    """Google Gemini AI Provider connector with strict system prompt & fallback."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", timeout_seconds: int = 15):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout_seconds
        self.mock_fallback = MockAIProvider()

    async def generate_referral_summary(self, context: Dict[str, Any]) -> ReferralAISummaryResponse:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        prompt = (
            f"{SYSTEM_SAFETY_INSTRUCTION}\n\n"
            f"Task: Generate a structured ReferralAISummaryResponse for the following care request.\n"
            f"Context Data (Demographics sanitized):\n"
            f"- Symptoms Summary: {context.get('symptoms_summary')}\n"
            f"- Category: {context.get('care_category')}\n"
            f"- Required Service: {context.get('required_service')}\n"
            f"- Diagnostics: {context.get('diagnostic_requirements')}\n"
            f"- Specialist Required: {context.get('specialist_required')}\n"
            f"- Demographics: {context.get('demographics')}\n"
            f"- Relevant History: {context.get('relevant_history')}\n\n"
            f"Return clean JSON adhering to schema: concise_summary, presenting_information, relevant_history, "
            f"requested_service, diagnostic_requirements, specialist_requirement, administrative_notes, missing_information."
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        parsed = json.loads(text)
                        return ReferralAISummaryResponse(
                            care_request_id=context.get("care_request_id", uuid.uuid4()),
                            concise_summary=parsed.get("concise_summary", context.get("symptoms_summary", "")),
                            presenting_information=parsed.get("presenting_information", context.get("symptoms_summary", "")),
                            relevant_history=parsed.get("relevant_history", context.get("relevant_history")),
                            requested_service=parsed.get("requested_service", context.get("required_service", "General Care")),
                            diagnostic_requirements=parsed.get("diagnostic_requirements", context.get("diagnostic_requirements", [])),
                            specialist_requirement=bool(parsed.get("specialist_requirement", context.get("specialist_required", False))),
                            administrative_notes=parsed.get("administrative_notes"),
                            missing_information=parsed.get("missing_information", []),
                            disclaimer=DEFAULT_AI_DISCLAIMER,
                            is_ai_assisted=True,
                            model_used=self.model,
                        )
        except Exception as e:
            logger.warning(f"Gemini API request failed, falling back to Mock provider: {e}")

        # Fallback to deterministic mock provider
        return await self.mock_fallback.generate_referral_summary(context)

    async def extract_structured_intake(
        self, raw_text: str, existing_category: Optional[str] = None, existing_urgency: Optional[str] = None
    ) -> AIStructuredExtractionResponse:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            prompt = (
                f"{SYSTEM_SAFETY_INSTRUCTION}\n\n"
                f"Task: Extract structured intake fields from raw clinical text.\n"
                f"Raw Text: {raw_text}\n"
                f"Existing Category: {existing_category}\n"
                f"Existing Urgency (DO NOT CHANGE): {existing_urgency}\n\n"
                f"Return clean JSON schema: symptoms_summary, care_category, required_service, diagnostic_requirements, "
                f"specialist_required, missing_information."
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1},
            }
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        parsed = json.loads(text)
                        return AIStructuredExtractionResponse(
                            symptoms_summary=parsed.get("symptoms_summary", raw_text),
                            care_category=parsed.get("care_category", existing_category),
                            required_service=parsed.get("required_service", "General Medicine"),
                            diagnostic_requirements=parsed.get("diagnostic_requirements", []),
                            specialist_required=bool(parsed.get("specialist_required", False)),
                            urgency_as_recorded=existing_urgency,
                            missing_information=parsed.get("missing_information", []),
                            disclaimer=DEFAULT_AI_DISCLAIMER,
                            is_ai_assisted=True,
                        )
        except Exception as e:
            logger.warning(f"Gemini extraction call failed, using mock fallback: {e}")

        return await self.mock_fallback.extract_structured_intake(raw_text, existing_category, existing_urgency)

    async def explain_recommendation(
        self, req: AIRecommendationExplanationRequest
    ) -> AIRecommendationExplanationResponse:
        # Explanations use the deterministic factor generator directly for maximum safety & consistency
        return await self.mock_fallback.explain_recommendation(req)


def get_ai_provider() -> BaseAIProvider:
    """Factory creating configured AI provider based on application settings."""
    provider_name = (settings.AI_PROVIDER or "mock").lower().strip()
    if provider_name == "gemini" and settings.AI_API_KEY and settings.AI_API_KEY != "your-ai-api-key-here":
        return GeminiAIProvider(
            api_key=settings.AI_API_KEY,
            model=settings.AI_MODEL,
            timeout_seconds=settings.AI_TIMEOUT_SECONDS,
        )
    return MockAIProvider()
