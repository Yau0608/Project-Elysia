# Project Elysia

![Project Elysia Demo](docs/demo.mp4)

A real-time, voice-controlled AI character engine built in Python and Unity. This project integrates a state-of-the-art cloud LLM (Google Gemini) with local, high-performance STT/TTS systems to create a foundation for truly interactive and emotionally intelligent digital agents.

---

## About The Project

Project Elysia is the first step towards creating a truly interactive and emotionally intelligent digital character. Inspired by the dream of creating immersive virtual worlds, this project focuses on building the core "brain" and "voice" of an AI persona, rendered and controlled in real-time within the Unity game engine.

The system is designed to be a modular platform. While this version uses the powerful Gemini Pro API for the best possible conversational quality, the architecture can easily be adapted to use local models like Llama for offline use. The current character persona is a custom-designed character named "昔涟" (Cyrene).

This project was a deep dive into the practical challenges of building an end-to-end AI application, from setting up a professional development environment with GPU acceleration to engineering a consistent and believable character persona through advanced prompt engineering and structured data formats.

## Core Features

*   **Real-time Voice Interaction:** A full pipeline from microphone input in Unity to a real-time, lip-synced voice response from the character.
*   **Advanced AI Persona:** Leverages **Google's Gemini Pro API** with a rich, structured character card (W++ format) and JSON Mode for consistent, high-quality, in-character responses.
*   **High-Quality Voice Cloning (TTS):** Integrates with a local **GPT-SoVITS** `api_v2.py` server to generate expressive, human-like speech from a custom-trained voice model.
*   **High-Performance Speech-to-Text (STT):** Uses the `faster-whisper` library for fast and accurate transcription of user audio sent from Unity.
*   **Modular Architecture:** Built with a clean Python backend and a Unity frontend.
    *   **Python:** Object-Oriented design with separate handlers for the LLM, STT, and TTS. A WebSocket server (`elysia_server.py`) manages the real-time communication.
    *   **Unity (C#):** A component-based system with separate controllers for expressions, gestures, and UI management, allowing for easy expansion.

## How It Works

1.  The Unity client records audio from the user's microphone.
2.  The raw audio data is Base64 encoded and sent via a WebSocket connection to the Python backend.
3.  The `elysia_server.py` receives the data. The `SpeechRecognizer` class uses `faster-whisper` to transcribe the audio to text.
4.  The `LLMHandler` injects a detailed character card (`.json`) into a prompt and sends it to the **Google Gemini API**, requesting a structured JSON response.
5.  The JSON response, containing dialogue, expression, and gesture, is received and parsed.
6.  The `TTSHandler` sends the dialogue text to a local `GPT-SoVITS` server to generate audio.
7.  The final, complete package (dialogue text, expression/gesture commands, and Base64 audio) is sent back to the Unity client.
8.  Unity's `ConnectionManager` receives the package, displays the text, triggers the animations, and plays the lip-synced audio.

## Getting Started

To get a local copy up and running, follow these steps.

### Prerequisites

*   **Python 3.9+** and a Conda environment.
*   **Unity Editor** (2022.x or newer).
*   **Git** and **Git LFS** (for handling large model files).
*   An **NVIDIA GPU** with CUDA Toolkit & cuDNN installed for STT acceleration.
*   A **Google Gemini API Key**.
*   A running instance of the **GPT-SoVITS `api_v2.py`** server with a trained voice model.

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
3.  Create a `config.py` file in the `core/` directory and add your Google Gemini API key:
    ```python
    # in core/config.py
    GEMINI_API_KEY = "YOUR_API_KEY_HERE"
    ```
4.  Open the Unity project folder and configure the `ConnectionManager` component with the correct scene references.

### Running the Application

1.  Start the GPT-SoVITS server.
2.  Start the Elysia server:
    ```sh
    python core/elysia_server.py
    ```
3.  Press "Play" in the Unity Editor.

## Future Development

The current version is a successful Minimum Viable Product (MVP). The next phase of development will focus on expanding the character's expressiveness and interactivity.

-   [ ] **Expand Expression & Gesture Library:** Create a wider range of facial expressions and body gestures in Unity and map them in the controllers.
-   [ ] **Implement Animation Intensity:** Refactor the animation controllers to use `float` parameters instead of `triggers`, allowing the LLM to control the *intensity* of expressions and gestures for more nuanced performances.
-   [ ] **(Experimental) MCP Integration:** Investigate migrating the communication layer to the Model Context Protocol (MCP) for deeper, stateful integration with the Unity client.

---