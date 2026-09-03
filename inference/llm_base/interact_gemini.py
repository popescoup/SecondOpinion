import random
import vertexai
from vertexai import generative_models
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_random_exponential,
)

AVAILABLE_LOCATIONS = ["us-east5", "us-south1", "us-central1", "us-west4", "us-east1", "us-east4", "us-west1"]
PROJECT_ID = "YOUR_PROJECT_ID"

random_location = random.choice(AVAILABLE_LOCATIONS)
print(f"Sending this query to: {random_location}")
vertexai.init(project=PROJECT_ID, location=random_location)

def log_retry_attempt(retry_state):
    print(f"[Retry] Attempt {retry_state.attempt_number} failed with exception: {retry_state.outcome.exception()}")

@retry(
    wait=wait_random_exponential(min=1, max=60), 
    stop=stop_after_attempt(10),
    before_sleep=log_retry_attempt
)
def call_gemini(model, prompt, temp):

    model = generative_models.GenerativeModel(model)

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": temp,
        },
        safety_settings={
            generative_models.HarmCategory.HARM_CATEGORY_UNSPECIFIED: generative_models.HarmBlockThreshold.OFF,
            generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.OFF,
            generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.OFF,
            generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.OFF,
            generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.OFF,
            generative_models.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY: generative_models.HarmBlockThreshold.OFF,
        }
    )
    return response.text