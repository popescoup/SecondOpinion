import os
from together import Together
from tenacity import retry, stop_after_attempt, wait_random_exponential
from typing import List, Dict
import argparse
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_api_key():
    return os.environ.get("TOGETHER_API_KEY")

def log_retry_attempt(retry_state):
    print(f"[Retry] Attempt {retry_state.attempt_number} failed with exception: {retry_state.outcome.exception()}")

@retry(
    wait=wait_random_exponential(min=1, max=60), 
    stop=stop_after_attempt(10),
    before_sleep=log_retry_attempt
)
def call_llama(model: str, prompt: str = None, role: str = "user", temp: float = 1.0, 
               messages: List[Dict[str, str]] = None, safety_off: bool = False):
    """
    Call the Llama model on a specified prompt with a set temperature value 
    """
    # Get API key and initialize client
    api_key = get_api_key()
    client = Together(api_key=api_key)
    
    # Handle messages vs prompt
    if prompt is None and messages is None:
        raise ValueError("Either 'prompt' or 'messages' should be provided")
    
    if messages is None and prompt is not None:
        messages = [{"role": role, "content": prompt}]
    
    # Prepare request parameters
    request_params = {
        "model": model,
        "messages": messages,
        "temperature": temp,
        "max_tokens": 16384,
    }
    
    # Add safety settings if requested
    if safety_off:
        request_params["safety_settings"] = {
            "HARM_CATEGORY_UNSPECIFIED": "OFF",
            "HARM_CATEGORY_HATE_SPEECH": "OFF",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "OFF",
            "HARM_CATEGORY_HARASSMENT": "OFF",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "OFF",
            "HARM_CATEGORY_CIVIC_INTEGRITY": "OFF",
        }
    
    response = client.chat.completions.create(**request_params)
    
    choice = response.choices[0]
    content = (choice.message.content or "").strip()
    finish_reason = choice.finish_reason
    
    if finish_reason == "length":
        print(f"Error: Output token size exceeds max token count", flush=True)
    
    if not content:
        print(f"Error: Content field in LLM response is empty", flush=True)
    
    return content

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="prompt Llama")
    parser.add_argument('--prompt', type=str, required=False, default="What's capital of France?",
                        help='Input prompt')
    parser.add_argument('--role', type=str, required=False, default="user")
    parser.add_argument('--model', type=str, required=False, 
                        default="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8", 
                        help="Llama model to use")
    parser.add_argument('--temp', type=float, default=0.0, required=False,
                       help='set the temperature value between 0 and 2')
    parser.add_argument('--message_list', type=str, required=False, default='',
                        help='pass elements of list separated by semi-colon. an element will be\
                        a dictionary of {"role":role, "content":prompt}')
    parser.add_argument('--safety_off', action='store_true',
                        help='Disable safety filters (matches original behavior)')
    
    args = parser.parse_args()
    
    if args.message_list == '':
        result = call_llama(
            model=args.model,
            prompt=args.prompt, 
            role=args.role, 
            temp=args.temp,
            safety_off=args.safety_off
        )
        print(result)
    else:
        list_args = args.message_list.split(';')
        messages = [json.loads(e, strict=False) for e in list_args]
        result = call_llama(
            model=args.model,
            messages=messages, 
            role=args.role, 
            temp=args.temp,
            safety_off=args.safety_off
        )
        print(result)