import asyncio
import websockets
import json
import base64 #We will use this for sending audio to unity
import time

# Import all tools that I build
from llm_handler import LLMHandler
from speech_recognition import SpeechRecognizer
from tts_handler import TTSHandler

# Initialize our components ONCE when the server starts
print("Initializing AI components...")
llm_handler = LLMHandler()
speech_recognizer = SpeechRecognizer()
tts_handler = TTSHandler()
print("AI components ready!")

async def send_streaming_tts(
    websocket,
    dialogue,
    expression,
    gesture,
    internal_thought_in_character
):
    await websocket.send(json.dumps({
        "event": "tts_stream_start",
        "dialogue": dialogue,
        "expression": expression,
        "gesture": gesture,
        "internal_thought_in_character": internal_thought_in_character,
        "sample_rate": 32000,
        "channels": 1,
        "sample_width": 2,
        "audio_format": "pcm_s16le",
    }))

    chunk_count = 0
    for chunk in tts_handler.text_to_speech_stream(
        dialogue,
        clean_commands=False,
        media_type="raw"
    ):
        await websocket.send(json.dumps({
            "event": "tts_stream_chunk",
            "seq": chunk_count,
            "audio_chunk_base64": base64.b64encode(chunk).decode('utf-8'),
        }))
        chunk_count += 1

    await websocket.send(json.dumps({
        "event": "tts_stream_end",
        "dialogue": dialogue,
        "expression": expression,
        "gesture": gesture,
        "internal_thought_in_character": internal_thought_in_character,
        "chunk_count": chunk_count,
    }))

async def handler(websocket):
    print("A client connected! (Unity)")
    try:
        # The server will not loop forever, waiting for messages from Unity
        async for message in websocket:
            # The message from Unity will now be a JSON string.
            data = json.loads(message)
            event_type = data.get("event")
            if event_type == "audio_data":
                request_started_at = time.perf_counter()
                stream_tts = data.get("stream_tts", False)
                full_audio_data = data.get("data", "")
                truncated_audio_data = full_audio_data[:80]

                print(f"Received audio_data event from Unity. Data begins with: {truncated_audio_data}...")
                audio_bytes = base64.b64decode(full_audio_data)

                # 1. Speech-to_Text (using our new recipe)
                transcribed_text = speech_recognizer.transcribe_audio_data(audio_bytes)
                print(f"Transcription: {transcribed_text}")
                # 2. LLM processing
                print("Sending text to LLM...")
                responses_json_string = llm_handler.send_prompt(transcribed_text)
                dialogue, expression, gesture, internal_thought_in_character = llm_handler.process_command_from_responses(responses_json_string)

                if stream_tts:
                    print("Generating streaming audio...")
                    await send_streaming_tts(
                        websocket,
                        dialogue,
                        expression,
                        gesture,
                        internal_thought_in_character
                    )
                else:
                    print("Generating audio...")
                    audio_data = tts_handler.text_to_speech(
                        dialogue,
                        play_audio=False,
                        clean_commands=False,
                        return_audio_data=True
                    )

                    if audio_data is None:
                        print("TTS failed. Sending response to Unity without audio.")
                        audio_data_base64 = ""
                    else:
                        audio_data_base64 = base64.b64encode(audio_data).decode('utf-8')

                    response_for_unity = {
                        "dialogue": dialogue,
                        "expression": expression,
                        "gesture": gesture,
                        "internal_thought_in_character": internal_thought_in_character,
                        "audio_base64": audio_data_base64
                    }
                    await websocket.send(json.dumps(response_for_unity))

                total_latency = time.perf_counter() - request_started_at
                print(f"Sent complete response to Unity. End-to-end latency: {total_latency:.2f}s")
    
    except websockets.exceptions.ConnectionClosed:
        print("Clinet disconnected")

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("Project Elysia WebSocket server started at ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
