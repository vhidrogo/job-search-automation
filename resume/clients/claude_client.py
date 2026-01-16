import anthropic

from tracker.models import LlmRequestLog


class ClaudeClient:
    def __init__(self, default_model: str = "claude-sonnet-4-5", client: anthropic.Anthropic = None):
        self.default_model = default_model
        self.client = client or anthropic.Anthropic()

    def generate(self, prompt: str, model: str = None, call_type: str = None, max_tokens: int = 1024) -> str:
        model = model or self.default_model
        input_tokens = self.count_tokens(prompt, model)
        output_tokens = 0
        chunks = []

        try:
            with self.client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ]
            ) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        text = event.delta.text
                        chunks.append(text)

                final_message = stream.get_final_message()
                output_tokens = final_message.usage.output_tokens

            return "".join(chunks)

        finally:
            LlmRequestLog.objects.create(
                call_type=call_type,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
    
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
