import os
import wave
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CORE_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
GPT_SOVITS_DIR = Path(os.getenv("GPT_SOVITS_DIR", BACKEND_DIR / "GPT-sovits")).resolve()

def _load_dotenv(dotenv_path):
    path = Path(dotenv_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if value and len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


_load_dotenv(PROJECT_ROOT / ".env")

OPENAI_COMPAT_API_KEY = os.getenv("OPENAI_COMPAT_API_KEY", "")
OPENAI_COMPAT_BASE_URL = os.getenv("OPENAI_COMPAT_BASE_URL", "http://127.0.0.1:7861/")
OPENAI_COMPAT_MODEL = os.getenv("OPENAI_COMPAT_MODEL", "gemini-3-flash-preview")
# OPENAI_COMPAT_MODEL = os.getenv("OPENAI_COMPAT_MODEL", "gemini-3.1-pro-preview")

TTS_API_URL = os.getenv("TTS_API_URL", "http://127.0.0.1:9880")
TTS_ACTIVE_VOICE = os.getenv("TTS_ACTIVE_VOICE", "cyrene_intro")
TTS_SAMPLE_STEPS = int(os.getenv("TTS_SAMPLE_STEPS", "16"))
TTS_PARALLEL_INFER = os.getenv("TTS_PARALLEL_INFER", "true").lower() == "true"
TTS_BATCH_SIZE = int(os.getenv("TTS_BATCH_SIZE", "1"))
TTS_BATCH_THRESHOLD = float(os.getenv("TTS_BATCH_THRESHOLD", "0.75"))
DEFAULT_TTS_TEXT_LANG = os.getenv("TTS_TEXT_LANG", "zh")
DEFAULT_TTS_PROMPT_LANG = os.getenv("TTS_PROMPT_LANG", "zh")
MIN_REF_AUDIO_SECONDS = float(os.getenv("TTS_MIN_REF_AUDIO_SECONDS", "3"))
MAX_REF_AUDIO_SECONDS = float(os.getenv("TTS_MAX_REF_AUDIO_SECONDS", "10"))


def resolve_project_path(path_value, base_dir=BACKEND_DIR):
    if not path_value:
        return None

    path = Path(path_value)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return str(path)


def _discover_first_file(patterns):
    for pattern in patterns:
        matches = sorted(GPT_SOVITS_DIR.glob(pattern))
        if matches:
            return str(matches[0].resolve())
    return None


def _get_wav_duration_seconds(file_path):
    try:
        with wave.open(str(file_path), "rb") as wav_file:
            return wav_file.getnframes() / float(wav_file.getframerate())
    except (OSError, EOFError, wave.Error):
        return None


def is_reference_audio_duration_valid(file_path, min_seconds=MIN_REF_AUDIO_SECONDS, max_seconds=MAX_REF_AUDIO_SECONDS):
    duration = _get_wav_duration_seconds(file_path)
    if duration is None:
        return False
    return min_seconds <= duration <= max_seconds


def resolve_reference_audio_path(voice_config):
    preferred_paths = []

    direct_path = voice_config.get("ref_audio_path")
    if direct_path:
        preferred_paths.append(direct_path)

    preferred_paths.extend(voice_config.get("ref_audio_candidates", []))

    for candidate in preferred_paths:
        resolved_candidate = resolve_project_path(candidate)
        if resolved_candidate and is_reference_audio_duration_valid(resolved_candidate):
            return resolved_candidate

    for pattern in voice_config.get("ref_audio_glob", []):
        for match in sorted(BACKEND_DIR.glob(pattern)):
            resolved_match = str(match.resolve())
            if is_reference_audio_duration_valid(resolved_match):
                return resolved_match

    for candidate in preferred_paths:
        resolved_candidate = resolve_project_path(candidate)
        if resolved_candidate:
            return resolved_candidate

    return None


def _read_prompt_text_file(file_path):
    try:
        return Path(file_path).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def infer_prompt_text_from_reference_audio(ref_audio_path, fallback_text=""):
    if not ref_audio_path:
        return fallback_text

    audio_path = Path(ref_audio_path)
    lab_path = audio_path.with_suffix(".lab")
    if lab_path.exists():
        prompt_text = _read_prompt_text_file(lab_path)
        if prompt_text:
            return prompt_text

    stem = audio_path.stem.strip()
    if "-" in stem:
        _, filename_prompt = stem.split("-", 1)
        filename_prompt = filename_prompt.strip()
        if filename_prompt:
            return filename_prompt

    return fallback_text


def _gpt_weight_globs(*keywords):
    patterns = [f"GPT_weights*/*{keyword}*.ckpt" for keyword in keywords]
    patterns.append("GPT_weights*/*.ckpt")
    return patterns


def _sovits_weight_globs(*keywords):
    patterns = [f"SoVITS_weights*/*{keyword}*.pth" for keyword in keywords]
    patterns.append("SoVITS_weights*/*.pth")
    return patterns


TTS_VOICE_PRESETS = {
    "cyrene_intro": {
        "ref_audio_path": "GPT-sovits/reference_audio/Cyrene/archive_cyrene_11.wav",
        "ref_audio_candidates": [
            "GPT-sovits/reference_audio/Cyrene/archive_cyrene_11.wav",
            "GPT-sovits/reference_audio/Cyrene/archive_cyrene_2.wav",
            "GPT-sovits/reference_audio/Cyrene/chapter4_33_cyrenely_101.wav",
        ],
        "ref_audio_glob": ["GPT-sovits/reference_audio/Cyrene/*.wav"],
        "prompt_lang": DEFAULT_TTS_PROMPT_LANG,
        "text_lang": DEFAULT_TTS_TEXT_LANG,
        "gpt_weights_path": os.getenv("TTS_CYRENE_GPT_WEIGHTS_PATH", os.getenv("TTS_GPT_WEIGHTS_PATH")),
        "sovits_weights_path": os.getenv("TTS_CYRENE_SOVITS_WEIGHTS_PATH", os.getenv("TTS_SOVITS_WEIGHTS_PATH")),
        "gpt_weights_glob": _gpt_weight_globs("cyrene", "昔涟"),
        "sovits_weights_glob": _sovits_weight_globs("cyrene", "昔涟"),
    },
    "cyrene_dreamy": {
        "ref_audio_path": "GPT-sovits/reference_audio/Cyrene/chapter4_72_cyrene_119.wav",
        "ref_audio_candidates": [
            "GPT-sovits/reference_audio/Cyrene/chapter4_72_cyrene_119.wav",
            "GPT-sovits/reference_audio/Cyrene/chapter4_69_cyrene_159.wav",
            "GPT-sovits/reference_audio/Cyrene/chapter4_72_cyrene_288.wav",
        ],
        "ref_audio_glob": ["GPT-sovits/reference_audio/Cyrene/*.wav"],
        "prompt_lang": DEFAULT_TTS_PROMPT_LANG,
        "text_lang": DEFAULT_TTS_TEXT_LANG,
        "gpt_weights_path": os.getenv("TTS_CYRENE_GPT_WEIGHTS_PATH", os.getenv("TTS_GPT_WEIGHTS_PATH")),
        "sovits_weights_path": os.getenv("TTS_CYRENE_SOVITS_WEIGHTS_PATH", os.getenv("TTS_SOVITS_WEIGHTS_PATH")),
        "gpt_weights_glob": _gpt_weight_globs("cyrene", "昔涟"),
        "sovits_weights_glob": _sovits_weight_globs("cyrene", "昔涟"),
    },
    "cyrene_playful": {
        "ref_audio_path": "GPT-sovits/reference_audio/Cyrene/chapter4_72_cyrene_127.wav",
        "ref_audio_candidates": [
            "GPT-sovits/reference_audio/Cyrene/chapter4_72_cyrene_127.wav",
            "GPT-sovits/reference_audio/Cyrene/chapter4_52_cyrene_124.wav",
            "GPT-sovits/reference_audio/Cyrene/chapter4_72_cyrene_142.wav",
        ],
        "ref_audio_glob": ["GPT-sovits/reference_audio/Cyrene/*.wav"],
        "prompt_lang": DEFAULT_TTS_PROMPT_LANG,
        "text_lang": DEFAULT_TTS_TEXT_LANG,
        "gpt_weights_path": os.getenv("TTS_CYRENE_GPT_WEIGHTS_PATH", os.getenv("TTS_GPT_WEIGHTS_PATH")),
        "sovits_weights_path": os.getenv("TTS_CYRENE_SOVITS_WEIGHTS_PATH", os.getenv("TTS_SOVITS_WEIGHTS_PATH")),
        "gpt_weights_glob": _gpt_weight_globs("cyrene", "昔涟"),
        "sovits_weights_glob": _sovits_weight_globs("cyrene", "昔涟"),
    },
    "elysia": {
        "ref_audio_path": "GPT-sovits/reference_audio/Elysia/Ely1.wav",
        "prompt_text": os.getenv(
            "TTS_ELYSIA_PROMPT_TEXT",
            "那我想，芽衣一定也已经迫不及待了，對不對？好了，我们邊走邊說吧。",
        ),
        "prompt_lang": DEFAULT_TTS_PROMPT_LANG,
        "text_lang": DEFAULT_TTS_TEXT_LANG,
        "gpt_weights_path": os.getenv("TTS_ELYSIA_GPT_WEIGHTS_PATH", os.getenv("TTS_GPT_WEIGHTS_PATH")),
        "sovits_weights_path": os.getenv("TTS_ELYSIA_SOVITS_WEIGHTS_PATH", os.getenv("TTS_SOVITS_WEIGHTS_PATH")),
        "gpt_weights_glob": _gpt_weight_globs("elysia", "爱莉希雅"),
        "sovits_weights_glob": _sovits_weight_globs("elysia", "爱莉希雅"),
    },
    "firefly": {
        "ref_audio_path": "GPT-sovits/reference_audio/Firefly/firefly.wav",
        "prompt_text": os.getenv("TTS_FIREFLY_PROMPT_TEXT", ""),
        "prompt_lang": DEFAULT_TTS_PROMPT_LANG,
        "text_lang": DEFAULT_TTS_TEXT_LANG,
        "gpt_weights_path": os.getenv("TTS_FIREFLY_GPT_WEIGHTS_PATH", os.getenv("TTS_GPT_WEIGHTS_PATH")),
        "sovits_weights_path": os.getenv("TTS_FIREFLY_SOVITS_WEIGHTS_PATH", os.getenv("TTS_SOVITS_WEIGHTS_PATH")),
        "gpt_weights_glob": _gpt_weight_globs("firefly", "流萤"),
        "sovits_weights_glob": _sovits_weight_globs("firefly", "流萤"),
    },
    "sparkle_smug": {
        "ref_audio_path": "GPT-sovits/reference_audio/Sparkle/说话-可聪明的人从一开始就不会入局。你瞧，我是不是更聪明一点？.wav",
        "prompt_lang": DEFAULT_TTS_PROMPT_LANG,
        "text_lang": DEFAULT_TTS_TEXT_LANG,
        "gpt_weights_path": os.getenv("TTS_SPARKLE_GPT_WEIGHTS_PATH", os.getenv("TTS_GPT_WEIGHTS_PATH")),
        "sovits_weights_path": os.getenv("TTS_SPARKLE_SOVITS_WEIGHTS_PATH", os.getenv("TTS_SOVITS_WEIGHTS_PATH")),
        "gpt_weights_glob": _gpt_weight_globs("sparkle", "花火"),
        "sovits_weights_glob": _sovits_weight_globs("sparkle", "花火"),
    },
    "sparkle_teasing": {
        "ref_audio_path": "GPT-sovits/reference_audio/Sparkle/反问-你听起来很有把握嘛～显得你已经把家族那位鸡翅膀男孩搞定了似的。.wav",
        "prompt_lang": DEFAULT_TTS_PROMPT_LANG,
        "text_lang": DEFAULT_TTS_TEXT_LANG,
        "gpt_weights_path": os.getenv("TTS_SPARKLE_GPT_WEIGHTS_PATH", os.getenv("TTS_GPT_WEIGHTS_PATH")),
        "sovits_weights_path": os.getenv("TTS_SPARKLE_SOVITS_WEIGHTS_PATH", os.getenv("TTS_SOVITS_WEIGHTS_PATH")),
        "gpt_weights_glob": _gpt_weight_globs("sparkle", "花火"),
        "sovits_weights_glob": _sovits_weight_globs("sparkle", "花火"),
    },
    "sparkle_confused": {
        "ref_audio_path": "GPT-sovits/reference_audio/Sparkle/疑惑-当我没读过匹诺康尼历史么？别想把我卷进你们无聊的办公室政治。.wav",
        "prompt_lang": DEFAULT_TTS_PROMPT_LANG,
        "text_lang": DEFAULT_TTS_TEXT_LANG,
        "gpt_weights_path": os.getenv("TTS_SPARKLE_GPT_WEIGHTS_PATH", os.getenv("TTS_GPT_WEIGHTS_PATH")),
        "sovits_weights_path": os.getenv("TTS_SPARKLE_SOVITS_WEIGHTS_PATH", os.getenv("TTS_SOVITS_WEIGHTS_PATH")),
        "gpt_weights_glob": _gpt_weight_globs("sparkle", "花火"),
        "sovits_weights_glob": _sovits_weight_globs("sparkle", "花火"),
    },
}


def get_tts_voice_config(voice_name=None):
    selected_voice = voice_name or TTS_ACTIVE_VOICE
    voice_config = TTS_VOICE_PRESETS.get(selected_voice)
    if voice_config is None:
        available = ", ".join(sorted(TTS_VOICE_PRESETS)) or "<none>"
        raise KeyError(f"Unknown TTS voice preset '{selected_voice}'. Available presets: {available}")

    gpt_weights_path = resolve_project_path(voice_config.get("gpt_weights_path"))
    if not gpt_weights_path:
        gpt_weights_path = _discover_first_file(voice_config.get("gpt_weights_glob", []))

    sovits_weights_path = resolve_project_path(voice_config.get("sovits_weights_path"))
    if not sovits_weights_path:
        sovits_weights_path = _discover_first_file(voice_config.get("sovits_weights_glob", []))

    ref_audio_path = resolve_reference_audio_path(voice_config)
    prompt_text = infer_prompt_text_from_reference_audio(
        ref_audio_path,
        fallback_text=voice_config.get("prompt_text", ""),
    )

    return {
        "name": selected_voice,
        "api_url": voice_config.get("api_url", TTS_API_URL),
        "ref_audio_path": ref_audio_path,
        "prompt_text": prompt_text,
        "prompt_lang": voice_config.get("prompt_lang", "zh"),
        "text_lang": voice_config.get("text_lang", "zh"),
        "gpt_weights_path": gpt_weights_path,
        "sovits_weights_path": sovits_weights_path,
        "sample_steps": int(voice_config.get("sample_steps", TTS_SAMPLE_STEPS)),
        "parallel_infer": bool(voice_config.get("parallel_infer", TTS_PARALLEL_INFER)),
        "batch_size": int(voice_config.get("batch_size", TTS_BATCH_SIZE)),
        "batch_threshold": float(voice_config.get("batch_threshold", TTS_BATCH_THRESHOLD)),
    }
