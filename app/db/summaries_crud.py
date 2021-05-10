from app.models.tortoise import TextSummary
from schemas.file import SummaryPayloadSchema


async def post(payload: SummaryPayloadSchema) -> int:
    """
    Creates a summary in the database
    """
    summary = TextSummary(
        url=payload.url,
        summary='dummy summary',
    )
    await summary.save()
    return summary.id
