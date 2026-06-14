import argparse
import csv
import math
import re
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np


DEFAULT_MIN_SECONDS = 3.0
DEFAULT_MAX_SECONDS = 10.0
FRAME_MS = 20
MAX_INT16 = 32768.0


@dataclass
class PresetRule:
    name: str
    matcher: Callable[[str], bool]
    description: str


PRESET_RULES = [
    PresetRule(
        name="intro",
        matcher=lambda text: any(keyword in text for keyword in ("名为", "少女", "见到你", "烦恼", "烟消云散")),
        description="self-introduction / signature lines",
    ),
    PresetRule(
        name="dreamy",
        matcher=lambda text: any(token in text for token in ("……", "...", "星", "梦", "月", "夜", "轻", "静", "温柔")),
        description="soft / dreamy / airy delivery",
    ),
    PresetRule(
        name="playful",
        matcher=lambda text: any(token in text for token in ("♪", "~", "呀", "啦", "呢", "嘛", "哈", "呵", "!", "！", "?", "？")),
        description="playful / teasing / expressive delivery",
    ),
]


def read_wav_metrics(file_path: Path) -> dict:
    with wave.open(str(file_path), "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        frame_rate = wav_file.getframerate()
        frame_count = wav_file.getnframes()
        pcm_bytes = wav_file.readframes(frame_count)

    if sample_width != 2:
        raise ValueError(f"Unsupported sample width {sample_width * 8}bit in {file_path}")

    samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32)
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)

    normalized = samples / MAX_INT16
    abs_samples = np.abs(normalized)
    duration_seconds = len(normalized) / float(frame_rate) if frame_rate else 0.0

    rms = float(np.sqrt(np.mean(np.square(normalized)))) if len(normalized) else 0.0
    peak = float(np.max(abs_samples)) if len(abs_samples) else 0.0
    clipping_ratio = float(np.mean(abs_samples >= 0.995)) if len(abs_samples) else 0.0
    dc_offset = float(np.mean(normalized)) if len(normalized) else 0.0

    frame_size = max(1, int(frame_rate * FRAME_MS / 1000))
    if len(abs_samples):
        frame_count = math.ceil(len(abs_samples) / frame_size)
        padded = np.pad(abs_samples, (0, frame_count * frame_size - len(abs_samples)))
        framed = padded.reshape(frame_count, frame_size)
        frame_rms = np.sqrt(np.mean(np.square(framed), axis=1))
    else:
        frame_rms = np.array([], dtype=np.float32)

    silence_threshold = 0.01
    voiced_frames = frame_rms >= silence_threshold
    silence_ratio = 1.0 - float(np.mean(voiced_frames)) if len(voiced_frames) else 1.0
    leading_silence_ratio = _edge_silence_ratio(voiced_frames, from_start=True)
    trailing_silence_ratio = _edge_silence_ratio(voiced_frames, from_start=False)

    return {
        "sample_rate": frame_rate,
        "channels": channels,
        "duration_seconds": duration_seconds,
        "rms_dbfs": linear_to_dbfs(rms),
        "peak_dbfs": linear_to_dbfs(peak),
        "clipping_ratio": clipping_ratio,
        "silence_ratio": silence_ratio,
        "leading_silence_ratio": leading_silence_ratio,
        "trailing_silence_ratio": trailing_silence_ratio,
        "dc_offset": dc_offset,
    }


def _edge_silence_ratio(voiced_frames: np.ndarray, from_start: bool) -> float:
    if len(voiced_frames) == 0:
        return 1.0

    frame_iterable = voiced_frames if from_start else voiced_frames[::-1]
    silent_frames = 0
    for is_voiced in frame_iterable:
        if is_voiced:
            break
        silent_frames += 1
    return silent_frames / float(len(voiced_frames))


def linear_to_dbfs(value: float) -> float:
    if value <= 0.0:
        return -120.0
    return 20.0 * math.log10(value)


def read_transcript(wav_path: Path) -> str:
    lab_path = wav_path.with_suffix(".lab")
    if not lab_path.exists():
        return ""
    return lab_path.read_text(encoding="utf-8", errors="ignore").strip()


def classify_transcript_style(transcript: str) -> list[str]:
    styles = []
    for rule in PRESET_RULES:
        if rule.matcher(transcript):
            styles.append(rule.name)
    if not styles:
        styles.append("neutral")
    return styles


def score_clip(metrics: dict, transcript: str, min_seconds: float, max_seconds: float) -> tuple[float, list[str]]:
    score = 100.0
    flags = []
    duration = metrics["duration_seconds"]

    if duration < min_seconds:
        score -= 60
        flags.append("too_short")
    elif duration > max_seconds:
        score -= 60
        flags.append("too_long")
    elif 4.0 <= duration <= 8.5:
        score += 6

    if not transcript:
        score -= 12
        flags.append("missing_lab")
    elif len(transcript) < 8:
        score -= 10
        flags.append("short_transcript")
    elif len(transcript) > 80:
        score -= 4
        flags.append("long_transcript")

    rms_dbfs = metrics["rms_dbfs"]
    if rms_dbfs < -28:
        score -= 22
        flags.append("too_quiet")
    elif rms_dbfs < -24:
        score -= 10
        flags.append("quiet")
    elif -22 <= rms_dbfs <= -12:
        score += 8
    elif rms_dbfs > -6:
        score -= 15
        flags.append("too_loud")

    peak_dbfs = metrics["peak_dbfs"]
    if peak_dbfs < -10:
        score -= 10
        flags.append("low_peak")
    elif peak_dbfs > -1:
        score -= 6
        flags.append("near_full_scale")

    clipping_ratio = metrics["clipping_ratio"]
    if clipping_ratio > 0.01:
        score -= 30
        flags.append("heavy_clipping")
    elif clipping_ratio > 0.001:
        score -= 15
        flags.append("light_clipping")

    silence_ratio = metrics["silence_ratio"]
    if silence_ratio > 0.40:
        score -= 24
        flags.append("too_much_silence")
    elif silence_ratio > 0.25:
        score -= 10
        flags.append("silence_heavy")
    elif silence_ratio < 0.05:
        score += 3

    if metrics["leading_silence_ratio"] > 0.12:
        score -= 8
        flags.append("long_leading_silence")
    if metrics["trailing_silence_ratio"] > 0.12:
        score -= 8
        flags.append("long_trailing_silence")

    if abs(metrics["dc_offset"]) > 0.02:
        score -= 4
        flags.append("dc_offset")

    if any(symbol in transcript for symbol in ("♪", "~", "！", "？", "!", "?")):
        score += 2

    return round(max(score, 0.0), 2), flags


def audit_directory(input_dir: Path, output_dir: Path, min_seconds: float, max_seconds: float, top_n: int) -> dict:
    wav_files = sorted(input_dir.glob("*.wav"))
    rows = []

    for wav_path in wav_files:
        try:
            metrics = read_wav_metrics(wav_path)
            transcript = read_transcript(wav_path)
            styles = classify_transcript_style(transcript)
            score, flags = score_clip(metrics, transcript, min_seconds, max_seconds)
            rows.append(
                {
                    "file_name": wav_path.name,
                    "relative_path": wav_path.relative_to(input_dir.parent.parent).as_posix(),
                    "score": score,
                    "styles": ",".join(styles),
                    "flags": ",".join(flags),
                    "duration_seconds": round(metrics["duration_seconds"], 3),
                    "sample_rate": metrics["sample_rate"],
                    "channels": metrics["channels"],
                    "rms_dbfs": round(metrics["rms_dbfs"], 3),
                    "peak_dbfs": round(metrics["peak_dbfs"], 3),
                    "silence_ratio": round(metrics["silence_ratio"], 4),
                    "leading_silence_ratio": round(metrics["leading_silence_ratio"], 4),
                    "trailing_silence_ratio": round(metrics["trailing_silence_ratio"], 4),
                    "clipping_ratio": round(metrics["clipping_ratio"], 6),
                    "dc_offset": round(metrics["dc_offset"], 6),
                    "transcript_length": len(transcript),
                    "transcript": transcript,
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "file_name": wav_path.name,
                    "relative_path": wav_path.relative_to(input_dir.parent.parent).as_posix(),
                    "score": 0.0,
                    "styles": "error",
                    "flags": f"read_error:{type(exc).__name__}",
                    "duration_seconds": 0.0,
                    "sample_rate": 0,
                    "channels": 0,
                    "rms_dbfs": -120.0,
                    "peak_dbfs": -120.0,
                    "silence_ratio": 1.0,
                    "leading_silence_ratio": 1.0,
                    "trailing_silence_ratio": 1.0,
                    "clipping_ratio": 0.0,
                    "dc_offset": 0.0,
                    "transcript_length": 0,
                    "transcript": "",
                }
            )

    ranked_rows = sorted(rows, key=lambda row: (-row["score"], row["file_name"]))
    output_dir.mkdir(parents=True, exist_ok=True)

    write_csv(output_dir / "all_ranked.csv", ranked_rows)
    write_csv(output_dir / "top_candidates.csv", ranked_rows[:top_n])

    for rule in PRESET_RULES:
        style_rows = [row for row in ranked_rows if rule.name in row["styles"].split(",")]
        write_csv(output_dir / f"top_{rule.name}.csv", style_rows[:top_n])

    return {
        "total_files": len(wav_files),
        "ranked_rows": ranked_rows,
    }


def write_csv(file_path: Path, rows: list[dict]) -> None:
    fieldnames = [
        "file_name",
        "relative_path",
        "score",
        "styles",
        "flags",
        "duration_seconds",
        "sample_rate",
        "channels",
        "rms_dbfs",
        "peak_dbfs",
        "silence_ratio",
        "leading_silence_ratio",
        "trailing_silence_ratio",
        "clipping_ratio",
        "dc_offset",
        "transcript_length",
        "transcript",
    ]
    with file_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(results: dict) -> None:
    ranked_rows = results["ranked_rows"]
    valid_rows = [row for row in ranked_rows if "too_short" not in row["flags"] and "too_long" not in row["flags"]]
    good_rows = [row for row in ranked_rows if row["score"] >= 75]
    excellent_rows = [row for row in ranked_rows if row["score"] >= 85]

    print(f"Scanned {results['total_files']} wav files")
    print(f"Valid duration clips: {len(valid_rows)}")
    print(f"Good candidates (score >= 75): {len(good_rows)}")
    print(f"Excellent candidates (score >= 85): {len(excellent_rows)}")
    print("")
    print("Top 10 overall:")
    for row in ranked_rows[:10]:
        print(
            f"- {row['file_name']} | score={row['score']:.2f} | styles={row['styles']} | "
            f"duration={row['duration_seconds']:.2f}s | flags={row['flags'] or 'ok'}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit and rank GPT-SoVITS reference audio clips.")
    parser.add_argument(
        "--input-dir",
        default=r"c:\Users\Yau\Documents\YauProject\Project-Elysia\Backend\GPT-sovits\reference_audio\Cyrene",
        help="Directory containing wav/lab reference files.",
    )
    parser.add_argument(
        "--output-dir",
        default=r"c:\Users\Yau\Documents\YauProject\Project-Elysia\Backend\task\audio_audit\cyrene",
        help="Directory to store ranked CSV outputs.",
    )
    parser.add_argument("--min-seconds", type=float, default=DEFAULT_MIN_SECONDS)
    parser.add_argument("--max-seconds", type=float, default=DEFAULT_MAX_SECONDS)
    parser.add_argument("--top-n", type=int, default=50)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not input_dir.exists():
        print(f"Input directory does not exist: {input_dir}")
        return 1

    results = audit_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        min_seconds=args.min_seconds,
        max_seconds=args.max_seconds,
        top_n=args.top_n,
    )
    print_summary(results)
    print("")
    print(f"CSV outputs written to: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
