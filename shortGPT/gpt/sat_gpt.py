from shortGPT.gpt import gpt_utils
import json

def generateSATquestion():
    chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/sat_generator.yaml')
    result = gpt_utils.gpt3Turbo_completion(chat_prompt=chat, system=system, temp=1.3)
    return result

def generateSATquestions(n):
    out = []
    chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/sat_question_generator.yaml')
    chat = chat.replace("<<N>>", f"{n}")
    count = 0
    while len(out) != n:
        result = gpt_utils.gpt3Turbo_completion(chat_prompt=chat, system=system, temp=1.69)
        count+=1
        try:
            out = json.loads(result.replace("'", '"'))
        except Exception as e:
            print(f"INFO - Failed generating {n} fact subjects after {count} trials", e)
            pass
        
    return out