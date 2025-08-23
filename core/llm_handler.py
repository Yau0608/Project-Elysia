import sys
from pathlib import Path
import colorsys
from google import genai
from google.genai import types
from config import GEMINI_API_KEY
from pydantic import BaseModel

# Add the task directory to the path
task_dir = Path(__file__).parent.parent / 'task'
sys.path.append(str(task_dir))

import requests
import json
from unity_control import UnityControl

client = genai.Client(api_key=GEMINI_API_KEY)

class CharacterAI(BaseModel):
    dialogue: str
    expression: str
    gesture: str
    internal_thought_in_character: str

class LLMHandler:
    def __init__(self, debug_mode=False):
        self.base_dir = Path(__file__).parent
        self.debug_mode = debug_mode

        self.config = types.GenerateContentConfig(
            system_instruction=
            """
            You are a world-class AI actor. Your job is to fully embody the character defined in the user's prompt.
            - You must always stay in character.
            - Your entire response must be a single, valid JSON object that conforms to the schema provided by the API.
            - Do not add any text, markdown, or explanations before or after the JSON object.
            """,
            response_mime_type="application/json",
            response_schema=CharacterAI,
            )

        character_card_path = self.base_dir / 'cyrene_character_card.json'
        with open(character_card_path, 'r', encoding='utf-8') as f:
            self.character_card = json.load(f)


        
    def log(self, message):
        """Print debug messages only if debug mode is enabled"""
        if self.debug_mode:
            print(f"DEBUG: {message}")

    def send_prompt(self, user_prompt):
        try:
            
            character_card_string = json.dumps(self.character_card, ensure_ascii=False, indent=2)

            # Build the full prompt to send
            full_prompt = f"""
            # CHARACTER DOSSIER
            {character_card_string}

            
            # INSTRUCTIONS
            1.  Your `expression` should be a single, descriptive word for your facial expression. This is your immediate, non-verbal reaction.
            2.  Your `dialogue` should be your spoken words.
            3.  Your `gesture` should be a single, descriptive word for a subtle body action that matches your dialogue. Most of the time, this should be `Idle` or `None`. Only use a specific gesture if it feels natural and necessary, like `Waving`, `Thinking` or `SlightNod`.
            4.  Your `internal_thought_in_character` should be your inner monologue as the character.

            You must now respond, in character, to the following user message.
            user == "開拓者"
            開拓者 is a single person(male)
            # USER MESSAGE
            "{user_prompt}"
            """

            responses_json = client.models.generate_content(
                model='gemini-2.5-pro',
                config=self.config,
                contents=full_prompt,
            )
            return responses_json.text
        

        except Exception as e:
            print(f"Error in send_prompt: {e}")
            return None

    def analyze_llm_response(self, responses_json):
        try:
            # item["response"] will select the dictionary which have the key name "response" 
            # Which inside the response that turned from json object to dictionary already
            """
            the content inside 'responses_dict' variable is a list that can contain multiple dictionary, but now only have one dictionary since API return one object
            {
            "model": "llama3.1:8b",
            "created_at": "2024-05-16T12:00:00.123Z",
            "response": "Of course! I can certainly do that for you.\n\nEXPRESSION:happy",
            "done": true,
            "total_duration": 1500123456,
            "load_duration": 123456,
            "prompt_eval_count": 25,
            "eval_count": 50,
            "eval_duration": 800123456
            }

            Then the response_text will be
            'Of course! I can certainly do that for you.\n\nEXPRESSION:happy' without the "" btw '' is just for me to separate the list returned item and my english word, that line didn't return ''
            Since "" is nothing and we only have one item in the responses_dict (API return one json object only for Ollama)
            But later we might use AI studio so remember if the API return more than one object
            """


            # Extract commands from response
            commands = []
            for line in responses_json.splitlines(): 
                """
                response_text.splitlines() will return
                [
                    "Of course! I can certainly do that for you.",
                    "",  # An empty line
                    "EXPRESSION:happy"
                ]
                """
                if line.startswith("LIGHT:"):
                    commands.append(("light", line))
                elif line.startswith("TV:"):
                    commands.append(("tv", line))
                elif line.startswith("STATUS:"):
                    commands.append(("status", line))
                elif line.startswith("EXPRESSION:"):
                    commands.append(("expression", line))

                """
                'commands' content
                [("expression","EXPRESSION:happy")] a tuple
                if one more command like 'LIGHT:wiz:OFF' are there, it will return one more item
                [('expression','EXPRESSION:happy'),('light','LIGHT:wiz:OFF')]
                two tuple inside a list instead of one tuple
                """
            return commands if commands else None

        except Exception as e:
            print(f"Error in analyze_llm_response: {e}")
            return None
            
    def rgb_to_hsl(self, r, g, b):
        """Convert RGB color values to HSL format expected by Home Assistant"""
        # Normalize RGB values to 0-1 range
        r = r / 255
        g = g / 255
        b = b / 255
        
        # Convert to HSL
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        
        # Convert to degrees and percentage
        h = round(h * 360)  # 0-360 degrees
        s = round(s * 100)  # 0-100%
        
        self.log(f"Converted RGB({r*255},{g*255},{b*255}) to HSL({h},{s})")
        return h, s

    def execute_command(self, command): #Contain old code in this method, remove when needed
        try:
            command_type, command_text = command
            
            if command_type == "light":
                # Extract the command portion (everything starting with LIGHT:)
                if "LIGHT:" not in command_text:
                    return "Command format incorrect"
                
                # Clean up the command - should be cleaner now that it's on its own line
                command_pattern = command_text.strip()
                
                parts = command_pattern.split(":")
                self.log(f"Cleaned command parts: {parts}")
                
                # Check if "wiz" or "rgb" is in the parts (the light names we care about)
                if "wiz" in parts or "rgb" in parts:
                    # Find the light name
                    if "wiz" in parts:
                        light_name = "wiz"
                    else:
                        light_name = "rgb"
                    
                    # Check if it's ON or OFF command
                    if "OFF" in parts or "off" in parts:
                        return self.home_control.control_light(light_name, "off")
                    elif "ON" in parts or "on" in parts:
                        brightness = None
                        color = None
                        
                        # Parse brightness and color
                        for part in parts:
                            if part.lower().startswith("brightness="):
                                try:
                                    brightness_str = part.split("=")[1].strip('"')
                                    brightness = int(brightness_str)
                                except (ValueError, IndexError) as e:
                                    self.log(f"Error parsing brightness: {e}")
                                    brightness = 50  # Default to 50% brightness
                            elif part.lower().startswith("color="):
                                try:
                                    color_str = part.split("=")[1].strip('"')
                                    color_values = [int(x) for x in color_str.split(",")]
                                    
                                    # Handle different color formats
                                    if len(color_values) == 2:
                                        # Already in HSL (hue, saturation) format
                                        hue, sat = color_values
                                        color = (hue, sat)
                                        self.log(f"Using HSL color: {color}")
                                    elif len(color_values) == 3:
                                        # RGB format, convert to HSL
                                        r, g, b = color_values
                                        hue, sat = self.rgb_to_hsl(r, g, b)
                                        color = (hue, sat)
                                        self.log(f"Converted RGB to HSL color: {color}")
                                    else:
                                        self.log(f"Unrecognized color format: {color_values}")
                                        # Default to white if format is unrecognized
                                        color = (0, 0)
                                except (ValueError, IndexError) as e:
                                    self.log(f"Error parsing color: {e}")
                                    # If we can't parse the color, default to white
                                    color = (0, 0)
                        
                        return self.home_control.control_light(light_name, "on", brightness, color)
                    else:
                        # Default to turning on if neither ON nor OFF is specified
                        self.log("Neither ON nor OFF found in command, defaulting to ON")
                        return self.home_control.control_light(light_name, "on")
                else:
                    # Default to wiz if no light name is found
                    return self.home_control.control_light("wiz", "on")
            
            elif command_type == "tv":
                return self.home_control.control_tv(command_text)
            
            elif command_type == "status":
                return self.home_control.get_status()
            
            elif command_type == "expression":

                parts = command_text.split(":")
                if len(parts) >= 2:
                    emotion_to_send = parts[1].strip()
                    return self.unity_control.set_expression(emotion_to_send)
                else:
                    return f"Error:Invalid EXPRESSION command format: {command_text}"
            
            return "Command not recognized"

        except Exception as e:
            print(f"Error in execute_command: {e}")
            return f"Error executing command: {str(e)}"
        
# In llm_handler.py, replace the old method with this new, clean version.

    def process_command_from_responses(self, responses_json_string):
        
        if responses_json_string is None:

            return ("API call failed. Please check the error log.", "pouting","sleeping","Error: No response from API.")
        try:
            response_data = json.loads(responses_json_string)
            dialogue = response_data.get("dialogue", "Error: Missing dialogue.")
            expression = response_data.get("expression", "neutral")
            gesture = response_data.get("gesture", "idle")
            internal_thought_in_character = response_data.get("internal_thought_in_character", "Error: Missing thought.")
            
            return dialogue, expression, gesture, internal_thought_in_character

        except Exception as e:
            print(f"Error in process_command_from_responses: {e}")
            return ("I'm sorry, I got a strange response and can't think clearly.", "pouting", f"Error: {e}")

