import google.generativeai as genai
import global_params as gp

from openai import OpenAI

## GEMINI ##

genai.configure(api_key="Enter Verification key")

# Create the model
# See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
gemini_config = {
    "temperature": 1.0,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

gemini_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=gemini_config,
    # safety_settings = Adjust safety settings
    # See https://ai.google.dev/gemini-api/docs/safety-settings
)

## ChatGPT ##
openai_model = OpenAI(api_key="Enter Verification key")


def generate_json(problem: str, llm_model: str = "Gemini"):
    if llm_model == "Gemini":
        return gemini_model.start_chat(history=[]).send_message(gp.prompt + problem).text
    else:
        return openai_model.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": gp.prompt
                },
                {
                    "role": "user",
                    "content": problem
                }
            ],
            temperature=0.5,
            max_tokens=1024,
            top_p=1
        ).choices[0].message.content
