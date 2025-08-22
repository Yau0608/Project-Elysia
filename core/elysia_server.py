import asyncio
import websockets
import json
import base64 #We will use this for sending audio to unity

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

async def handler(websocket):
    print("A client connected! (Unity)")
    try:
        # The server will not loop forever, waiting for messages from Unity
        async for message in websocket:
            # The message from Unity will now be a JSON string.
            data = json.loads(message)
            event_type = data.get("event")
            if event_type == "audio_data":
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

                # 3. Text-to-Speech
                print("Generating audio...")
                # We want the raw audio data, not to play it on the server
                audio_file_path = tts_handler.text_to_speech(dialogue, play_audio=False,clean_commands=False)

                if audio_file_path is None:
                    print("TTS failed. Sending response to Unity without audio.")
                    # We will still send a response, but the audio will be empty.
                    audio_data_base64 = ""
                else:
                    # If it succeeded, read the audio file and encode it.
                    with open(audio_file_path, "rb") as f:
                        audio_data = f.read()
                    audio_data_base64 = base64.b64encode(audio_data).decode('utf-8')

                # 4. Package the final response for Unity
                response_for_unity = {
                    "dialogue": dialogue,
                    "expression": expression,
                    "gesture": gesture,
                    "internal_thought_in_character": internal_thought_in_character,
                    "audio_base64": audio_data_base64
                }

                # 5. Send the complete package back to Unity
                await websocket.send(json.dumps(response_for_unity))
                print("Sent complete response to Unity.")
    
    except websockets.exceptions.ConnectionClosed:
        print("Clinet disconnected")

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("Project Elysia WebSocket server started at ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
