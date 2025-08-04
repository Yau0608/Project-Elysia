# Project Elysia

A voice-controlled AI character engine built in Python. Integrates local LLMs (Llama 3), TTS (GPT-SoVITS), and STT (Faster-Whisper) to power a real-time conversational agent for interactive applications.

---

## About The Project

Project Elysia is the first step towards creating a truly interactive and emotionally intelligent digital character. Inspired by the dream of creating immersive virtual worlds, this project focuses on building the core "brain" and "voice" of an AI persona.

The system is designed to be a modular platform for experimenting with different AI technologies. It currently uses a local large language model to generate responses for a character named "花火" (Sparkle), a mischievous and intelligent "Masked Fool."

This project was a deep dive into the practical challenges of building an end-to-end AI application, from setting up the development environment with GPU acceleration to engineering a stable character persona through carefully crafted system prompts.

## Core Features

*   **Real-time Voice Interaction:** Uses the microphone to listen for commands and responds with a synthesized voice.
*   **AI Character Persona:** Leverages a local LLM (Llama 3.1) with a detailed system prompt to create a consistent and engaging character.
*   **High-Quality Voice Cloning (TTS):** Integrates with GPT-SoVITS to generate expressive, human-like speech from a custom voice model.
*   **High-Performance Speech-to-Text (STT):** Uses the `faster-whisper` library for fast and accurate transcription on the local machine.
*   **Modular, Object-Oriented Design:** Built in Python with separate classes for each core component (`LLMHandler`, `TTSHandler`, `SpeechRecognizer`), making the system easy to extend and maintain.

## How It Works

The application follows a simple, robust pipeline:

1.  The `run.py` script initializes the system and listens for user input.
2.  The `SpeechRecognizer` class captures audio from the microphone and uses `faster-whisper` to transcribe it into text.
3.  The `LLMHandler` takes the text, packages it with a detailed system prompt, and sends it to a local Ollama server running Llama 3.1.
4.  The LLM's response, containing both conversational text and a command (e.g., `EXPRESSION:happy`), is received.
5.  The `TTSHandler` takes the full response, cleans the command part, and sends the conversational text to a `GPT-SoVITS` API server to generate audio, which is then played back.
6.  Simultaneously, the `LLMHandler` parses the command and sends it to a mock `UnityControl` module, simulating a change in the character's expression.

## Getting Started

To get a local copy up and running, follow these steps.

### Prerequisites

*   Python 3.9+ and Anaconda/Miniconda
*   Git
*   An NVIDIA GPU with CUDA Toolkit 12.x installed for GPU acceleration.
*   Running instances of the **Ollama** server (with `llama3.1`) and the **GPT-SoVITS** `api_v2.py` server.

### Installation

1.  Clone the repo:
    ```sh
    git clone https://github.com/your_username/Project-Elysia.git
    ```
2.  Create and activate a Conda environment:
    ```sh
    conda create --name elysia python=3.9
    conda activate elysia
    ```
3.  Install the required Python packages:
    *(You will need to create this file! See note below)*
    ```sh
    pip install -r requirements.txt
    ```

### Configuration

1.  Update the hard-coded file paths in `tts_handler.py` (`DEFAULT_REF_AUDIO`, etc.) to match your local setup.
2.  Ensure the API URLs in `tts_handler.py` and `llm_handler.py` point to your running servers.

### Running the Application

Execute the main script from the `core` directory:
```sh
python run.py
```

## Future Development

-   [ ] **Phase 1: Gemini Integration:** Upgrade the LLM from the local Llama 3.1 to the more powerful Google Gemini Pro API for enhanced conversational abilities.
-   [ ] **Phase 2: MCP Integration:** Re-architect the communication layer to use the Model Context Protocol (MCP) for deep, stateful integration with a Unity game engine client.

---
