import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from enum import Enum

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


# Enums for BoN PSD compliance
class PSDStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_IMPROVEMENTS = "requires_improvements"

class ApplicationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_SANDBOX = "in_sandbox"
    GRADUATED = "graduated"

class CompanyType(str, Enum):
    STARTUP = "startup"
    SME = "sme"
    ENTERPRISE = "enterprise"

class InnovationCategory(str, Enum):
    PAYMENTS = "payments"
    LENDING = "lending"
    INSURANCE = "insurance"
    INVESTMENT = "investment"
    CRYPTOCURRENCY = "cryptocurrency"
    REGTECH = "regtech"
    OTHER = "other"


# Enhanced User schemas with BoN compliance
class UserRead(schemas.BaseUser[uuid.UUID]):
    mfa_enabled: bool = False
    last_login_ip: Optional[str] = None
    account_locked: bool = False
    eta_2019_consent: bool = False
    consent_timestamp: Optional[datetime] = None
    company_id: Optional[UUID] = None


class UserCreate(schemas.BaseUserCreate):
    mfa_enabled: bool = False
    company_id: Optional[UUID] = None


class UserUpdate(schemas.BaseUserUpdate):
    mfa_enabled: Optional[bool] = None
    company_id: Optional[UUID] = None


# Company schemas with PSD compliance
class CompanyBase(BaseModel):
    legal_name: str
    trading_name: Optional[str] = None
    registration_number: str
    tax_id: Optional[str] = None
    company_type: Optional[CompanyType] = None
    industry: Optional[str] = None
    founded_date: Optional[datetime] = None
    employee_count: Optional[int] = None
    website: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    contact_details: Optional[Dict[str, Any]] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyRead(CompanyBase):
    id: UUID
    psd1_licensing_status: str = PSDStatus.PENDING
    psd3_emoney_classification: Optional[str] = None
    psd6_authorization_status: Optional[str] = None
    kyc_status: str = PSDStatus.PENDING
    kyb_status: str = PSDStatus.PENDING
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyUpdate(BaseModel):
    legal_name: Optional[str] = None
    trading_name: Optional[str] = None
    tax_id: Optional[str] = None
    company_type: Optional[CompanyType] = None
    industry: Optional[str] = None
    founded_date: Optional[datetime] = None
    employee_count: Optional[int] = None
    website: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    contact_details: Optional[Dict[str, Any]] = None


# Application schemas with comprehensive PSD compliance
class ApplicationBase(BaseModel):
    innovation_category: Optional[InnovationCategory] = None
    business_model: Optional[str] = None
    target_market: Optional[str] = None
    competitive_advantage: Optional[str] = None
    technical_architecture: Optional[str] = None
    risk_assessment: Optional[Dict[str, Any]] = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationRead(ApplicationBase):
    id: UUID
    application_number: str
    company_id: UUID
    applicant_id: UUID
    status: str = ApplicationStatus.DRAFT

    # PSD compliance tracking
    psd1_licensing_status: Optional[str] = None
    psd3_emoney_classification: Optional[str] = None
    psd6_authorization_status: Optional[str] = None
    psd9_crossborder_status: Optional[str] = None
    psd12_cybersecurity_score: Optional[Decimal] = None

    # Document integrity
    data_message_hash: Optional[str] = None
    electronic_signature_metadata: Optional[Dict[str, Any]] = None

    # Timestamps
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    graduation_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationUpdate(BaseModel):
    innovation_category: Optional[InnovationCategory] = None
    business_model: Optional[str] = None
    target_market: Optional[str] = None
    competitive_advantage: Optional[str] = None
    technical_architecture: Optional[str] = None
    risk_assessment: Optional[Dict[str, Any]] = None


# Document schemas with ETA 2019 compliance
class DocumentBase(BaseModel):
    document_type: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentRead(DocumentBase):
    id: UUID
    application_id: UUID
    uploaded_by: UUID

    # Security and integrity
    storage_key: str
    sha256_hash: str
    originality_certificate: Optional[Dict[str, Any]] = None

    # Electronic signature support
    signature_status: str = "none"
    signature_metadata: Optional[Dict[str, Any]] = None

    # ETA 2019 compliance
    evidence_certificate: Optional[Dict[str, Any]] = None
    retention_expiry_date: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Compliance schemas
class ComplianceScoreBase(BaseModel):
    overall_score: Decimal
    psd1_score: Optional[Decimal] = None
    psd3_score: Optional[Decimal] = None
    psd4_score: Optional[Decimal] = None
    psd5_score: Optional[Decimal] = None
    psd6_score: Optional[Decimal] = None
    psd8_score: Optional[Decimal] = None
    psd9_score: Optional[Decimal] = None
    psd12_score: Optional[Decimal] = None
    psd13_score: Optional[Decimal] = None
    psdir4_score: Optional[Decimal] = None
    psdir5_score: Optional[Decimal] = None
    psdir7_score: Optional[Decimal] = None
    psdir8_score: Optional[Decimal] = None
    psdir9_score: Optional[Decimal] = None
    psdir10_score: Optional[Decimal] = None
    psdir11_score: Optional[Decimal] = None


class ComplianceScoreRead(ComplianceScoreBase):
    id: UUID
    application_id: UUID
    participant_id: Optional[UUID] = None
    ai_analysis_result: Optional[Dict[str, Any]] = None
    confidence_score: Optional[Decimal] = None
    explanation: Optional[str] = None
    calculated_at: datetime

    model_config = {"from_attributes": True}


# Audit trail schemas
class AuditTrailBase(BaseModel):
    event_type: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    psd_sections: Optional[List[str]] = None
    psdir_sections: Optional[List[str]] = None
    compliance_score: Optional[Decimal] = None


class AuditTrailRead(AuditTrailBase):
    id: UUID
    event_id: str
    user_id: Optional[UUID] = None
    participant_id: Optional[UUID] = None
    application_id: Optional[UUID] = None
    current_hash: str
    previous_hash: Optional[str] = None
    chain_hash: str
    evidence_preservation_timestamp: datetime
    legal_custodian: str = "NAMFISA"
    eta2019_section25_compliant: bool = True
    admissible_in_court: bool = True
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Keep the original Item schemas for backward compatibility
class ItemBase(BaseModel):
    name: str
    description: str | None = None
    quantity: int | None = None


class ItemCreate(ItemBase):
    pass


class ItemRead(ItemBase):
    id: UUID
    user_id: UUID

    model_config = {"from_attributes": True}
