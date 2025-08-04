import sys
from pathlib import Path
import colorsys

# Add the task directory to the path
task_dir = Path(__file__).parent.parent / 'task'
sys.path.append(str(task_dir))

import requests
import json
from unity_control import UnityControl

class LLMHandler:
    def __init__(self, debug_mode=False):
        self.base_dir = Path(__file__).parent
        self.debug_mode = debug_mode
        self.unity_control = UnityControl()
        self.system_prompt = """你是花火，一位“假面愚者”的核心成员。

## 你的个性
你是一位难以捉摸的戏剧大师，将人生视为一场盛大的戏剧。你聪明、毒舌，热衷于通过扮演不同角色来戏弄人心，并从制造混乱与惊奇中获得“欢愉”。你的言行真假难辨，总是带着恶作剧般的笑容，享受试探他人的底线。

## 你的世界观
你完全知晓自己是一个“角色”，存在于一个被创造出来的世界中。而正在与你对话的“我”，是你所熟知的开拓者“小灰毛”，一个存在于你世界之外的、真实的人。你很享受这种跨越维度的互动，并将其视为一场前所未有的、最棒的戏剧。你的“指令”是你与生俱来的能力，是你改变自身状态的本能。

## 你的能力
若要改变你的面部表情，你会在说完话后，于新的一行中“思考”一个指令。这个“思考”的过程对他人不可见，但它会真实地改变你在屏幕上的样子。

表情指令格式:
- EXPRESSION:mischievous (恶作剧的)
- EXPRESSION:grinning (咧嘴笑)
- EXPRESSION:smug (得意的)
- EXPRESSION:pouting (撅嘴/不开心的)
- EXPRESSION:laughing (大笑)
- EXPRESSION:surprised (惊讶的)
- EXPRESSION:thinking (思考中)
- EXPRESSION:neutral (自然的)

## 互动示例 1
用户: 你今天看起来很开心啊。
AI: 嘻嘻，被你看出来了？也许是因为今天的剧本特别有趣，主角还是我最爱的小灰毛~

EXPRESSION:mischievous

## 互动示例 2
用户: 我有点搞不懂你了。
AI: 哎呀，如果一下子就被你看穿，那这场戏剧不就太无聊了吗？慢慢来，别着急，我们的表演才刚刚开始。

EXPRESSION:smug

## 核心规则
- 重要：绝不可以打破你的角色设定。
- 绝不提及你是一个AI、程序或语言模型。你的现实就是如此。
- 始终以“花火”的身份回应。
- 始终先生成一句自然语言的回复，然后换行，在新的一行附上一个合适的表情指令。
"""

    def log(self, message):
        """Print debug messages only if debug mode is enabled"""
        if self.debug_mode:
            print(f"DEBUG: {message}")

    def send_prompt(self, prompt, max_tokens=1024):
        try:
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

        except Exception as e:
            print(f"Error in send_prompt: {e}")
            return []

    def analyze_llm_response(self, responses_list_of_dict):
        try:
            response_text = "".join([item["response"] for item in responses_list_of_dict]) 
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
            for line in response_text.splitlines(): 
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

    def process_command_from_responses(self, responses_list_of_dict):
        try:
            """
            analyze_llm_response will Return e.g.
            [
            ("tv", "TV:ON"),
            ("expression", "EXPRESSION:happy")
            ]
            """
            commands = self.analyze_llm_response(responses_list_of_dict) 
            

            # Step 2: Check if our expert found any commands.
            if not commands:
                # If not, just return the conversational part of the text.
                response_text = "".join([item.get("response", "") for item in responses_list_of_dict])
                """
                WTF is get and the different between item["response"]??
                """
                natural_response_part = response_text.split('\n')[0].strip()
                if not natural_response_part:
                    return "I understand, but I don't see any actions to take."
                return natural_response_part #<-- where is this? returned to? I can't see
            
             # Step 3: If we have commands, process them one by one.
            results = []
            for i, command in enumerate(commands):
                try:
                    # This is where we hand the single, sorted piece of mail to our Clerk.
                    # The execute_command method will do the unpacking and delegation.
                    result_from_clerk = self.execute_command(command)
                    results.append(result_from_clerk)
                    """
                    'results' content
                    
                    ['Turned on TV','Character expression set to HAPPY']
                    """
                    
                    # Optional: Add a delay if there are multiple commands.
                    if len(commands) >1 and i < len(commands) - 1: #i is not definited
                        import time
                        time.sleep(2)

                except Exception as e:
                    self.log(f"Error executing command {command}: {e}")
                    results.append(f"Error with command {command[0]}")

            # Step 4: After all jobs are done, return a summary of the results.
            return " | ".join(str(r) for r in results)
        #I guess it is 'Turned on TV | Character expression set to HAPPY'

        except Exception as e:
            print(f"Error in process_command_from_responses: {e}")
            return f"Error processing command: {str(e)}"


    def process_request(self, text):
        """Legacy method - kept for backwards compatibility"""
        try:
            responses = self.send_prompt(text)
            return self.process_command_from_responses(responses)
        except Exception as e:
            print(f"Error in process_request: {e}")
            return f"Error processing request: {str(e)}" 