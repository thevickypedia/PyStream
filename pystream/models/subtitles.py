import pathlib


async def srt_to_vtt(filename: pathlib.PosixPath) -> None:
    """Convert a .srt file to .vtt for subtitles to be compatible with video-js.

    Args:
        filename: Name of the srt file.
    """
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
