from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import json
import logging
from datetime import datetime

# Import Pydantic AI and related libraries
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Import our custom modules
from .config import settings
from .database import get_async_session
from .models import Application, Document, ComplianceScore
from .schemas import (
    DocumentValidationRequest,
    DocumentValidationResponse,
    ApplicationTriageRequest,
    ApplicationTriageResponse,
    ComplianceAnalysisRequest,
    ComplianceAnalysisResponse
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="NAMFISA AI Orchestration Service",
    description="AI-powered document validation and compliance analysis for Bank of Namibia regulatory sandbox",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic AI Agents
class DocumentValidationAgent:
    """AI agent for PSD-compliant document validation"""

    def __init__(self):
        self.agent = Agent(
            'openai:gpt-4o',
            system_prompt="""
            You are a regulatory compliance expert specializing in Bank of Namibia
            Payment System Determinations (PSDs) and Directives (PSDIRs).

            Your role is to analyze fintech application documents and validate
            compliance with PSD-1, PSD-3, PSD-6, PSD-9, PSD-12 requirements.

            Provide detailed analysis with:
            - Compliance status for each PSD section
            - Confidence scores (0.0-1.0)
            - Specific recommendations for improvements
            - Risk flags for regulatory violations
            """
        )

    async def validate_document(
        self,
        document_content: str,
        document_type: str,
        psd_requirements: Dict[str, str]
    ) -> Dict[str, Any]:
        """Validate document against PSD requirements"""

        prompt = f"""
        Analyze this {document_type} document for PSD compliance:

        Document Content:
        {document_content}

        PSD Requirements to check:
        {json.dumps(psd_requirements, indent=2)}

        Provide analysis in JSON format with:
        - compliance_status: "compliant" | "non_compliant" | "partial"
        - confidence_score: 0.0-1.0
        - missing_sections: list of missing PSD sections
        - recommendations: list of improvement suggestions
        - risk_flags: list of potential regulatory risks
        - psd_sections_validated: list of validated PSD sections
        """

        try:
            result = await self.agent.run(prompt)
            return json.loads(result.content)
        except Exception as e:
            logger.error(f"Document validation failed: {e}")
            return {
                "compliance_status": "error",
                "confidence_score": 0.0,
                "error": str(e)
            }


class ApplicationTriageAgent:
    """AI agent for intelligent application triage and risk assessment"""

    def __init__(self):
        self.agent = Agent(
            'openai:gpt-4o',
            system_prompt="""
            You are a fintech regulatory expert responsible for triaging sandbox
            applications based on Bank of Namibia risk-based regulatory framework.

            Evaluate applications for:
            - PSD-1 licensing readiness
            - PSD-3 e-money compliance (March 2025 requirements)
            - PSD-12 cybersecurity posture
            - PSD-9 cross-border payment compliance
            - Overall innovation risk assessment

            Provide:
            - Risk score (0.0-1.0)
            - Priority classification (High/Medium/Low)
            - Reviewer assignment recommendations
            - Compliance gap analysis
            """
        )

    async def triage_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligent triage of sandbox applications"""

        prompt = f"""
        Analyze this fintech application for regulatory risk and triage:

        Application Data:
        {json.dumps(application_data, indent=2)}

        Evaluate against Bank of Namibia PSD requirements:
        - PSD-1: Licensing readiness
        - PSD-3: E-money compliance
        - PSD-4: Card payment systems
        - PSD-6: Authorization process
        - PSD-9: Cross-border payments
        - PSD-12: Cybersecurity

        Provide analysis in JSON format with:
        - risk_score: 0.0-1.0 (1.0 = highest risk)
        - priority: "HIGH" | "MEDIUM" | "LOW"
        - recommended_reviewers: list of expertise needed
        - compliance_gaps: list of PSD sections requiring attention
        - estimated_review_time: hours needed for review
        - immediate_flags: urgent compliance issues
        """

        try:
            result = await self.agent.run(prompt)
            return json.loads(result.content)
        except Exception as e:
            logger.error(f"Application triage failed: {e}")
            return {
                "risk_score": 1.0,
                "priority": "HIGH",
                "error": str(e)
            }


class ComplianceAnalysisAgent:
    """AI agent for comprehensive PSD compliance analysis"""

    def __init__(self):
        self.agent = Agent(
            'openai:gpt-4o',
            system_prompt="""
            You are a regulatory compliance analyst specializing in Bank of Namibia
            Payment System Determinations and Directives.

            Analyze applications for complete PSD compliance:
            - PSD-1: Licensing requirements
            - PSD-3: E-money issuer requirements
            - PSD-4: Card payment systems
            - PSD-5: Consumer protection
            - PSD-6: Authorization process
            - PSD-8: Administrative penalties
            - PSD-9: Cross-border payments
            - PSD-12: Cybersecurity
            - PSD-13: Systemic importance

            Provide actionable insights and recommendations.
            """
        )

    async def analyze_compliance(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive compliance analysis"""

        prompt = f"""
        Perform comprehensive PSD compliance analysis:

        Application Data:
        {json.dumps(application_data, indent=2)}

        Analyze against ALL Bank of Namibia PSD requirements:

        PSD-1: Licensing of Payment Service Providers
        PSD-3: E-money Service Provider Requirements
        PSD-4: Card Payment Systems
        PSD-5: Consumer Protection & Basic Accounts
        PSD-6: Payment Service Provider Authorization
        PSD-8: Administrative Penalties
        PSD-9: Cross-border Payment Transactions
        PSD-12: Cybersecurity and Operational Resilience
        PSD-13: Systemically Important Payment Systems

        Provide analysis in JSON format with:
        - overall_compliance_score: 0.0-1.0
        - psd_compliance_scores: dict of PSD section scores
        - critical_gaps: list of must-fix compliance issues
        - recommendations: prioritized improvement suggestions
        - risk_assessment: overall risk level
        - estimated_implementation_time: days to reach compliance
        """

        try:
            result = await self.agent.run(prompt)
            return json.loads(result.content)
        except Exception as e:
            logger.error(f"Compliance analysis failed: {e}")
            return {
                "overall_compliance_score": 0.0,
                "error": str(e)
            }


# LangGraph workflow for document validation
def create_document_validation_workflow():
    """Create LangGraph workflow for PSD-compliant document validation"""

    workflow = StateGraph(dict)

    async def extract_document_content(state):
        """Extract and preprocess document content"""
        documents = state.get('documents', [])
        processed_docs = []

        for doc in documents:
            # Extract text content (implement based on document type)
            content = await extract_text_from_document(doc)
            processed_docs.append({
                'id': doc.id,
                'type': doc.document_type,
                'content': content,
                'original': doc
            })

        return {**state, 'processed_documents': processed_docs}

    async def validate_psd_compliance(state):
        """Validate documents against PSD requirements"""
        validation_agent = DocumentValidationAgent()
        processed_docs = state.get('processed_documents', [])

        validation_results = []

        for doc in processed_docs:
            # Get PSD requirements for document type
            psd_requirements = get_psd_requirements_for_document_type(doc['type'])

            result = await validation_agent.validate_document(
                doc['content'],
                doc['type'],
                psd_requirements
            )
            validation_results.append({
                'document_id': doc['id'],
                'validation_result': result
            })

        return {**state, 'validation_results': validation_results}

    async def aggregate_validation_results(state):
        """Aggregate validation results and generate recommendations"""
        validation_results = state.get('validation_results', [])

        overall_score = calculate_overall_validation_score(validation_results)
        recommendations = generate_validation_recommendations(validation_results)

        return {
            **state,
            'overall_validation_score': overall_score,
            'recommendations': recommendations,
            'status': 'validation_complete'
        }

    # Add nodes
    workflow.add_node("extract_content", extract_document_content)
    workflow.add_node("validate_compliance", validate_psd_compliance)
    workflow.add_node("aggregate_results", aggregate_validation_results)

    # Define workflow edges
    workflow.set_entry_point("extract_content")
    workflow.add_edge("extract_content", "validate_compliance")
    workflow.add_edge("validate_compliance", "aggregate_results")
    workflow.add_edge("aggregate_results", END)

    return workflow.compile()


# API Routes
@app.post("/ai/validate-documents", response_model=DocumentValidationResponse)
async def validate_documents(request: DocumentValidationRequest):
    """AI-powered document validation for PSD compliance"""

    try:
        # Create validation workflow
        workflow = create_document_validation_workflow()

        # Prepare initial state
        initial_state = {
            'documents': request.documents,
            'psd_requirements': request.psd_requirements,
            'status': 'processing'
        }

        # Execute workflow
        result = await workflow.ainvoke(initial_state)

        return DocumentValidationResponse(
            validation_id=str(uuid.uuid4()),
            overall_score=result['overall_validation_score'],
            validation_results=result['validation_results'],
            recommendations=result['recommendations'],
            processing_time_ms=0,  # Calculate actual time
            created_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Document validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@app.post("/ai/triage-application", response_model=ApplicationTriageResponse)
async def triage_application(request: ApplicationTriageRequest):
    """AI-powered application triage and risk assessment"""

    try:
        triage_agent = ApplicationTriageAgent()

        # Perform triage analysis
        triage_result = await triage_agent.triage_application(request.application_data)

        return ApplicationTriageResponse(
            triage_id=str(uuid.uuid4()),
            risk_score=triage_result['risk_score'],
            priority=triage_result['priority'],
            recommended_reviewers=triage_result['recommended_reviewers'],
            compliance_gaps=triage_result['compliance_gaps'],
            estimated_review_time=triage_result['estimated_review_time'],
            immediate_flags=triage_result.get('immediate_flags', []),
            created_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Application triage failed: {e}")
        raise HTTPException(status_code=500, detail=f"Triage failed: {str(e)}")


@app.post("/ai/compliance-analysis", response_model=ComplianceAnalysisResponse)
async def analyze_compliance(request: ComplianceAnalysisRequest):
    """Comprehensive PSD compliance analysis"""

    try:
        compliance_agent = ComplianceAnalysisAgent()

        # Perform compliance analysis
        analysis_result = await compliance_agent.analyze_compliance(request.application_data)

        return ComplianceAnalysisResponse(
            analysis_id=str(uuid.uuid4()),
            overall_compliance_score=analysis_result['overall_compliance_score'],
            psd_compliance_scores=analysis_result.get('psd_compliance_scores', {}),
            critical_gaps=analysis_result.get('critical_gaps', []),
            recommendations=analysis_result.get('recommendations', []),
            risk_assessment=analysis_result.get('risk_assessment', {}),
            estimated_implementation_time=analysis_result.get('estimated_implementation_time', 0),
            created_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Compliance analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-orchestration-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {
        "status": "ready",
        "services": ["pydantic_ai", "langgraph", "openai"],
        "timestamp": datetime.utcnow().isoformat()
    }


# Utility functions
async def extract_text_from_document(document):
    """Extract text content from document"""
    # Implement based on document type (PDF, DOCX, etc.)
    # This is a placeholder implementation
    return f"Extracted content from {document.document_type}: {document.file_name}"


def get_psd_requirements_for_document_type(document_type: str) -> Dict[str, str]:
    """Get PSD requirements for specific document type"""
    requirements = {
        "business_plan": {
            "PSD-1": "Business model and licensing requirements",
            "PSD-3": "E-money business model compliance",
            "PSD-6": "Authorization requirements"
        },
        "financial_statements": {
            "PSD-1": "Financial capacity verification",
            "PSD-8": "Capital requirements compliance"
        },
        "security_assessment": {
            "PSD-12": "Cybersecurity and operational resilience"
        },
        "legal_opinion": {
            "PSD-1": "Legal compliance verification",
            "PSD-6": "Authorization legal basis"
        }
    }
    return requirements.get(document_type, {})


def calculate_overall_validation_score(validation_results: List[Dict]) -> float:
    """Calculate overall validation score from results"""
    if not validation_results:
        return 0.0

    scores = [result['validation_result']['confidence_score'] for result in validation_results]
    return sum(scores) / len(scores)


def generate_validation_recommendations(validation_results: List[Dict]) -> List[str]:
    """Generate recommendations from validation results"""
    recommendations = []

    for result in validation_results:
        validation = result['validation_result']
        if validation.get('recommendations'):
            recommendations.extend(validation['recommendations'])

    return list(set(recommendations))  # Remove duplicates


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
