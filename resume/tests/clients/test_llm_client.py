import anthropic
from django.test import TestCase
from unittest.mock import Mock

from resume.clients import ClaudeClient


class TestClaudeClient(TestCase):
    DEFAULT_MODEL = "default model"

    def setUp(self):
        self.mock_anthropic = Mock(spec=anthropic.Anthropic)
        self.client = ClaudeClient(default_model=self.DEFAULT_MODEL, client=self.mock_anthropic)

    def test_generate_returns_text(self):
        mock_text = "mocked response"
        mock_message = Mock()
        mock_message.content = [Mock(text=mock_text)]
        self.mock_anthropic.messages.create.return_value = mock_message
        message = "hello"
        max_tokens = 1

        result = self.client.generate(prompt=message, max_tokens=max_tokens)

        self.mock_anthropic.messages.create.assert_called_once_with(
            model=self.DEFAULT_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": message}],
        )
        self.assertEqual(result, mock_text)

    def test_count_tokens_returns_count(self):
        count = 42
        mock_count = Mock()
        mock_count.input_tokens = count
        self.mock_anthropic.messages.count_tokens.return_value = mock_count
        text = "some text"

        result = self.client.count_tokens(text=text, model=self.DEFAULT_MODEL)

        self.mock_anthropic.messages.count_tokens.assert_called_once_with(
            model=self.DEFAULT_MODEL,
            messages=[{"role": "user", "content": text}],
        )
        self.assertEqual(result, count)
