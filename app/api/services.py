from typing import Callable, Optional

import ffmpeg
from asynccpu import ProcessTaskPoolExecutor
from asyncffmpeg import FFmpegCoroutineFactory, StreamSpec
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.klepp import Video, VideoRead


async def generate_user_thumbnail(path: str, name: str) -> StreamSpec:
    """
    Cuts first frame and generates a new file
    """
    return ffmpeg.input(path).filter('scale', 420, 420, force_original_aspect_ratio='decrease').output(name)


async def generate_video_thumbnail(path: str, name: str) -> StreamSpec:
    """
    Cuts first frame and generates a new file
    """
    return ffmpeg.input(path).filter('scale', 420, -1).output(name, vframes=1)


async def await_ffmpeg(function: Callable) -> None:
    """
    Make ffmpeg awaitable
    """
    ffmpeg_coroutine = FFmpegCoroutineFactory.create()

    with ProcessTaskPoolExecutor(max_workers=3, cancel_tasks_when_shutdown=True) as executor:
        await executor.create_process_task(ffmpeg_coroutine.execute, function)


async def fetch_one_or_none_video(video_path: str, db_session: AsyncSession) -> Optional[VideoRead]:
    """
    Takes a video path and fetches everything about it.
    """
    query_video = (
        select(Video)
        .where(Video.path == video_path)
        .options(selectinload(Video.user))
        .options(selectinload(Video.tags))
        .options(selectinload(Video.likes))
    )
    result = await db_session.exec(query_video)  # type: ignore
    return result.one_or_none()
