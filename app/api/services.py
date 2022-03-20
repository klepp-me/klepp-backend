import asyncio
import functools

import ffmpeg
from asynccpu import ProcessTaskPoolExecutor
from asyncffmpeg import FFmpegCoroutineFactory, StreamSpec


async def generate_thumbnail(url: str, name: str) -> StreamSpec:
    """
    Downloads from URL, cuts first frame and generates a new file
    """
    return ffmpeg.input(url).filter('scale', 420, -1).output(name, vframes=1)


async def await_ffmpeg(url: str, name: str) -> None:
    """
    Make ffmpeg awaitable
    """
    ffmpeg_coroutine = FFmpegCoroutineFactory.create()

    with ProcessTaskPoolExecutor(max_workers=3, cancel_tasks_when_shutdown=True) as executor:
        awaitables = (
            executor.create_process_task(ffmpeg_coroutine.execute, create_stream_spec)
            for create_stream_spec in [functools.partial(generate_thumbnail, url, name)]
        )
        await asyncio.gather(*awaitables)
