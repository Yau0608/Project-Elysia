import requests
import json
import os
import time
import pygame
import re
import glob
from io import BytesIO
import urllib.parse

# Hard-coded reference audio configuration
DEFAULT_REF_AUDIO = "C:\\Users\\Yau\\Documents\\YauProject\\GPT-SoVITS-v2pro-20250604\\test\\Ely1.wav"
DEFAULT_PROMPT_TEXT = "那我想，芽衣一定也已经迫不及待了，对不对？好了，我们边走边说吧。"
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
    
    def text_to_speech(self, text, play_audio=True, clean_commands=True): #remember to change the text_lang = language
        """
        Convert text to speech using the new GPT-SoVITS api_v2.py.
        This version uses a POST request with a JSON payload.
        """    
        try:


            gpt_endpoint_url = f"{self.api_url}/set_gpt_weights"

            gpt_params = {"weights_path": self.gpt_url}
            self.log(f"Sending GET request to change GPT model: {gpt_endpoint_url}")
            gpt_response = requests.get(gpt_endpoint_url, params=gpt_params)

            if gpt_response.status_code != 200:
                print(f"Error setting GPT weights: {gpt_response.json()}")
                return None
            
            sovits_endpoint_url = f"{self.api_url}/set_sovits_weights"


            sovits_params = {"weights_path": self.sovits_url}
            self.log(f"Sending GET request to change GPT model: {sovits_endpoint_url}")
            sovits_response = requests.get(sovits_endpoint_url, params=sovits_params)

            if sovits_response.status_code != 200:
                print(f"Error from setting SoVITS weights: {sovits_response.json()}")
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
            params = {
                "text": speech_text,
                "text_lang": self.default_text_lang,
                "ref_audio_path": self.default_ref_audio,
                "prompt_text": self.default_prompt_text,
                "prompt_lang": self.default_prompt_lang,
                "text_split_method": "cut5" # Explicitly requesting the best split method
            }
            
            self.log(f"Sending POST request to: {url} with params: {params}")
            
            response = requests.post(url, json=params)
            
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
            
            # Return the path to the latest file
            return self.latest_output_file
                
        except Exception as e:
            print(f"Error in text_to_speech: {e}")
            return None
    
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