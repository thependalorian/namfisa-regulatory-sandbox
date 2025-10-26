from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class DocumentValidationRequest(BaseModel):
    documents: List[Dict[str, Any]] = Field(..., description="List of documents to validate")
    psd_requirements: Dict[str, str] = Field(..., description="PSD requirements to check against")


class DocumentValidationResponse(BaseModel):
    validation_id: str
    overall_score: float
    validation_results: List[Dict[str, Any]]
    recommendations: List[str]
    processing_time_ms: int
    created_at: datetime


class ApplicationTriageRequest(BaseModel):
    application_data: Dict[str, Any] = Field(..., description="Complete application data for triage")


class ApplicationTriageResponse(BaseModel):
    triage_id: str
    risk_score: float
    priority: str
    recommended_reviewers: List[str]
    compliance_gaps: List[str]
    estimated_review_time: int
    immediate_flags: List[str]
    created_at: datetime


class ComplianceAnalysisRequest(BaseModel):
    application_data: Dict[str, Any] = Field(..., description="Complete application data for analysis")


class ComplianceAnalysisResponse(BaseModel):
    analysis_id: str
    overall_compliance_score: float
    psd_compliance_scores: Dict[str, float]
    critical_gaps: List[str]
    recommendations: List[str]
    risk_assessment: Dict[str, Any]
    estimated_implementation_time: int
    created_at: datetime


class DocumentInfo(BaseModel):
    id: UUID
    document_type: str
    file_name: str
    file_size: Optional[int]
    mime_type: Optional[str]
    content: Optional[str] = None


class ValidationResult(BaseModel):
    document_id: UUID
    compliance_status: str
    confidence_score: float
    missing_sections: List[str]
    recommendations: List[str]
    risk_flags: List[str]
    psd_sections_validated: List[str]


class TriageResult(BaseModel):
    application_id: UUID
    risk_score: float
    priority: str
    recommended_reviewers: List[str]
    compliance_gaps: List[str]
    estimated_review_time: int
    immediate_flags: List[str]


class ComplianceResult(BaseModel):
    application_id: UUID
    overall_compliance_score: float
    psd_compliance_scores: Dict[str, float]
    critical_gaps: List[str]
    recommendations: List[str]
    risk_assessment: Dict[str, Any]
    estimated_implementation_time: int
