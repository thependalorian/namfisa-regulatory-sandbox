from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime, JSON, DECIMAL, Text, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid


class Base(DeclarativeBase):
    pass


class DocumentValidation(Base):
    __tablename__ = "document_validations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), nullable=False)
    application_id = Column(UUID(as_uuid=True), nullable=False)

    # Validation results
    validation_result = Column(JSON, nullable=False)
    confidence_score = Column(DECIMAL(3, 2), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # PSD compliance
    psd_sections_validated = Column(JSON, nullable=True)  # List of PSD sections checked
    compliance_status = Column(String(50), nullable=True)  # compliant, non_compliant, partial

    created_at = Column(DateTime, default=datetime.utcnow)


class ApplicationTriage(Base):
    __tablename__ = "application_triages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), nullable=False)

    # Triage results
    risk_score = Column(DECIMAL(3, 2), nullable=False)
    priority = Column(String(20), nullable=False)  # HIGH, MEDIUM, LOW
    recommended_reviewers = Column(JSON, nullable=True)  # List of expertise needed
    estimated_review_time = Column(Integer, nullable=True)  # Hours

    # Compliance analysis
    compliance_gaps = Column(JSON, nullable=True)  # List of PSD sections needing attention
    immediate_flags = Column(JSON, nullable=True)  # Urgent compliance issues

    created_at = Column(DateTime, default=datetime.utcnow)


class ComplianceAnalysis(Base):
    __tablename__ = "compliance_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), nullable=False)

    # Analysis results
    overall_compliance_score = Column(DECIMAL(3, 2), nullable=False)
    psd_compliance_scores = Column(JSON, nullable=True)  # Dict of PSD section scores
    risk_assessment = Column(JSON, nullable=True)

    # Recommendations
    critical_gaps = Column(JSON, nullable=True)  # Must-fix compliance issues
    recommendations = Column(JSON, nullable=True)  # Prioritized improvement suggestions
    estimated_implementation_time = Column(Integer, nullable=True)  # Days to reach compliance

    created_at = Column(DateTime, default=datetime.utcnow)


class AIModelPerformance(Base):
    __tablename__ = "ai_model_performances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    metric_type = Column(String(50), nullable=False)  # accuracy, precision, recall, f1
    metric_value = Column(DECIMAL(5, 4), nullable=False)

    # Test details
    test_dataset = Column(String(100), nullable=True)
    evaluated_at = Column(DateTime, default=datetime.utcnow)
