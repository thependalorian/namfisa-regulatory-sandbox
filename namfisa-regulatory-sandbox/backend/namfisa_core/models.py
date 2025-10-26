from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime, JSON, DECIMAL, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from uuid import uuid4
from datetime import datetime
from typing import List, Optional
import enum


class Base(DeclarativeBase):
    pass


# Enums for BoN PSD compliance
class PSDStatus(enum.Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_IMPROVEMENTS = "requires_improvements"

class ApplicationStatus(enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_SANDBOX = "in_sandbox"
    GRADUATED = "graduated"

class CompanyType(enum.Enum):
    STARTUP = "startup"
    SME = "sme"
    ENTERPRISE = "enterprise"

class InnovationCategory(enum.Enum):
    PAYMENTS = "payments"
    LENDING = "lending"
    INSURANCE = "insurance"
    INVESTMENT = "investment"
    CRYPTOCURRENCY = "cryptocurrency"
    REGTECH = "regtech"
    OTHER = "other"


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    # BoN PSD-12 cybersecurity compliance
    mfa_enabled = Column(Boolean, default=False)
    last_login_ip = Column(String, nullable=True)
    login_attempts = Column(Integer, default=0)
    account_locked = Column(Boolean, default=False)
    security_questions = Column(JSON, nullable=True)

    # ETA 2019 Section 20 signature readiness
    eta_2019_consent = Column(Boolean, default=False)
    consent_timestamp = Column(TIMESTAMP, nullable=True)

    # Relationships
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    company = relationship("Company", back_populates="users")
    applications = relationship("Application", back_populates="applicant")
    audit_entries = relationship("AuditTrail", back_populates="user")


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    legal_name = Column(String(500), nullable=False)
    trading_name = Column(String(500), nullable=True)
    registration_number = Column(String(100), unique=True, nullable=False)
    tax_id = Column(String(100), nullable=True)

    # PSD-1 licensing status
    psd1_licensing_status = Column(String(50), default=PSDStatus.PENDING.value)
    psd1_license_number = Column(String(100), nullable=True)
    psd1_licensed_at = Column(TIMESTAMP, nullable=True)

    # PSD-3 e-money classification
    psd3_emoney_classification = Column(String(50), nullable=True)  # micro, non_micro
    psd3_authorization_status = Column(String(50), nullable=True)
    psd3_float_limit = Column(DECIMAL(15, 2), nullable=True)

    # PSD-6 authorization
    psd6_authorization_status = Column(String(50), nullable=True)
    psd6_authorized_services = Column(JSON, nullable=True)  # List of authorized services

    # KYC/KYB verification
    kyc_status = Column(String(50), default=PSDStatus.PENDING.value)
    kyb_status = Column(String(50), default=PSDStatus.PENDING.value)
    verification_documents = Column(JSON, nullable=True)

    # Company details
    company_type = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    founded_date = Column(TIMESTAMP, nullable=True)
    employee_count = Column(Integer, nullable=True)
    website = Column(String(500), nullable=True)
    address = Column(JSON, nullable=True)
    contact_details = Column(JSON, nullable=True)

    # Relationships
    users = relationship("User", back_populates="company")
    applications = relationship("Application", back_populates="company")

    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    application_number = Column(String(100), unique=True, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Application status
    status = Column(String(50), default=ApplicationStatus.DRAFT.value)

    # PSD compliance tracking
    psd1_licensing_status = Column(String(50), nullable=True)
    psd3_emoney_classification = Column(String(50), nullable=True)
    psd6_authorization_status = Column(String(50), nullable=True)
    psd9_crossborder_status = Column(String(50), nullable=True)
    psd12_cybersecurity_score = Column(DECIMAL(3, 2), nullable=True)

    # Application details
    innovation_category = Column(String(100), nullable=True)
    business_model = Column(Text, nullable=True)
    target_market = Column(Text, nullable=True)
    competitive_advantage = Column(Text, nullable=True)
    technical_architecture = Column(Text, nullable=True)
    risk_assessment = Column(JSON, nullable=True)

    # Document integrity (ETA 2019 Section 21)
    data_message_hash = Column(String(64), nullable=True)
    electronic_signature_metadata = Column(JSON, nullable=True)

    # Timestamps
    submitted_at = Column(TIMESTAMP, nullable=True)
    approved_at = Column(TIMESTAMP, nullable=True)
    rejected_at = Column(TIMESTAMP, nullable=True)
    graduation_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    company = relationship("Company", back_populates="applications")
    applicant = relationship("User", back_populates="applications")
    documents = relationship("Document", back_populates="application")
    compliance_scores = relationship("ComplianceScore", back_populates="application")
    audit_entries = relationship("AuditTrail", back_populates="application")

    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    document_type = Column(String(100), nullable=False)
    file_name = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)

    # Security and integrity
    storage_key = Column(String(500), unique=True, nullable=False)
    encryption_key_id = Column(String(100), nullable=True)
    sha256_hash = Column(String(64), nullable=False)  # Content integrity (ETA 2019 Sec 21)
    originality_certificate = Column(JSON, nullable=True)  # ETA 2019 Section 21 compliance

    # Electronic signature support (CRAN ready)
    signature_status = Column(String(50), default="none")  # none, prepared, signed, verified
    signature_metadata = Column(JSON, nullable=True)
    signature_certificate = Column(JSON, nullable=True)

    # Audit and compliance
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    upload_ip = Column(String(45), nullable=True)
    upload_user_agent = Column(Text, nullable=True)

    # ETA 2019 Section 25 evidence admissibility
    evidence_certificate = Column(JSON, nullable=True)
    retention_expiry_date = Column(TIMESTAMP, nullable=True)
    legal_custodian = Column(String(200), default="NAMFISA")

    # Relationships
    application = relationship("Application", back_populates="documents")
    uploader = relationship("User", back_populates="uploaded_documents")
    access_audit = relationship("DocumentAccessAudit", back_populates="document")
    integrity_checks = relationship("DocumentIntegrityCheck", back_populates="document")

    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)


class ComplianceScore(Base):
    __tablename__ = "compliance_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    participant_id = Column(UUID(as_uuid=True), nullable=True)  # For post-approval tracking

    # Overall compliance score
    overall_score = Column(DECIMAL(3, 2), nullable=False)

    # Individual PSD scores
    psd1_score = Column(DECIMAL(3, 2), nullable=True)  # Licensing
    psd3_score = Column(DECIMAL(3, 2), nullable=True)  # E-money
    psd4_score = Column(DECIMAL(3, 2), nullable=True)  # Card payments
    psd5_score = Column(DECIMAL(3, 2), nullable=True)  # Consumer protection
    psd6_score = Column(DECIMAL(3, 2), nullable=True)  # Authorization
    psd8_score = Column(DECIMAL(3, 2), nullable=True)  # Penalties
    psd9_score = Column(DECIMAL(3, 2), nullable=True)  # Cross-border
    psd12_score = Column(DECIMAL(3, 2), nullable=True)  # Cybersecurity
    psd13_score = Column(DECIMAL(3, 2), nullable=True)  # Systemic importance

    # PSDIR scores
    psdir4_score = Column(DECIMAL(3, 2), nullable=True)  # Reporting
    psdir5_score = Column(DECIMAL(3, 2), nullable=True)  # Audit
    psdir7_score = Column(DECIMAL(3, 2), nullable=True)  # Data protection
    psdir8_score = Column(DECIMAL(3, 2), nullable=True)  # Localization
    psdir9_score = Column(DECIMAL(3, 2), nullable=True)  # CMA cross-border
    psdir10_score = Column(DECIMAL(3, 2), nullable=True)  # SADC protocols
    psdir11_score = Column(DECIMAL(3, 2), nullable=True)  # Market conduct

    # AI analysis results
    ai_analysis_result = Column(JSON, nullable=True)
    confidence_score = Column(DECIMAL(3, 2), nullable=True)
    explanation = Column(Text, nullable=True)

    # Timestamps
    calculated_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="compliance_scores")


class AuditTrail(Base):
    __tablename__ = "audit_trail"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(String(100), unique=True, nullable=False)
    event_type = Column(String(100), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    participant_id = Column(UUID(as_uuid=True), nullable=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True)

    # Event context
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(200), nullable=False)

    # Cryptographic integrity (ETA 2019 Section 21 & 22)
    current_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=True)
    chain_hash = Column(String(64), nullable=False)

    # Legal evidence (ETA 2019 Section 25)
    evidence_preservation_timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    legal_custodian = Column(String(200), default="NAMFISA")
    eta2019_section25_compliant = Column(Boolean, default=True)
    admissible_in_court = Column(Boolean, default=True)

    # PSD/PSDIR context
    psd_sections = Column(JSON, nullable=True)  # Array of related PSD sections
    psdir_sections = Column(JSON, nullable=True)  # Array of related PSDIR sections
    compliance_score = Column(DECIMAL(3, 2), nullable=True)

    # Network context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(200), nullable=True)

    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class DocumentAccessAudit(Base):
    __tablename__ = "document_access_audit"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)  # view, download, modify, delete
    access_timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    access_purpose = Column(String(200), nullable=True)

    # Cryptographic chaining for immutability
    audit_hash = Column(String(64), nullable=False)
    previous_audit_hash = Column(String(64), nullable=True)

    # Legal evidence
    eta2019_section25_compliant = Column(Boolean, default=True)
    legal_evidence_preserved = Column(Boolean, default=True)

    # Relationships
    document = relationship("Document", back_populates="access_audit")
    accessor = relationship("User")


class DocumentIntegrityCheck(Base):
    __tablename__ = "document_integrity_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    integrity_check_type = Column(String(50), nullable=False)  # scheduled, on-demand, pre-access
    expected_hash = Column(String(64), nullable=False)
    actual_hash = Column(String(64), nullable=False)
    integrity_verified = Column(Boolean, nullable=False)
    checked_at = Column(TIMESTAMP, default=datetime.utcnow)

    # ETA 2019 compliance
    eta2019_section21_compliant = Column(Boolean, default=True)
    eta2019_section22_compliant = Column(Boolean, default=True)

    # Relationships
    document = relationship("Document", back_populates="integrity_checks")


# Keep the original Item model for backward compatibility
class Item(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="items")
