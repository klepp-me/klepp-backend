import asyncio

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import yield_db_session
from app.api.security import cognito_scheme_or_anonymous
from app.models.klepp import ListResponse, Tag, TagRead

router = APIRouter()


@router.get('/tags', response_model=ListResponse[TagRead], dependencies=[Depends(cognito_scheme_or_anonymous)])
async def get_all_tags(
    session: AsyncSession = Depends(yield_db_session),
    offset: int = 0,
    limit: int = Query(default=100, lte=100),
) -> dict[str, int | list]:
    """
    Gets possible tags to use
    """
    # Video query
    tag_statement = select(Tag).order_by(desc(Tag.name))
    # Total count query based on query params, without pagination
    count_statement = select(func.count('*')).select_from(tag_statement)  # type: ignore

    # Add pagination
    tag_statement = tag_statement.offset(offset=offset).limit(limit=limit)
    # Do DB requests async
    tasks = [
        asyncio.create_task(session.exec(tag_statement)),  # type: ignore
        asyncio.create_task(session.exec(count_statement)),
    ]
    results, count = await asyncio.gather(*tasks)
    count_number = count.one_or_none()
    return {'total_count': count_number, 'response': results.all()}
