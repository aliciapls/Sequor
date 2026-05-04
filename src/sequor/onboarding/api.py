"""Onboarding API endpoint — handles signup form submissions.

Provides POST /api/v1/onboarding which validates input, creates
Tenant + Account + BackupContact records, and returns the result.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from sequor.db.database import get_engine
from sequor.onboarding.service import DuplicateEmailError, signup
from sequor.schemas import OnboardingRequest

logger = structlog.get_logger()


async def handle_signup(request_data: dict) -> dict:
    """Process an onboarding signup request.

    Accepts a dict of form data, validates via Pydantic, creates
    database records, and returns the result.

    Returns:
        {"status": "ok", "tenant_id": "...", "account_id": "...", "backup_contact_id": "..."}

    Raises:
        ValueError: on validation failure
        DuplicateEmailError: on duplicate owner email
    """
    logger.info("onboarding.signup.start", org_name=request_data.get("org_name"))

    # 1. Validate input
    req = OnboardingRequest(**request_data)

    # 2. Create records
    from sqlalchemy.ext.asyncio import AsyncSession as AS

    engine = get_engine()
    async with AsyncSession(engine) as session:
        result = await signup(session, req)

    logger.info(
        "onboarding.signup.ok",
        tenant_id=result["tenant_id"],
        account_id=result["account_id"],
    )

    return {"status": "ok", **result}
