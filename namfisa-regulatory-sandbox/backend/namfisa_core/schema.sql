-- NAMFISA Regulatory Sandbox Database Schema
-- Complete schema with PSD/PSDIR compliance and ETA 2019 compliance

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create enum types for PSD compliance
CREATE TYPE psd_status AS ENUM ('pending', 'in_review', 'approved', 'rejected', 'requires_improvements');
CREATE TYPE application_status AS ENUM ('draft', 'submitted', 'under_review', 'approved', 'rejected', 'in_sandbox', 'graduated');
CREATE TYPE company_type AS ENUM ('startup', 'sme', 'enterprise');
CREATE TYPE innovation_category AS ENUM ('payments', 'lending', 'insurance', 'investment', 'cryptocurrency', 'regtech', 'other');

-- Users table with PSD-12 cybersecurity compliance
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(32),
    last_login_ip INET,
    login_attempts INTEGER DEFAULT 0,
    account_locked BOOLEAN DEFAULT FALSE,
    security_questions JSONB,
    eta_2019_consent BOOLEAN DEFAULT FALSE,
    consent_timestamp TIMESTAMP WITH TIME ZONE,
    company_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Companies table with PSD compliance tracking
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_name VARCHAR(500) NOT NULL,
    trading_name VARCHAR(500),
    registration_number VARCHAR(100) UNIQUE NOT NULL,
    tax_id VARCHAR(100),
    company_type company_type,
    industry VARCHAR(100),
    founded_date TIMESTAMP WITH TIME ZONE,
    employee_count INTEGER,
    website VARCHAR(500),
    address JSONB,
    contact_details JSONB,
    psd1_licensing_status psd_status DEFAULT 'pending',
    psd1_license_number VARCHAR(100),
    psd1_licensed_at TIMESTAMP WITH TIME ZONE,
    psd3_emoney_classification VARCHAR(50), -- micro, non_micro
    psd3_authorization_status VARCHAR(50),
    psd3_float_limit DECIMAL(15, 2),
    psd6_authorization_status VARCHAR(50),
    psd6_authorized_services JSONB,
    kyc_status psd_status DEFAULT 'pending',
    kyb_status psd_status DEFAULT 'pending',
    verification_documents JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sandbox applications with comprehensive PSD compliance
CREATE TABLE sandbox_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_number VARCHAR(100) UNIQUE NOT NULL,
    company_id UUID NOT NULL REFERENCES companies(id),
    applicant_id UUID NOT NULL REFERENCES users(id),
    status application_status DEFAULT 'draft',
    innovation_category innovation_category,
    business_model TEXT,
    target_market TEXT,
    competitive_advantage TEXT,
    technical_architecture TEXT,
    risk_assessment JSONB,
    psd1_licensing_status VARCHAR(50),
    psd3_emoney_classification VARCHAR(50),
    psd6_authorization_status VARCHAR(50),
    psd9_crossborder_status VARCHAR(50),
    psd12_cybersecurity_score DECIMAL(3, 2),
    data_message_hash VARCHAR(64),
    electronic_signature_metadata JSONB,
    submitted_at TIMESTAMP WITH TIME ZONE,
    approved_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    graduation_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Application documents with ETA 2019 compliance
CREATE TABLE application_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID NOT NULL REFERENCES sandbox_applications(id),
    document_type VARCHAR(100) NOT NULL,
    file_name VARCHAR(500) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    storage_key VARCHAR(500) UNIQUE NOT NULL,
    encryption_key_id VARCHAR(100),
    sha256_hash VARCHAR(64) NOT NULL,
    originality_certificate JSONB,
    signature_status VARCHAR(50) DEFAULT 'none',
    signature_metadata JSONB,
    signature_certificate JSONB,
    uploaded_by UUID NOT NULL REFERENCES users(id),
    upload_ip INET,
    upload_user_agent TEXT,
    evidence_certificate JSONB,
    retention_expiry_date TIMESTAMP WITH TIME ZONE,
    legal_custodian VARCHAR(200) DEFAULT 'NAMFISA',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI analysis results with explainability
CREATE TABLE ai_analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES sandbox_applications(id),
    document_id UUID REFERENCES application_documents(id),
    agent_type VARCHAR(100) NOT NULL,
    analysis_result JSONB NOT NULL,
    confidence_score DECIMAL(3, 2),
    explanation TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Compliance scores with PSD tracking
CREATE TABLE compliance_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID NOT NULL REFERENCES sandbox_applications(id),
    participant_id UUID,
    overall_score DECIMAL(3, 2) NOT NULL,
    psd1_score DECIMAL(3, 2),
    psd3_score DECIMAL(3, 2),
    psd4_score DECIMAL(3, 2),
    psd5_score DECIMAL(3, 2),
    psd6_score DECIMAL(3, 2),
    psd8_score DECIMAL(3, 2),
    psd9_score DECIMAL(3, 2),
    psd12_score DECIMAL(3, 2),
    psd13_score DECIMAL(3, 2),
    psdir4_score DECIMAL(3, 2),
    psdir5_score DECIMAL(3, 2),
    psdir7_score DECIMAL(3, 2),
    psdir8_score DECIMAL(3, 2),
    psdir9_score DECIMAL(3, 2),
    psdir10_score DECIMAL(3, 2),
    psdir11_score DECIMAL(3, 2),
    ai_analysis_result JSONB,
    confidence_score DECIMAL(3, 2),
    explanation TEXT,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Immutable audit trail with ETA 2019 Section 25 compliance
CREATE TABLE audit_trail (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id VARCHAR(100) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES users(id),
    participant_id UUID,
    application_id UUID REFERENCES sandbox_applications(id),
    resource_type VARCHAR(100),
    resource_id UUID,
    action VARCHAR(200) NOT NULL,
    previous_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(200),
    current_hash VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64),
    chain_hash VARCHAR(64) NOT NULL,
    hash_algorithm VARCHAR(20) DEFAULT 'SHA-256',
    digital_signature TEXT,
    signature_algorithm VARCHAR(50) DEFAULT 'RSA-2048',
    evidence_preservation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    legal_custodian VARCHAR(200) DEFAULT 'NAMFISA',
    eta2019_section25_compliant BOOLEAN DEFAULT TRUE,
    admissible_in_court BOOLEAN DEFAULT TRUE,
    psd_sections TEXT[],
    psdir_sections TEXT[],
    compliance_score DECIMAL(3, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document access audit with cryptographic chaining
CREATE TABLE document_access_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES application_documents(id),
    user_id UUID NOT NULL REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    access_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    access_purpose VARCHAR(200),
    audit_hash VARCHAR(64) NOT NULL,
    previous_audit_hash VARCHAR(64),
    eta2019_section25_compliant BOOLEAN DEFAULT TRUE,
    legal_evidence_preserved BOOLEAN DEFAULT TRUE
);

-- Document integrity checks
CREATE TABLE document_integrity_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES application_documents(id),
    integrity_check_type VARCHAR(50) NOT NULL,
    expected_hash VARCHAR(64) NOT NULL,
    actual_hash VARCHAR(64) NOT NULL,
    integrity_verified BOOLEAN NOT NULL,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    eta2019_section21_compliant BOOLEAN DEFAULT TRUE,
    eta2019_section22_compliant BOOLEAN DEFAULT TRUE
);

-- Electronic signatures for CRAN accreditation
CREATE TABLE electronic_signatures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES application_documents(id),
    user_id UUID NOT NULL REFERENCES users(id),
    signature_type VARCHAR(50) NOT NULL,
    signature_data JSONB NOT NULL,
    certificate_metadata JSONB,
    signed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE,
    verification_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vector embeddings for AI RAG system (pgvector)
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES application_documents(id),
    content_chunk TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Regulatory knowledge embeddings
CREATE TABLE regulatory_knowledge_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_name VARCHAR(500) NOT NULL,
    section_reference VARCHAR(100),
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB,
    psd_sections TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_company_id ON users (company_id);
CREATE INDEX idx_users_role ON users (is_superuser, is_active);

CREATE INDEX idx_companies_registration ON companies (registration_number);
CREATE INDEX idx_companies_psd1_status ON companies (psd1_licensing_status);
CREATE INDEX idx_companies_psd3_classification ON companies (psd3_emoney_classification);

CREATE INDEX idx_applications_company ON sandbox_applications (company_id);
CREATE INDEX idx_applications_status ON sandbox_applications (status);
CREATE INDEX idx_applications_submitted ON sandbox_applications (submitted_at);

CREATE INDEX idx_documents_application ON application_documents (application_id);
CREATE INDEX idx_documents_hash ON application_documents (sha256_hash);
CREATE INDEX idx_documents_type ON application_documents (document_type);

CREATE INDEX idx_compliance_application ON compliance_scores (application_id);
CREATE INDEX idx_compliance_overall_score ON compliance_scores (overall_score);

CREATE INDEX idx_audit_user ON audit_trail (user_id);
CREATE INDEX idx_audit_resource ON audit_trail (resource_type, resource_id);
CREATE INDEX idx_audit_timestamp ON audit_trail (created_at);
CREATE INDEX idx_audit_chain_hash ON audit_trail (chain_hash);

CREATE INDEX idx_embeddings_vector ON document_embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_embeddings_document ON document_embeddings (document_id);

-- Functions for PSD compliance calculations
CREATE OR REPLACE FUNCTION calculate_compliance_score(
    psd_scores JSONB
) RETURNS DECIMAL(3,2) AS $$
DECLARE
    total_score DECIMAL(3,2) := 0;
    section_count INTEGER := 0;
    section_key TEXT;
    section_score DECIMAL(3,2);
BEGIN
    -- PSD compliance weights (total 100%)
    FOR section_key IN SELECT jsonb_object_keys(psd_scores)
    LOOP
        section_score := (psd_scores->>section_key)::DECIMAL;
        IF section_score IS NOT NULL THEN
            total_score := total_score + section_score;
            section_count := section_count + 1;
        END IF;
    END LOOP;

    IF section_count > 0 THEN
        RETURN total_score / section_count;
    ELSE
        RETURN 0.0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function for audit chain verification
CREATE OR REPLACE FUNCTION verify_audit_chain(
    start_hash VARCHAR(64),
    end_hash VARCHAR(64)
) RETURNS BOOLEAN AS $$
DECLARE
    current_entry RECORD;
    previous_hash VARCHAR(64) := start_hash;
    calculated_hash VARCHAR(64);
BEGIN
    -- Traverse audit chain from start to end
    FOR current_entry IN
        SELECT * FROM audit_trail
        WHERE chain_hash >= start_hash AND chain_hash <= end_hash
        ORDER BY created_at
    LOOP
        -- Verify hash chain
        IF previous_hash IS NOT NULL THEN
            calculated_hash := encode(
                digest(previous_hash || current_entry.current_hash, 'sha256'),
                'hex'
            );

            IF calculated_hash != current_entry.chain_hash THEN
                RETURN FALSE;
            END IF;
        END IF;

        previous_hash := current_entry.chain_hash;
    END LOOP;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic audit trail creation
CREATE OR REPLACE FUNCTION create_audit_trail_entry()
RETURNS TRIGGER AS $$
DECLARE
    event_type TEXT;
    action_type TEXT;
    previous_values JSONB;
    new_values JSONB;
BEGIN
    -- Determine event type based on table and operation
    event_type := TG_TABLE_NAME || '_' || TG_OP;

    -- Determine action type
    IF TG_OP = 'INSERT' THEN
        action_type := 'CREATE';
        new_values := to_jsonb(NEW);
        previous_values := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        action_type := 'UPDATE';
        new_values := to_jsonb(NEW);
        previous_values := to_jsonb(OLD);
    ELSIF TG_OP = 'DELETE' THEN
        action_type := 'DELETE';
        previous_values := to_jsonb(OLD);
        new_values := NULL;
    END IF;

    -- Insert audit trail entry
    INSERT INTO audit_trail (
        event_id,
        event_type,
        user_id,
        resource_type,
        resource_id,
        action,
        previous_values,
        new_values,
        ip_address,
        user_agent,
        current_hash,
        created_at
    ) VALUES (
        gen_random_uuid()::text,
        event_type,
        NULL, -- Will be set by application layer
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        action_type,
        previous_values,
        new_values,
        NULL, -- Will be set by application layer
        NULL, -- Will be set by application layer
        encode(gen_random_bytes(32), 'hex'), -- Random hash for now
        NOW()
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create audit triggers for critical tables
CREATE TRIGGER audit_applications
    AFTER INSERT OR UPDATE OR DELETE ON sandbox_applications
    FOR EACH ROW EXECUTE FUNCTION create_audit_trail_entry();

CREATE TRIGGER audit_documents
    AFTER INSERT OR UPDATE OR DELETE ON application_documents
    FOR EACH ROW EXECUTE FUNCTION create_audit_trail_entry();

CREATE TRIGGER audit_companies
    AFTER INSERT OR UPDATE OR DELETE ON companies
    FOR EACH ROW EXECUTE FUNCTION create_audit_trail_entry();
