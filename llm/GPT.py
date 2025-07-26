"""
Use GPT Series Models
"""

from openai import OpenAI
import time

class GPT():
    def __init__(self, model, base_url, api_key):
        self.model_name = model
        self.base_url = base_url
        self.api_key = api_key

        self._init_model()

    def _init_model(self):
        self.client = OpenAI(base_url= self.base_url, api_key=self.api_key)

    def build_prompt(self, question):
        message = []

        message.append(
            {
                "type": "text",
                "text": question,
            }
        )

        prompt =  [
            {
                "role": "user",
                "content": message
            }
        ]
        return prompt

    def call_gpt_eval(self, message, model_name, retries=10, wait_time=1, temperature=0.0):
        for i in range(retries):
            try:
                result = self.client.chat.completions.create(
                    model=model_name,
                    messages=message,
                    temperature=temperature
                )
                response_message = result.choices[0].message.content
                return response_message
            except Exception as e:
                if i < retries - 1:
                    print(f"Failed to call the API {i+1}/{retries}, will retry after {wait_time} seconds.")
                    print(e)
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Failed to call the API after {retries} attempts.")
                    print(e)
                    raise

    def inference(self, prompt, temperature=0.7):
        prompt = self.build_prompt(prompt)
        response = self.call_gpt_eval(prompt, self.model_name, temperature=temperature)
        return response
    
if __name__ == "__main__":
    # Test GPT
    model = "gpt-3.5-turbo"
    base_url = "https://api.openai.com/v1"
    api_key = "*"

    # Test SiliconFlow
    model = "deepseek-ai/DeepSeek-V3"
    base_url = "https://api.siliconflow.cn/v1"
    api_key = "*"
    gpt = GPT(model, base_url, api_key)
    prompt = "Hello, who are you?"
    response = gpt.inference(prompt, temperature=1)
    print(response)