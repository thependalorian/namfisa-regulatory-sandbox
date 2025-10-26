from typing import List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_async_session
from ..models import Application, Company, User
from ..schemas import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    CompanyCreate,
    CompanyRead,
    CompanyUpdate
)
from ..users import current_active_user

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("/", response_model=ApplicationRead)
async def create_application(
    application: ApplicationCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Create a new sandbox application"""
    # Check if company exists, create if not
    company_query = select(Company).filter(
        Company.registration_number == application.company_registration_number
    )
    company_result = await db.execute(company_query)
    company = company_result.scalars().first()

    if not company:
        # Create company
        company = Company(
            legal_name=application.company_legal_name,
            registration_number=application.company_registration_number,
            company_type=application.company_type,
            industry=application.industry,
            contact_details=application.contact_details,
        )
        db.add(company)
        await db.flush()  # Get the company ID

    # Create application
    db_application = Application(
        company_id=company.id,
        applicant_id=user.id,
        application_number=f"APP-{datetime.now().strftime('%Y%m%d')}-{company.id}",
        innovation_category=application.innovation_category,
        business_model=application.business_model,
        target_market=application.target_market,
        competitive_advantage=application.competitive_advantage,
        technical_architecture=application.technical_architecture,
        risk_assessment=application.risk_assessment,
    )

    db.add(db_application)
    await db.commit()
    await db.refresh(db_application)

    return ApplicationRead.model_validate(db_application)


@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(
    application_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Get application by ID"""
    query = select(Application).filter(
        Application.id == application_id,
        Application.applicant_id == user.id
    )
    result = await db.execute(query)
    application = result.scalars().first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or not authorized"
        )

    return ApplicationRead.model_validate(application)


@router.get("/", response_model=Page[ApplicationRead])
async def list_applications(
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
    page: int = 1,
    size: int = 10,
):
    """List user's applications with pagination"""
    params = Params(page=page, size=size)
    query = select(Application).filter(Application.applicant_id == user.id)
    return await apaginate(db, query, params, transformer=lambda apps: [ApplicationRead.model_validate(app) for app in apps])


@router.put("/{application_id}", response_model=ApplicationRead)
async def update_application(
    application_id: UUID,
    application_update: ApplicationUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Update application"""
    query = select(Application).filter(
        Application.id == application_id,
        Application.applicant_id == user.id
    )
    result = await db.execute(query)
    application = result.scalars().first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or not authorized"
        )

    # Update fields
    for field, value in application_update.model_dump(exclude_unset=True).items():
        setattr(application, field, value)

    await db.commit()
    await db.refresh(application)

    return ApplicationRead.model_validate(application)


@router.post("/{application_id}/submit")
async def submit_application(
    application_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Submit application for review"""
    query = select(Application).filter(
        Application.id == application_id,
        Application.applicant_id == user.id
    )
    result = await db.execute(query)
    application = result.scalars().first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or not authorized"
        )

    if application.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application can only be submitted from draft status"
        )

    # Update status to submitted
    application.status = "submitted"
    application.submitted_at = datetime.utcnow()

    await db.commit()

    return {"message": "Application submitted successfully", "application_id": application_id}


@router.get("/{application_id}/compliance", response_model=dict)
async def get_application_compliance(
    application_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Get application compliance status"""
    query = select(Application).filter(
        Application.id == application_id,
        Application.applicant_id == user.id
    )
    result = await db.execute(query)
    application = result.scalars().first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or not authorized"
        )

    compliance_status = {
        "application_id": application_id,
        "psd1_licensing_status": application.psd1_licensing_status,
        "psd3_emoney_classification": application.psd3_emoney_classification,
        "psd6_authorization_status": application.psd6_authorization_status,
        "psd9_crossborder_status": application.psd9_crossborder_status,
        "psd12_cybersecurity_score": application.psd12_cybersecurity_score,
        "overall_status": "pending"  # This would be calculated based on all PSD scores
    }

    return compliance_status
