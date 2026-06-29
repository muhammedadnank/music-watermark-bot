"""
FFmpeg helper: applies watermarks to audio files.
Supports mix overlay and full-stop (mute music) for interval mode.
"""

import asyncio
import os
from config import JINGLE_PATH

SUPPORTED_EXTENSIONS = {".mp3", ".m4a"}


class WatermarkError(Exception):
    pass


def get_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def is_supported(filename: str) -> bool:
    return get_extension(filename) in SUPPORTED_EXTENSIONS


def _jingle_chain(label_in: str, label_out: str, fade_s: float, jingle_dur: float) -> str:
    """Build a filter chain for a single jingle copy: resample + fade."""
    chain = f"{label_in}aresample=44100,aformat=channel_layouts=stereo"
    if fade_s > 0:
        fade_out_st = max(0.0, jingle_dur - fade_s)
        chain += f",afade=t=in:st=0:d={fade_s},afade=t=out:st={fade_out_st}:d={fade_s}"
    return chain + label_out


def _build_mute_filter(intervals: list, jingle_dur: float, fade_s: float,
                        include_start_end: bool) -> str:
    """
    Build filter_complex for Full-Stop mode.
    Input 0 = jingle, Input 1 = main audio.

    If include_start_end=True:  start_jingle + [seg+jingle...] + seg_last + end_jingle
    If include_start_end=False: seg0 + jingle0 + seg1 + jingle1 + ... + seg_last
    """
    num_int = len(intervals)
    num_segs = num_int + 1
    filter_parts = []

    # --- Split main audio into num_segs copies for trimming ---
    ma_labels = "".join(f"[ma{i}]" for i in range(num_segs))
    filter_parts.append(f"[1:a]asplit={num_segs}{ma_labels}")

    # --- Split jingle into required copies ---
    extra = 2 if include_start_end else 0
    total_jingles = num_int + extra

    if total_jingles == 1:
        # Only one jingle needed, use stream directly
        filter_parts.append(_jingle_chain("[0:a]", "[jr0]", fade_s, jingle_dur))
    else:
        raw_labels = "".join(f"[jraw{i}]" for i in range(total_jingles))
        filter_parts.append(f"[0:a]asplit={total_jingles}{raw_labels}")
        for i in range(total_jingles):
            filter_parts.append(_jingle_chain(f"[jraw{i}]", f"[jr{i}]", fade_s, jingle_dur))

    # --- Trim main audio segments ---
    prev_end = 0.0
    for i, t in enumerate(intervals):
        filter_parts.append(
            f"[ma{i}]atrim=start={prev_end}:end={t},"
            f"asetpts=PTS-STARTPTS,aresample=44100,aformat=channel_layouts=stereo[seg{i}]"
        )
        prev_end = t + jingle_dur

    filter_parts.append(
        f"[ma{num_int}]atrim=start={prev_end},"
        f"asetpts=PTS-STARTPTS,aresample=44100,aformat=channel_layouts=stereo[seg_last]"
    )

    # --- Build concat list ---
    if include_start_end:
        # jr0 = start, jr1 = end, jr2..N = interval jingles
        concat = ["[jr0]"]  # start jingle
        for i in range(num_int):
            concat.append(f"[seg{i}]")
            concat.append(f"[jr{i + 2}]")  # interval jingles start at index 2
        concat.append("[seg_last]")
        concat.append("[jr1]")  # end jingle
    else:
        concat = []
        for i in range(num_int):
            concat.append(f"[seg{i}]")
            concat.append(f"[jr{i}]")
        concat.append("[seg_last]")

    n = len(concat)
    filter_parts.append("".join(concat) + f"concat=n={n}:v=0:a=1[out]")
    return ";".join(filter_parts)


async def add_watermark(input_path: str, output_path: str,
                        title: str = None, artist: str = None) -> None:
    """
    Adds watermarks to the audio file based on settings configuration.
    Modes: 'both', 'start_end', 'interval', 'none'.
    interval_mute_music=True → music fully stops during jingle (Full Stop mode).
    """
    from utils.settings_manager import load_settings
    from utils.metadata import get_audio_duration

    settings = load_settings()
    mode = settings.get("mode", "both")
    interval = int(settings.get("interval_seconds", 120))
    volume = float(settings.get("interval_volume", 0.7))
    fade_ms = int(settings.get("interval_fade_ms", 300))
    fade_s = fade_ms / 1000.0
    mute_music = bool(settings.get("interval_mute_music", False))

    # Resolve jingle path (custom upload takes priority over default)
    from config import JINGLE_PATH, CUSTOM_JINGLE_BASE
    jingle_path = JINGLE_PATH
    for ext in [".mp3", ".m4a"]:
        custom_path = f"{CUSTOM_JINGLE_BASE}{ext}"
        if os.path.exists(custom_path):
            jingle_path = custom_path
            break

    if mode != "none" and not os.path.exists(jingle_path):
        raise WatermarkError(
            f"Jingle file not found at '{jingle_path}'. Upload a custom one or check JINGLE_PATH."
        )

    jingle_dur = 0.0
    if mode != "none":
        jingle_dur = await get_audio_duration(jingle_path)

    out_ext = get_extension(output_path)
    if out_ext == ".mp3":
        codec_args = ["-c:a", "libmp3lame", "-q:a", "2"]
    elif out_ext == ".m4a":
        codec_args = ["-c:a", "aac", "-b:a", "192k"]
    else:
        raise WatermarkError(f"Unsupported output extension: {out_ext}")

    duration = await get_audio_duration(input_path)

    # Build interval timestamps
    intervals = []
    if mode in ("interval", "both") and interval > 0:
        t = interval
        while t < duration - 3:
            intervals.append(t)
            t += interval

    metadata_args = []
    if title:
        metadata_args += ["-metadata", f"title={title}"]
    if artist:
        metadata_args += ["-metadata", f"artist={artist}"]

    cmd = ["ffmpeg", "-y"]

    # ── NONE ──────────────────────────────────────────────────────────────────
    if mode == "none":
        cmd += [
            "-i", input_path,
            "-map_metadata", "0",
            *metadata_args,
            *codec_args,
            output_path
        ]

    # ── START_END ─────────────────────────────────────────────────────────────
    elif mode == "start_end":
        fc = (
            "[0:a]asplit=2[js0][je0];"
            "[js0]aresample=44100,aformat=channel_layouts=stereo[js];"
            "[1:a]aresample=44100,aformat=channel_layouts=stereo[main];"
            "[je0]aresample=44100,aformat=channel_layouts=stereo[je];"
            "[js][main][je]concat=n=3:v=0:a=1[out]"
        )
        cmd += [
            "-i", jingle_path, "-i", input_path,
            "-filter_complex", fc,
            "-map", "[out]", "-map_metadata", "1",
            *metadata_args, *codec_args, output_path
        ]

    # ── INTERVAL ──────────────────────────────────────────────────────────────
    elif mode == "interval":
        if not intervals:
            # Track too short — pass through with re-encode
            fc = "[0:a]aresample=44100,aformat=channel_layouts=stereo[out]"
            cmd += [
                "-i", input_path,
                "-filter_complex", fc,
                "-map", "[out]", "-map_metadata", "0",
                *metadata_args, *codec_args, output_path
            ]
        elif mute_music:
            # ── Full Stop: concat segments + jingles ──────────────────────────
            fc = _build_mute_filter(intervals, jingle_dur, fade_s,
                                    include_start_end=False)
            cmd += [
                "-i", jingle_path, "-i", input_path,
                "-filter_complex", fc,
                "-map", "[out]", "-map_metadata", "1",
                *metadata_args, *codec_args, output_path
            ]
        else:
            # ── Mix: amix overlay with volume + fade ──────────────────────────
            num_j = len(intervals)
            j_labels = "".join(f"[j{i}]" for i in range(num_j))
            fp = [f"[0:a]asplit={num_j}{j_labels}"]
            mix_in = ["[main]"]
            fade_out_st = max(0.0, jingle_dur - fade_s)
            for i, t in enumerate(intervals):
                fp.append(
                    f"[j{i}]aresample=44100,aformat=channel_layouts=stereo,"
                    f"afade=t=in:st=0:d={fade_s},"
                    f"afade=t=out:st={fade_out_st}:d={fade_s},"
                    f"volume={volume},adelay={t * 1000}:all=1[jd{i}]"
                )
                mix_in.append(f"[jd{i}]")
            fp.append("[1:a]aresample=44100,aformat=channel_layouts=stereo[main]")
            fp.append(
                "".join(mix_in) +
                f"amix=inputs={len(mix_in)}:duration=first:dropout_transition=0:normalize=0[out]"
            )
            cmd += [
                "-i", jingle_path, "-i", input_path,
                "-filter_complex", ";".join(fp),
                "-map", "[out]", "-map_metadata", "1",
                *metadata_args, *codec_args, output_path
            ]

    # ── BOTH ──────────────────────────────────────────────────────────────────
    elif mode == "both":
        num_int = len(intervals)

        if mute_music:
            # ── Full Stop: start_jingle + segments + end_jingle ───────────────
            if num_int == 0:
                # No interval jingles → simple 3-part concat
                fc = (
                    "[0:a]asplit=2[js0][je0];"
                    "[js0]aresample=44100,aformat=channel_layouts=stereo[js];"
                    "[1:a]aresample=44100,aformat=channel_layouts=stereo[main];"
                    "[je0]aresample=44100,aformat=channel_layouts=stereo[je];"
                    "[js][main][je]concat=n=3:v=0:a=1[out]"
                )
            else:
                fc = _build_mute_filter(intervals, jingle_dur, fade_s,
                                        include_start_end=True)
            cmd += [
                "-i", jingle_path, "-i", input_path,
                "-filter_complex", fc,
                "-map", "[out]", "-map_metadata", "1",
                *metadata_args, *codec_args, output_path
            ]
        else:
            # ── Mix: start/end concat + interval amix ─────────────────────────
            num_j = 2 + num_int
            js_je_j = "[js0][je0]" + "".join(f"[j{i}]" for i in range(num_int))
            fp = [f"[0:a]asplit={num_j}{js_je_j}"]
            fp.append("[js0]aresample=44100,aformat=channel_layouts=stereo[js]")
            fp.append("[je0]aresample=44100,aformat=channel_layouts=stereo[je]")
            fp.append("[1:a]aresample=44100,aformat=channel_layouts=stereo[main]")

            if num_int == 0:
                fp.append("[js][main][je]concat=n=3:v=0:a=1[out]")
            else:
                mix_in = ["[main]"]
                fade_out_st = max(0.0, jingle_dur - fade_s)
                for i, t in enumerate(intervals):
                    fp.append(
                        f"[j{i}]aresample=44100,aformat=channel_layouts=stereo,"
                        f"afade=t=in:st=0:d={fade_s},"
                        f"afade=t=out:st={fade_out_st}:d={fade_s},"
                        f"volume={volume},adelay={t * 1000}:all=1[jd{i}]"
                    )
                    mix_in.append(f"[jd{i}]")
                fp.append(
                    "".join(mix_in) +
                    f"amix=inputs={len(mix_in)}:duration=first:dropout_transition=0:normalize=0[mid]"
                )
                fp.append("[js][mid][je]concat=n=3:v=0:a=1[out]")

            cmd += [
                "-i", jingle_path, "-i", input_path,
                "-filter_complex", ";".join(fp),
                "-map", "[out]", "-map_metadata", "1",
                *metadata_args, *codec_args, output_path
            ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        raise WatermarkError(
            f"FFmpeg failed:\n{stderr.decode(errors='ignore')[-800:]}"
        )
