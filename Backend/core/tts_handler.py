import requests
import os
import time
import pygame
import re
import glob
from io import BytesIO

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Hard-coded reference audio configuration
DEFAULT_REF_AUDIO = os.path.join(CURRENT_DIR, "Ely1.wav")

DEFAULT_PROMPT_TEXT = "那我想，芽衣一定也已经迫不及待了，對不對？好了，我们邊走邊說吧。"
DEFAULT_PROMPT_LANG = "zh"
DEFAULT_API_URL = "http://127.0.0.1:9880"
DEFAULT_TEXT_LANG = "zh"
DEFAULT_GPT_URL = "C:\\Users\\Yau\\Documents\\YauProject\\GPT-SoVITS-v2pro-20250604\\GPT_weights_v4\\爱莉希雅-e10.ckpt"
DEFAULT_SOVITS_URL = "C:\\Users\\Yau\\Documents\\YauProject\\GPT-SoVITS-v2pro-20250604\\SoVITS_weights_v4\\爱莉希雅_e10_s270_l32.pth"

class TTSHandler:
    """
    Text-to-Speech handler using GPT-SoVITS API
    
    This class manages text-to-speech conversion and playback using the GPT-SoVITS API.
    It sends text to the API, receives audio data, and plays it locally.
    """
    
    def __init__(self, api_url=DEFAULT_API_URL, gpt_url=DEFAULT_GPT_URL, sovits_url=DEFAULT_SOVITS_URL, debug_mode=False):
        self.api_url = api_url
        self.gpt_url = gpt_url
        self.sovits_url = sovits_url
        self.debug_mode = debug_mode
        self.audio_dir = os.path.join(os.path.dirname(__file__), "temp")
        self.latest_output_file = os.path.join(self.audio_dir, "latest_tts_output.wav")
        self.session = requests.Session()
        self.request_timeout = 120
        self.active_gpt_url = None
        self.active_sovits_url = None
        self.sample_steps = 16
        self.parallel_infer = True
        self.batch_size = 1
        self.batch_threshold = 0.75
        
        # Default reference audio configuration - use the hard-coded values
        self.default_ref_audio = DEFAULT_REF_AUDIO
        self.default_prompt_text = DEFAULT_PROMPT_TEXT
        self.default_prompt_lang = DEFAULT_PROMPT_LANG
        self.default_text_lang = DEFAULT_TEXT_LANG
        
        # Create the audio directory if it doesn't exist
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
        
        # Clean up old TTS output files
        self._cleanup_old_tts_files()
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
        
        print(f"TTS Handler initialized with API URL: {api_url}")
        print(f"Using reference audio: {self.default_ref_audio}")

    def _set_gpt_weights(self):
        gpt_endpoint_url = f"{self.api_url}/set_gpt_weights"
        gpt_params = {"weights_path": self.gpt_url}
        self.log(f"Sending GET request to change GPT model: {gpt_endpoint_url}")
        gpt_response = self.session.get(gpt_endpoint_url, params=gpt_params, timeout=self.request_timeout)
        if gpt_response.status_code != 200:
            print(f"Error setting GPT weights: {gpt_response.text}")
            return False
        self.active_gpt_url = self.gpt_url
        return True

    def _set_sovits_weights(self):
        sovits_endpoint_url = f"{self.api_url}/set_sovits_weights"
        sovits_params = {"weights_path": self.sovits_url}
        self.log(f"Sending GET request to change SoVITS model: {sovits_endpoint_url}")
        sovits_response = self.session.get(sovits_endpoint_url, params=sovits_params, timeout=self.request_timeout)
        if sovits_response.status_code != 200:
            print(f"Error setting SoVITS weights: {sovits_response.text}")
            return False
        self.active_sovits_url = self.sovits_url
        return True

    def _ensure_weights_loaded(self):
        if self.active_gpt_url != self.gpt_url:
            if not self._set_gpt_weights():
                return False
        if self.active_sovits_url != self.sovits_url:
            if not self._set_sovits_weights():
                return False
        return True

    def _build_tts_payload(self, speech_text, streaming_mode=False, media_type="wav"):
        return {
            "text": speech_text,
            "text_lang": self.default_text_lang,
            "ref_audio_path": self.default_ref_audio,
            "prompt_text": self.default_prompt_text,
            "prompt_lang": self.default_prompt_lang,
            "text_split_method": "cut5",
            "sample_steps": self.sample_steps,
            "parallel_infer": self.parallel_infer,
            "batch_size": self.batch_size,
            "batch_threshold": self.batch_threshold,
            "streaming_mode": streaming_mode,
            "media_type": media_type,
        }
    
    def _cleanup_old_tts_files(self):
        """Clean up old TTS output files from previous runs"""
        try:
            # Find all tts_output_*.wav files
            old_files = glob.glob(os.path.join(self.audio_dir, "tts_output_*.wav"))
            
            # Delete them
            for file in old_files:
                os.remove(file)
        except Exception as e:
            self.log(f"Error cleaning up old TTS files: {e}")
    
    def log(self, message):
        """Print debug messages only if debug mode is enabled"""
        if self.debug_mode:
            print(f"TTS DEBUG: {message}")

    def set_default_reference(self, ref_audio_path, prompt_text, prompt_lang, text_lang):

        self.default_ref_audio = ref_audio_path
        self.default_prompt_text = prompt_text
        self.default_prompt_lang = prompt_lang
        self.default_text_lang = text_lang
        self.log(f"Default reference set: {ref_audio_path}, '{prompt_text}' ({prompt_lang})")
  
    def clean_for_speech(self, text):
        if not text:
            return ""
            
        # Store the original text for comparison
        original_text = text #remove
        
        # Remove LIGHT commands with all parameters (handles multiple commands)
        text = re.sub(r'LIGHT:[\w]+:(ON|OFF)(:[\w]+=[\w\d,]+)*', '', text, flags=re.IGNORECASE)
        
        # Remove TV commands
        text = re.sub(r'TV:(ON|OFF)', '', text, flags=re.IGNORECASE)
        
        # Remove STATUS commands
        text = re.sub(r'STATUS:[^\s]*', '', text, flags=re.IGNORECASE)

        # Rmove EXPRESSION commands
        text = re.sub(r'EXPRESSION:[^\s]*', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s+$', '', text).strip()
        
        # Log if there were any changes
        if text != original_text and self.debug_mode:
            self.log(f"Cleaned text for speech:\nBEFORE: {original_text}\nAFTER: {text}")
        
        return text
    
    def text_to_speech(self, text, play_audio=True, clean_commands=True, return_audio_data=False):
        """
        Convert text to speech using the new GPT-SoVITS api_v2.py.
        This version uses a POST request with a JSON payload.
        """    
        try:


            if not self._ensure_weights_loaded():
                return None

            # First, clean the text if requested, so we don't send commands to the API.
            if clean_commands:
                speech_text = self.clean_for_speech(text)
                if not speech_text:
                    print("WARNING: Text is empty after cleaning commands")
                    return None
            else:
                speech_text = text

            # THe new API endpoint is /tts
            url = f"{self.api_url}/tts"

            # The new API requires the reference audio with every call.
            # We will use the default values we stored in our object.
            # This dictionary structure matches the TTS_Request model in api_v2.py.            
            # Construct the URL with query parameters
            params = self._build_tts_payload(speech_text=speech_text, streaming_mode=False, media_type="wav")
            
            self.log(f"Sending POST request to: {url} with params: {params}")
            
            response = self.session.post(url, json=params, timeout=self.request_timeout)
            
            if response.status_code != 200:
                print(f"Error from TTS API: {response.status_code} - {response.json()}")
                return None
            
            # Process the audio response
            audio_data = response.content
            
            # Save to both the timestamped file (for debugging) and the latest file
            timestamp_file = os.path.join(self.audio_dir, f"tts_output_{int(time.time())}.wav")
            
            # For debugging: save a timestamped version
            if self.debug_mode:
                with open(timestamp_file, "wb") as f:
                    f.write(audio_data)
                self.log(f"Debug copy saved to {timestamp_file}")
            
            # Always save to the latest file (overwriting previous)
            with open(self.latest_output_file, "wb") as f:
                f.write(audio_data)
            
            self.log(f"Audio saved to {self.latest_output_file}")
            
            # Play the audio if requested
            if play_audio:
                self.play_audio_data(audio_data)

            if return_audio_data:
                return audio_data
            
            # Return the path to the latest file
            return self.latest_output_file
                
        except Exception as e:
            print(f"Error in text_to_speech: {e}")
            return None

    def text_to_speech_stream(self, text, clean_commands=True, media_type="raw", chunk_size=8192):
        try:
            if not self._ensure_weights_loaded():
                return

            if clean_commands:
                speech_text = self.clean_for_speech(text)
                if not speech_text:
                    print("WARNING: Text is empty after cleaning commands")
                    return
            else:
                speech_text = text

            url = f"{self.api_url}/tts"
            params = self._build_tts_payload(
                speech_text=speech_text,
                streaming_mode=True,
                media_type=media_type
            )
            self.log(f"Sending streaming POST request to: {url} with params: {params}")

            response = self.session.post(url, json=params, timeout=self.request_timeout, stream=True)
            if response.status_code != 200:
                print(f"Error from TTS API stream: {response.status_code} - {response.text}")
                return

            try:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        yield chunk
            finally:
                response.close()
        except Exception as e:
            print(f"Error in text_to_speech_stream: {e}")
    
    def play_audio_data(self, audio_data):
        """
        Play audio data using pygame
        
        Args:
            audio_data (bytes): Audio data to play
        """
        try:
            # Create a BytesIO object from the audio data
            audio_io = BytesIO(audio_data)
            
            # Load and play the audio
            pygame.mixer.music.load(audio_io)
            pygame.mixer.music.play()
            
            # Wait for the audio to finish playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            self.log("Finished playing audio")
            
        except Exception as e:
            print(f"Error playing audio: {e}")
    
if __name__ == "__main__":
    pass
