import anthropic
from django.test import TestCase
from unittest.mock import Mock

from resume.clients import ClaudeClient
from tracker.models import LlmRequestLog


class TestClaudeClient(TestCase):
    DEFAULT_MODEL = "default model"

    def setUp(self):
        self.mock_anthropic = Mock(spec=anthropic.Anthropic)
        self.client = ClaudeClient(default_model=self.DEFAULT_MODEL, client=self.mock_anthropic)

    def test_generate_returns_text_and_logs_request(self):
        mock_text = "mocked response"
        output_tokens = 5
        mock_message = Mock()
        mock_message.content = [Mock(text=mock_text)]
        mock_message.usage.output_tokens = output_tokens
        self.mock_anthropic.messages.create.return_value = mock_message
        input_tokens = 7
        self.mock_anthropic.messages.count_tokens.return_value.input_tokens = input_tokens
        message = "hello"
        max_tokens = 1
        call_type = "test_call"

        result = self.client.generate(prompt=message, max_tokens=max_tokens, call_type=call_type)

        self.mock_anthropic.messages.create.assert_called_once_with(
            model=self.DEFAULT_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": message}],
        )
        log = LlmRequestLog.objects.first()
        self.assertEqual(result, mock_text)
        self.assertIsNotNone(log)
        self.assertEqual(log.call_type, call_type)
        self.assertEqual(log.model, self.DEFAULT_MODEL)
        self.assertEqual(log.input_tokens, self.mock_anthropic.messages.count_tokens.return_value.input_tokens)
        self.assertEqual(log.input_tokens, input_tokens)
        self.assertEqual(log.output_tokens, output_tokens)

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
