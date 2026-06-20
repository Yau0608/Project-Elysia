# Project Elysia

<div align="center">
  <video src="https://github.com/user-attachments/assets/98d98c72-10f7-4f97-b188-faf507eff20f" width="80%" autoplay loop muted playsinline>
  </video>
</div>

A real-time, voice-controlled AI character engine built in Python and Unity. This project integrates an OpenAI-compatible cloud LLM endpoint with local, high-performance STT/TTS systems to create a foundation for truly interactive and emotionally intelligent digital agents.

---

## About The Project

Project Elysia is the first step towards creating a truly interactive and emotionally intelligent digital character. Inspired by the dream of creating immersive virtual worlds, this project focuses on building the core "brain" and "voice" of an AI persona, rendered and controlled in real-time within the Unity game engine.

The system is designed to be a modular platform. While this version uses an OpenAI-compatible cloud LLM endpoint for conversational quality and flexibility, the architecture can easily be adapted to use local models for offline use. The current setup supports multiple TTS voice presets, including `elysia` and several `cyrene_*` profiles, with runtime switching through shared project config.

This project was a deep dive into the practical challenges of building an end-to-end AI application, from setting up a professional development environment with GPU acceleration to engineering a consistent and believable character persona through advanced prompt engineering and structured data formats.

## Core Features

*   **Real-time Voice Interaction:** A full pipeline from microphone input in Unity to a real-time, lip-synced voice response from the character.
*   **Advanced AI Persona:** Uses an OpenAI-compatible LLM endpoint with a rich, structured character card (W++ format) and JSON-mode style responses for consistent, high-quality, in-character dialogue.
*   **High-Quality Voice Cloning (TTS):** Integrates with a local **GPT-SoVITS** `api_v2.py` server and project-managed voice presets to generate expressive, human-like speech from custom-trained voice models.
*   **Config-Driven Voice Presets:** Shared TTS behavior now lives in `Backend/core/config.py`, including active voice selection, reference audio, prompt text, language settings, and GPT/SoVITS weight paths.
*   **High-Performance Speech-to-Text (STT):** Uses the `faster-whisper` library for fast and accurate transcription of user audio sent from Unity.
*   **Modular Architecture:** Built with a clean Python backend and a Unity frontend.
    *   **Python:** Object-Oriented design with separate handlers for the LLM, STT, and TTS. A WebSocket server (`elysia_server.py`) manages the real-time communication.
    *   **Unity (C#):** A component-based system with separate controllers for expressions, gestures, and UI management, allowing for easy expansion.

## How It Works

1.  The Unity client records audio from the user's microphone.
2.  The raw audio data is Base64 encoded and sent via a WebSocket connection to the Python backend.
3.  The `elysia_server.py` receives the data. The `SpeechRecognizer` class uses `faster-whisper` to transcribe the audio to text.
4.  The `LLMHandler` injects a detailed character card (`.json`) into a prompt and sends it to the configured OpenAI-compatible LLM endpoint, requesting a structured JSON response.
5.  The JSON response, containing dialogue, expression, and gesture, is received and parsed.
6.  The `TTSHandler` reloads the active voice preset from `Backend/core/config.py`, applies the configured GPT/SoVITS weights if needed, and sends the dialogue text to the local `GPT-SoVITS` server.
7.  In streaming mode, the backend forwards `tts_stream_start`, `tts_stream_chunk`, and `tts_stream_end` events to Unity, including audio metadata such as sample rate.
8.  Unity's `ConnectionManager` receives the events, displays the text, triggers the animations, and streams or plays back the returned audio.

## Getting Started

To get a local copy up and running, follow these steps.

### Prerequisites

*   **Python 3.9+** and a Conda environment.
*   **Unity Editor** (2022.x or newer).
*   **Git** and **Git LFS** (for handling large model files).
*   An **NVIDIA GPU** with CUDA Toolkit & cuDNN installed for STT acceleration.
*   An API key and base URL for your OpenAI-compatible LLM provider.
*   A running instance of the project-local **GPT-SoVITS `api_v2.py`** server with trained voice models available.

### Installation & Configuration

1.  Clone the repo (ensure you have Git LFS installed):
    ```sh
    git clone https://github.com/Yau0608/Project-Elysia.git
    ```
2.  Set up the Python environment using the provided `requirements.txt`:
    ```sh
    conda create --name elysia python=3.9
    conda activate elysia
    pip install -r requirements.txt
    ```
3.  Copy `.env.example` to `.env` and fill in your local LLM settings such as `OPENAI_COMPAT_API_KEY`, `OPENAI_COMPAT_BASE_URL`, and `OPENAI_COMPAT_MODEL`.
4.  Review `Backend/core/config.py` for shared TTS settings such as `TTS_ACTIVE_VOICE` and `TTS_VOICE_PRESETS`. This file is tracked in git and now owns the shared voice/model configuration.
5.  Open the Unity project folder and configure the `ConnectionManager` component with the correct scene references.

### Running the Application

1.  Start the project-local GPT-SoVITS server.
2.  Start the Elysia server:
    ```sh
    python core/elysia_server.py
    ```
3.  Press "Play" in the Unity Editor.
4.  To switch TTS voice/model settings, update `Backend/core/config.py`. Changes to the active preset are picked up on the next TTS request without restarting the Elysia backend.
5.  For best GPT-SoVITS results, use reference audio clips in the 3-10 second range. The helper script `Backend/task/audit_reference_audio.py` can be used to rank and shortlist good candidates.

## Future Development

The current version is a successful Minimum Viable Product (MVP). The next phase of development will focus on expanding the character's expressiveness and interactivity.

-   [ ] **Expand Expression & Gesture Library:** Create a wider range of facial expressions and body gestures in Unity and map them in the controllers.
-   [ ] **Implement Animation Intensity:** Refactor the animation controllers to use `float` parameters instead of `triggers`, allowing the LLM to control the *intensity* of expressions and gestures for more nuanced performances.
-   [ ] **(Experimental) MCP Integration:** Investigate migrating the communication layer to the Model Context Protocol (MCP) for deeper, stateful integration with the Unity client.

---