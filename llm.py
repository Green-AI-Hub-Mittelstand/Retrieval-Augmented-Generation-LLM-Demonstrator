import threading
from mlx_lm import load, generate

class LLM:
    def __init__(self, query, llm, tokenizer):
        self.query = query
        self.llm = llm
        self.tokenizer = tokenizer
        self.result = None

    def run(self):
        self.result = generate(self.llm, self.tokenizer, prompt="hello", verbose=True)