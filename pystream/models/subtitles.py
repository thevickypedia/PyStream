import asyncio
import os
import pathlib


async def srt_to_vtt(filename: pathlib.PosixPath) -> None:
    """Convert a .srt file to .vtt for subtitles to be compatible with video-js.

    Args:
        filename: Name of the srt file.
    """
    assert filename.suffix == '.srt'
    output_file = filename.with_suffix('.vtt')
    with open(filename, 'r', encoding='utf-8') as rf:
        srt_content = rf.read()
    srt_content = srt_content.replace(',', '.')
    srt_content = srt_content.replace(' --> ', '-->')
    vtt_content = 'WEBVTT\n\n'
    subtitle_blocks = srt_content.strip().split('\n\n')
    for block in subtitle_blocks:
        lines = block.split('\n')
        timecode = lines[1]
        text = '\n'.join(lines[2:])
        vtt_content += f"{timecode}\n{text}\n\n"
    with open(output_file, 'w', encoding='utf-8') as wf:
        wf.write(vtt_content)


async def vtt_to_srt(filename: pathlib.PosixPath):
    """Convert a .vtt file to .srt for subtitles to be compatible with video-js.

    Args:
        filename: Name of the srt file.
    """
    assert filename.suffix == '.vtt'
    output_file = filename.with_suffix('.srt')
    with open(filename, 'r', encoding='utf-8') as f:
        vtt_content = f.read()
    vtt_content = vtt_content.replace('WEBVTT\n\n', '').replace('WEBVTT FILE\n\n', '')
    subtitle_blocks = vtt_content.strip().split('\n\n')
    subtitle_counter = 1
    srt_content = ''
    for block in subtitle_blocks:
        lines = block.split('\n')
        for idx, line in enumerate(lines):
            if '-->' in line:
                break
        else:
            raise RuntimeError
        text = '\n'.join(lines[idx+1:])
        srt_timecode = line if ' --> ' in line else line.replace('-->', ' --> ')
        srt_content += f"{subtitle_counter}\n{srt_timecode}\n{text}\n\n"
        subtitle_counter += 1
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(srt_content)


if __name__ == '__main__':
    path = os.path.expanduser('~/Desktop/Streaming/got/Season 2')
    for file in os.listdir(path):
        if file.endswith('.vtt'):
            sub_path = pathlib.PosixPath(os.path.join(path, file))
            asyncio.run(vtt_to_srt(sub_path))
            if os.path.exists(sub_path.with_suffix('.srt')):
                os.remove(sub_path)
