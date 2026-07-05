# Project Elysia Structure For AI Context

This document is a condensed project tree for sharing with another AI model.
It intentionally omits noisy, generated, cached, or very large folders so the
other model can understand the architecture quickly.

## Scope And Omitted Content

Ignored or summarized on purpose:

- `.venv/`
- `__pycache__/`
- `.vscode/`, `.vs/`
- project-local `GPT-SoVITS` runtime/model contents
- large Unity asset/vendor/plugin content unless it helps explain the pipeline
- temporary files such as `temp_recording.wav`, `latest_transcription.txt`

## Condensed Tree

```text
Project-Elysia/
|-- .env.example                      # Environment template for LLM/backend config
|-- .gitattributes
|-- .gitignore
|-- LICENSE
|-- README.md                         # Human overview, setup, and end-to-end pipeline
|-- PROJECT_STRUCTURE_FOR_AI.md       # This file
|
|-- Backend/
|   |-- requirements.txt              # Python dependencies
|   |
|   |-- core/
|   |   |-- config.py                 # Shared runtime config, TTS presets, paths
|   |   |-- elysia_server.py          # Main WebSocket server; Unity <-> backend bridge
|   |   |-- llm_handler.py            # Calls LLM and parses structured character output
|   |   |-- speech_recognition.py     # STT via faster-whisper
|   |   |-- tts_handler.py            # TTS / GPT-SoVITS HTTP integration, streaming audio
|   |   |-- run.py                    # Alternate/local runner entry
|   |   |-- cyrene_character_card.json# Character/persona definition for prompting
|   |   `-- Ely1.wav                  # Reference/sample audio asset
|   |
|   |-- task/
|   |   |-- audit_reference_audio.py  # Utility to rank/reference voice clips
|   |   |-- unity_control.py          # Helper/control script related to Unity workflow
|   |   `-- audio_audit/
|   |       `-- cyrene/
|   |           |-- all_ranked.csv
|   |           |-- top_candidates.csv
|   |           |-- top_dreamy.csv
|   |           |-- top_intro.csv
|   |           `-- top_playful.csv
|   |
|   `-- third_party_setup/
|       `-- api_v2.bat                # Helper script to launch GPT-SoVITS API
|
`-- Frontend/
    |-- .vsconfig
    |
    |-- Assets/
    |   |-- Scenes/
    |   |   `-- SampleScene.unity     # Main Unity scene
    |   |
    |   |-- Script/
    |   |   |-- ConnectionManager.cs  # WebSocket client; sends mic data, receives events
    |   |   |-- StreamingAudioPlayer.cs # Plays streamed PCM audio chunks
    |   |   |-- ExpressionController.cs # Maps LLM expression tags to face states
    |   |   |-- GestureController.cs  # Maps LLM gesture tags to animation states
    |   |   |-- BlinkingController.cs
    |   |   |-- MoveController.cs
    |   |   |-- WavUtility.cs
    |   |   |-- AnimationClipExporter.cs
    |   |   |-- BlinkTest.cs
    |   |   `-- SmileTest.cs
    |   |
    |   |-- Animation/                # Idle/thinking/waving/etc. animation clips
    |   |-- UI/                       # UI assets such as icons
    |   |
    |   |-- WebSocket/                # NativeWebSocket library files
    |   |-- uLipSync/                 # Lip-sync assets/profiles
    |   |-- Plugins/                  # Third-party mocap/plugin content
    |   |-- TextMesh Pro/             # TMPro package assets
    |   |-- MMD4Mecanim/              # Third-party model/animation tooling
    |   `-- Elysia/                   # Character model/material/art content
    |
    |-- Packages/
    |   |-- manifest.json
    |   `-- packages-lock.json
    |
    |-- ProjectSettings/              # Unity project configuration
    `-- UserSettings/                 # Unity local editor settings
```

## End-To-End Pipeline Map

High-level data flow:

1. Unity records microphone audio in `Frontend/Assets/Script/ConnectionManager.cs`.
2. Unity sends audio to `Backend/core/elysia_server.py` over WebSocket.
3. `Backend/core/speech_recognition.py` transcribes speech to text.
4. `Backend/core/llm_handler.py` sends transcript + character card to the LLM.
5. The backend gets structured output like dialogue, expression, gesture, and internal thought.
6. `Backend/core/tts_handler.py` sends dialogue to GPT-SoVITS and receives streamed PCM audio.
7. `Backend/core/elysia_server.py` relays audio/events back to Unity.
8. `Frontend/Assets/Script/StreamingAudioPlayer.cs` plays the audio stream.
9. `ExpressionController.cs` and `GestureController.cs` drive character behavior.

## Best Files To Send Another AI

If you want another AI to explain the whole system, send these first:

- `README.md`
- `Backend/core/config.py`
- `Backend/core/elysia_server.py`
- `Backend/core/llm_handler.py`
- `Backend/core/speech_recognition.py`
- `Backend/core/tts_handler.py`
- `Frontend/Assets/Script/ConnectionManager.cs`
- `Frontend/Assets/Script/StreamingAudioPlayer.cs`
- `Frontend/Assets/Script/ExpressionController.cs`
- `Frontend/Assets/Script/GestureController.cs`

## Suggested Prompt To Another AI

You can paste this together with the files above:

```text
This is a Python backend + Unity frontend real-time AI character project.
Please use the attached project tree and source files to explain:
1. the architecture,
2. the end-to-end audio/text pipeline,
3. how Unity and the Python backend communicate,
4. how STT, LLM, and TTS are connected,
5. which files are the main extension points for new features.

Important: focus on the meaningful runtime code, not large Unity assets or third-party plugin content.
```
