from fastapi import APIRouter

from app.db import summaries_crud
from schemas.file import SummaryPayloadSchema, SummaryResponseSchema

router = APIRouter()


@router.post('/', response_model=SummaryResponseSchema, status_code=201)
async def create_summary(payload: SummaryPayloadSchema) -> SummaryResponseSchema:
    """
    Create a summary
    """
    summary_id = await summaries_crud.post(payload)
    return SummaryResponseSchema(**{'id': summary_id, 'url': payload.url})
