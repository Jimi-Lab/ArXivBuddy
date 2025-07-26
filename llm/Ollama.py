from ollama import generate
import json

class Ollama:
    def __init__(self, model):
        self.model_name = model

    def inference(self, prompt):
        response = generate(self.model_name, prompt)["response"]
        response = response.split("</think>")[1].strip()
        return response
    
if __name__ == "__main__":
    model = "deepseek-r1:7b"
    ollama = Ollama(model)
    prompt = "Hello, who are you?"
    response = ollama.inference(prompt)
    print(response)