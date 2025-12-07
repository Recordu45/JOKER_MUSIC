# Joker/converter.py
"""
Audio converter for JOKER_MUSIC
Converts any supported audio input into:
 - raw 16-bit little endian
 - mono
 - 48000 Hz
"""

import asyncio
import os
from os import path
from Process.errors import FFmpegReturnCodeError


async def convert(file_path: str) -> str:
    """
    Convert input file to raw audio format for PyTgCalls.
    Returns output filepath (inside raw_files folder).
    """

    # Ensure output directory exists
    output_dir = "raw_files"
    os.makedirs(output_dir, exist_ok=True)

    # Generate output filename
    base = path.basename(file_path)
    name, _ = path.splitext(base)
    out_file = path.join(output_dir, f"{name}.raw")

    # If raw already exists → skip conversion
    if path.isfile(out_file):
        return out_file

    # Build ffmpeg command safely
    cmd = (
        f'ffmpeg -y -i "{file_path}" '
        "-f s16le "
        "-ac 1 "
        "-ar 48000 "
        "-acodec pcm_s16le "
        f'"{out_file}"'
    )

    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()
        return_code = process.returncode

        if return_code != 0:
            raise FFmpegReturnCodeError(
                returncode=return_code,
                cmd=cmd,
                stderr=stderr.decode(errors="ignore"),
                message=f"FFmpeg exited with code {return_code}"
            )

        return out_file

    except FFmpegReturnCodeError:
        raise  # rethrow with full metadata

    except Exception as e:
        raise FFmpegReturnCodeError(
            returncode=-1,
            cmd=cmd,
            stderr=str(e),
            message="Unexpected FFmpeg conversion failure"
        )
