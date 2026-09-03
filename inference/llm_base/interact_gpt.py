from dotenv import load_dotenv
import os
from openai import OpenAI
import argparse
import ast
import json
from typing import List, Dict
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

load_dotenv()
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def log_retry_attempt(retry_state):
    print(f"[Retry] Attempt {retry_state.attempt_number} failed with exception: {retry_state.outcome.exception()}")

@retry(
    wait=wait_random_exponential(min=1, max=60), 
    stop=stop_after_attempt(6),
    before_sleep=log_retry_attempt
)
def completion_with_backoff(**kwargs):
    return client.chat.completions.create(**kwargs)


def call_gpt(model, prompt=None,role="user", temp=1, messages: List[Dict[str, str]]=None):
    if prompt == None and messages == None:
        raise ValueError("Either 'prompt' or 'messages' should be provided")
    elif messages == None:
        messages=[
            {
                "role": role,
                "content": prompt,
            }
        ]
    chat_completion = completion_with_backoff(
        messages=messages,
        model=model,
        temperature=temp,
    )
    
    return chat_completion.choices[0].message.content

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="prompt ChatGPT")
    parser.add_argument('--prompt', type=str, required=False, default="What's capital of France?",
                        help='Input prompt')
    parser.add_argument('--role', type=str, required=False, default="user")
    parser.add_argument('--model', type=str, required=False, default="gpt-4o")
    parser.add_argument('--temp', type=float, default=1, required=False,
                       help='set the temperature value between 0 and 2')
    parser.add_argument('--message_list', type=str, required=False, default='',
                        help='pass elements of list separated by semi-colon. an element will be\
                        a dictionary of {"role":role, "content":prompt}')
    
    args = parser.parse_args()
    if args.message_list == '':
        print(call_gpt(prompt=args.prompt, role=args.role, model=args.model, temp=args.temp))
    else:
        list_args = args.message_list.split(';')
        messages=[json.loads(e, strict=False) for e in list_args]
        print(call_gpt(messages=messages, role=args.role, model=args.model, temp=args.temp))