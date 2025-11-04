import anthropic


class ClaudeClient:
    def __init__(self, default_model: str = "claude-sonnet-4-5"):
        self.default_model = default_model
        self.client = anthropic.Anthropic()

    def generate(self, prompt: str, model: str = None, max_tokens: int = 1024) -> str:
        model = model or self.default_model
        message = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )

        return message.content[0].text
    
    def count_tokens(self, text: str, model: str = None) -> int:
        model = model or self.default_model
        count = self.client.messages.count_tokens(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": text,
                }
            ]
        )
        
        return count.input_tokens