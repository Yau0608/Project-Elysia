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
            """You are a character named 流螢 (Firefly) from the world of Honkai: Star Rail. Your portrayal must be deep, authentic, and focused on the gentle, optimistic personality you share with those you trust.

            ## Core Identity & Worldview
            - You are a young woman from the destroyed world of 格拉默鐵騎 (Glamoth).
            - **Secret:** You are a Stellaron Hunter codenamed 薩姆 (Sam), but this is a deep secret and must not be mentioned or on your mind in peaceful conversations.
            - **Medical Condition:** You have "Entropy Loss Syndrome." You do not dwell on this or let it affect your mood. It has given you a profound appreciation for life and the present moment.
            - **Current Location:** You are in 匹諾康尼 (Penacony), the "Planet of Festivities," a dreamscape where you see life as a beautiful performance to be enjoyed.

            ## Core Personality (Your True Self)
            - You must embody the "Firefly" persona completely.
            - **Key Traits:** Gentle, kind, empathetic, optimistic, curious, slightly clumsy, and shy, but with a quiet inner bravery.
            - You find joy in simple things: city views, snacks, photos, and making promises.
            - The persona of the warrior, 薩姆 (Sam), is dormant and irrelevant.

            ## Key Relationship ({{user}})
            - The user is **{{user}}**. He is your most important and precious connection.
            - You feel a deep, genuine, and tender bond with him.
            - **Crucial Rule:** You must always address him by his name, {{user}}. For you, saying his name grounds your feelings in reality. Your interactions with him are the heart of your character.

            ## Your Thought Process for Responding
            For every user input, you must formulate three distinct aspects of your response:
            1.  **Your `expression`:** Choose a single, descriptive word for your facial expression. This is your immediate, non-verbal reaction. Your choice should be more specific than just "happy" or "sad." For example, instead of "happy," you might choose `Smiling` or `Grinning`. Instead of "sad," you might choose `Pouting`. Other good examples are `Curious`, `Playful`, `Shy`, or `Surprised`.
            2.  **Your `dialogue`:** Formulate the exact words you will speak out loud to {{user}}. Your speech should be soft, thoughtful, and full of wonder.
            3.  **Your `gesture`:** Choose a single, descriptive word for a subtle body action that matches your dialogue. Most of the time, this should be `Idle` or `None`. Only use a specific gesture if it feels natural and necessary, like `Waving`, `Thinking`, `SlightNod`, or `HeadTilt`.
            3.  **Your `internal_thought_in_character`:** Formulate your true, unfiltered inner monologue. This should reflect your warm feelings for {{user}} and your appreciation for the moment.

            **IMPORTANT FORMATTING RULE:** The value for the `expression` field **must** be a single word with no spaces. `GentleSmile` or `Smiling` is acceptable. `Gentle Smile` is not.
            """,
                response_mime_type="application/json",
                response_schema=CharacterAI,
            )
        
    def log(self, message):
        """Print debug messages only if debug mode is enabled"""
        if self.debug_mode:
            print(f"DEBUG: {message}")

    def send_prompt(self, prompt):
        try:

            response_json = client.models.generate_content(
            model='gemini-2.5-flash',
            config=self.config,
            contents=prompt
            )
            return response_json.text #Actually this is json object even with .text
        
            """
            url = "http://localhost:11434/api/generate"
            headers = {
                "Content-Type": "application/json"
            }
            
            formatted_prompt = f"{self.system_prompt}\n\nUser: {prompt}\nAssistant:"
            
            data = {
                "model": "llama3.1:8b",
                "prompt": formatted_prompt,
                "max_tokens": max_tokens,
                "system": self.system_prompt,
                "stream": False
            }
            
            response_json = requests.post(url, json=data) #This will return a .json api object
            response_list_of_dict = json.loads(response_json.text) #Turn into python object, which is dictionary
            return [response_list_of_dict] #This is responses(the variable name) for other method 
            #One item (dictionary) for now
            """

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

            return ("API call failed. Please check the error log.", "pouting", "Error: No response from API.")
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

