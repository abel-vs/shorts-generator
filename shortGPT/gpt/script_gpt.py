from shortGPT.gpt import gpt_utils
import json
def generateScript(script_description):
    chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/script_generator.yaml')
    chat = chat.replace("<<SCRIPT_DESCRIPTION>>", script_description)
    result = gpt_utils.gpt3Turbo_completion(chat_prompt=chat, system=system, temp=1.3)
    return result