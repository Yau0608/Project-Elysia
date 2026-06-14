import glob
import importlib
import os
import re
import time
from io import BytesIO
from pathlib import Path

import pygame
import requests

import config as runtime_config

class TTSHandler:
    """
    Text-to-Speech handler using GPT-SoVITS API
    
    This class manages text-to-speech conversion and playback using the GPT-SoVITS API.
    It sends text to the API, receives audio data, and plays it locally.
    """
    
    def __init__(self, api_url=None, gpt_url=None, sovits_url=None, debug_mode=False, voice_name=None, auto_reload_config=True):
        self.debug_mode = debug_mode
        self.auto_reload_config = auto_reload_config
        self.config_module = runtime_config
        self.voice_name = voice_name
        self.voice_name_override = voice_name is not None
        self.api_url_override = api_url
        self.gpt_url_override = gpt_url
        self.sovits_url_override = sovits_url
        self.reference_override_active = False
        self.audio_dir = os.path.join(os.path.dirname(__file__), "temp")
        self.latest_output_file = os.path.join(self.audio_dir, "latest_tts_output.wav")
        self.session = requests.Session()
        self.request_timeout = 120
        self.api_url = None
        self.gpt_url = None
        self.sovits_url = None
        self.active_gpt_url = None
        self.active_sovits_url = None
        self.sample_steps = 16
        self.parallel_infer = True
        self.batch_size = 1
        self.batch_threshold = 0.75
        self.default_ref_audio = None
        self.default_prompt_text = ""
        self.default_prompt_lang = "zh"
        self.default_text_lang = "zh"
        self.request_logging = False

        self._load_runtime_config(reload_module=False)

        # Create the audio directory if it doesn't exist
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
        
        # Clean up old TTS output files
        self._cleanup_old_tts_files()
        
        # Initialize pygame for audio playback
        pygame.mixer.init()

        print(f"TTS Handler initialized with API URL: {self.api_url}")
        print(f"Using reference audio: {self.default_ref_audio}")

    def _load_runtime_config(self, reload_module=True):
        if reload_module and self.auto_reload_config:
            self.config_module = importlib.reload(self.config_module)

        config_voice_name = self.voice_name if self.voice_name_override else getattr(self.config_module, "TTS_ACTIVE_VOICE", None)
        voice_config = self.config_module.get_tts_voice_config(config_voice_name)

        self.api_url = self.api_url_override or voice_config["api_url"]
        self.gpt_url = self.gpt_url_override or voice_config["gpt_weights_path"]
        self.sovits_url = self.sovits_url_override or voice_config["sovits_weights_path"]
        self.sample_steps = voice_config["sample_steps"]
        self.parallel_infer = voice_config["parallel_infer"]
        self.batch_size = voice_config["batch_size"]
        self.batch_threshold = voice_config["batch_threshold"]
        self.request_logging = getattr(self.config_module, "TTS_REQUEST_LOGGING", True)

        if not self.reference_override_active:
            self.default_ref_audio = voice_config["ref_audio_path"]
            self.default_prompt_text = voice_config["prompt_text"]
            self.default_prompt_lang = voice_config["prompt_lang"]
            self.default_text_lang = voice_config["text_lang"]

        if not self.voice_name_override:
            self.voice_name = voice_config["name"]

        self.log(
            "Loaded TTS config "
            f"(voice={voice_config['name']}, gpt={self.gpt_url}, sovits={self.sovits_url}, ref={self.default_ref_audio})"
        )
        return True

    def _format_path_for_log(self, path_value):
        if not path_value:
            return "<none>"
        return str(Path(path_value).name)

    def _format_text_for_log(self, text, max_length=120):
        if not text:
            return ""
        normalized = re.sub(r"\s+", " ", text).strip()
        if len(normalized) <= max_length:
            return normalized
        return normalized[: max_length - 3] + "..."

    def _detect_sovits_model_version(self, weights_path):
        if not weights_path or not os.path.exists(weights_path):
            return None

        head_to_version = {
            b"00": "v1",
            b"01": "v2",
            b"02": "v3",
            b"03": "v3",
            b"04": "v4",
            b"05": "v2Pro",
            b"06": "v2ProPlus",
        }

        try:
            with open(weights_path, "rb") as weights_file:
                version_head = weights_file.read(2)
        except OSError:
            return None

        if version_head in head_to_version:
            return head_to_version[version_head]

        if version_head == b"PK":
            file_size = os.path.getsize(weights_path)
            if file_size < 82978 * 1024:
                return "v1"
            if file_size < 700 * 1024 * 1024:
                return "v2"
            return "v3"

        return None

    def get_expected_output_sample_rate(self):
        if not self._refresh_runtime_config():
            return 32000
        if not self._ensure_weights_loaded():
            return 32000

        model_version = self._detect_sovits_model_version(self.sovits_url)
        output_sample_rate = {
            "v3": 24000,
            "v4": 48000,
        }.get(model_version, 32000)

        self._request_log(
            f"stream_sample_rate={output_sample_rate} "
            f"(model_version={model_version or 'unknown'}, sovits={self._format_path_for_log(self.sovits_url)})"
        )
        return output_sample_rate

    def _request_log(self, message):
        if self.request_logging or self.debug_mode:
            print(f"TTS INFO: {message}")

    def _log_active_configuration(self, speech_text, streaming_mode, media_type):
        ref_duration = None
        if hasattr(self.config_module, "_get_wav_duration_seconds"):
            ref_duration = self.config_module._get_wav_duration_seconds(self.default_ref_audio)

        ref_duration_text = f"{ref_duration:.2f}s" if isinstance(ref_duration, (int, float)) else "unknown"
        self._request_log(
            "voice={voice} stream={streaming} media={media} gpt={gpt} sovits={sovits} "
            "ref={ref} ref_duration={ref_duration} prompt_lang={prompt_lang} text_lang={text_lang} "
            "sample_steps={sample_steps} parallel_infer={parallel_infer} batch_size={batch_size} "
            "batch_threshold={batch_threshold}".format(
                voice=self.voice_name or "<none>",
                streaming=streaming_mode,
                media=media_type,
                gpt=self._format_path_for_log(self.gpt_url),
                sovits=self._format_path_for_log(self.sovits_url),
                ref=self._format_path_for_log(self.default_ref_audio),
                ref_duration=ref_duration_text,
                prompt_lang=self.default_prompt_lang,
                text_lang=self.default_text_lang,
                sample_steps=self.sample_steps,
                parallel_infer=self.parallel_infer,
                batch_size=self.batch_size,
                batch_threshold=self.batch_threshold,
            )
        )
        self._request_log(f"reference_text={self._format_text_for_log(self.default_prompt_text)}")
        self._request_log(f"target_text={self._format_text_for_log(speech_text)}")

    def _refresh_runtime_config(self):
        try:
            return self._load_runtime_config(reload_module=True)
        except Exception as e:
            print(f"Error loading TTS config: {e}")
            return False

    def _validate_runtime_configuration(self):
        if not self.api_url:
            print("TTS API URL is not configured. Set TTS_API_URL in core/config.py.")
            return False
        if not self.gpt_url:
            print(
                "GPT weights not found. Put a .ckpt file under Backend/GPT-sovits/GPT_weights* "
                "or set TTS_GPT_WEIGHTS_PATH in core/config.py."
            )
            return False
        if not os.path.exists(self.gpt_url):
            print(f"GPT weights path does not exist: {self.gpt_url}")
            return False
        if not self.sovits_url:
            print(
                "SoVITS weights not found. Put a .pth file under Backend/GPT-sovits/SoVITS_weights* "
                "or set TTS_SOVITS_WEIGHTS_PATH in core/config.py."
            )
            return False
        if not os.path.exists(self.sovits_url):
            print(f"SoVITS weights path does not exist: {self.sovits_url}")
            return False
        if not self.default_ref_audio:
            print("Reference audio is not configured. Set ref_audio_path in core/config.py.")
            return False
        if not os.path.exists(self.default_ref_audio):
            print(f"Reference audio path does not exist: {self.default_ref_audio}")
            return False
        return True

    def _set_gpt_weights(self):
        gpt_endpoint_url = f"{self.api_url}/set_gpt_weights"
        gpt_params = {"weights_path": self.gpt_url}
        self._request_log(f"switching_gpt={self._format_path_for_log(self.gpt_url)}")
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
        self._request_log(f"switching_sovits={self._format_path_for_log(self.sovits_url)}")
        self.log(f"Sending GET request to change SoVITS model: {sovits_endpoint_url}")
        sovits_response = self.session.get(sovits_endpoint_url, params=sovits_params, timeout=self.request_timeout)
        if sovits_response.status_code != 200:
            print(f"Error setting SoVITS weights: {sovits_response.text}")
            return False
        self.active_sovits_url = self.sovits_url
        return True

    def _ensure_weights_loaded(self):
        if not self._validate_runtime_configuration():
            return False
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
        self.reference_override_active = True
        self.log(f"Default reference set: {ref_audio_path}, '{prompt_text}' ({prompt_lang})")

    def set_voice_profile(self, voice_name):
        self.voice_name = voice_name
        self.voice_name_override = True
        self.reference_override_active = False
        return self._refresh_runtime_config()

    def use_config_voice_profile(self):
        self.voice_name_override = False
        self.reference_override_active = False
        return self._refresh_runtime_config()
  
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
            if not self._refresh_runtime_config():
                return None

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

            self._log_active_configuration(speech_text, streaming_mode=False, media_type="wav")

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
                self._request_log(f"tts_request_failed status={response.status_code}")
                print(f"Error from TTS API: {response.status_code} - {response.json()}")
                return None
            
            # Process the audio response
            audio_data = response.content
            self._request_log(f"tts_request_succeeded bytes={len(audio_data)}")
            
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
            if not self._refresh_runtime_config():
                return
            if not self._ensure_weights_loaded():
                return

            if clean_commands:
                speech_text = self.clean_for_speech(text)
                if not speech_text:
                    print("WARNING: Text is empty after cleaning commands")
                    return
            else:
                speech_text = text

            self._log_active_configuration(speech_text, streaming_mode=True, media_type=media_type)

            url = f"{self.api_url}/tts"
            params = self._build_tts_payload(
                speech_text=speech_text,
                streaming_mode=True,
                media_type=media_type
            )
            self.log(f"Sending streaming POST request to: {url} with params: {params}")

            response = self.session.post(url, json=params, timeout=self.request_timeout, stream=True)
            if response.status_code != 200:
                self._request_log(f"tts_stream_failed status={response.status_code}")
                print(f"Error from TTS API stream: {response.status_code} - {response.text}")
                return

            try:
                self._request_log("tts_stream_started")
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        yield chunk
            finally:
                self._request_log("tts_stream_finished")
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
