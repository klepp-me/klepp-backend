import logging

from fastapi import FastAPI
from tortoise import Tortoise, run_async
from tortoise.contrib.fastapi import register_tortoise

from core.config import settings

log = logging.getLogger('db_init')


def init_db(app: FastAPI) -> None:
    """
    Register tortoise, this happens on startup from main.
    """
    register_tortoise(
        app,
        db_url=settings.DATABASE_URL,
        modules={'models': ['app.models.tortoise']},
        generate_schemas=False,
        add_exception_handlers=True,
    )


async def generate_schema() -> None:
    """
    Generate tortoise schema. This has to be called manually.
    """
    log.info('Initializing Tortoise...')

    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={'models': ['models.tortoise']},
    )
    log.info('Generating database schema via Tortoise...')
    await Tortoise.generate_schemas()
    await Tortoise.close_connections()


if __name__ == '__main__':
    run_async(generate_schema())
