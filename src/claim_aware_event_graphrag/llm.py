from __future__ import annotations

import json
import os
from typing import Protocol
from urllib import request


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str:
        ...


class MockLLMClient:
    """Keyword-based mock extractor for Step 2 tests and scripts."""

    def complete(self, prompt: str) -> str:
        chunk_text = self._extract_chunk_text(prompt)
        text = chunk_text.lower()

        if (('military facility' in text and 'civilian infrastructure' in text)
            or ('military logistics warehouse' in text and 'civilian fuel depot' in text)
            or ('military logistics warehouse' in text and 'not civilian facilities' in text)):
            result = {
                'temp_events': [
                    {
                        'temp_event_id': 'e1',
                        'time': None,
                        'type': 'military',
                        'summary': 'Reported strike concerning facility type.',
                        'actors': ['Defense spokesperson', 'Local authority'],
                        'location': None,
                    }
                ],
                'temp_claims': [
                    {
                        'temp_claim_id': 'c1',
                        'temp_event_id': 'e1',
                        'claimant': 'Defense spokesperson',
                        'text': 'The strike targeted a military facility.',
                        'topic': 'target',
                        'stance': 'assert',
                    },
                    {
                        'temp_claim_id': 'c2',
                        'temp_event_id': 'e1',
                        'claimant': 'Local authority',
                        'text': 'The strike hit civilian infrastructure.',
                        'topic': 'target',
                        'stance': 'deny',
                    },
                ],
            }
            return json.dumps(result, ensure_ascii=False)

        if 'oil prices' in text or 'premium surcharges' in text or 'insurers' in text:
            result = {
                'temp_events': [
                    {
                        'temp_event_id': 'e1',
                        'time': None,
                        'type': 'economic',
                        'summary': 'Market impact after regional incident.',
                        'actors': ['Energy analysts'],
                        'location': None,
                    }
                ],
                'temp_claims': [
                    {
                        'temp_claim_id': 'c1',
                        'temp_event_id': 'e1',
                        'claimant': 'Energy analysts',
                        'text': 'Oil prices rose after the incident.',
                        'topic': 'economic_impact',
                        'stance': 'report',
                    }
                ],
            }
            return json.dumps(result, ensure_ascii=False)

        if 'could not be independently verified' in text:
            result = {
                'temp_events': [
                    {
                        'temp_event_id': 'e1',
                        'time': None,
                        'type': 'other',
                        'summary': 'Reported incident pending independent verification.',
                        'actors': ['Monitoring group'],
                        'location': None,
                    }
                ],
                'temp_claims': [
                    {
                        'temp_claim_id': 'c1',
                        'temp_event_id': 'e1',
                        'claimant': 'Monitoring group',
                        'text': 'The reported details could not be independently verified.',
                        'topic': 'verification',
                        'stance': 'uncertain',
                    }
                ],
            }
            return json.dumps(result, ensure_ascii=False)

        return json.dumps({'temp_events': [], 'temp_claims': []}, ensure_ascii=False)

    @staticmethod
    def _extract_chunk_text(prompt: str) -> str:
        marker = 'Chunk text:\n'
        if marker in prompt:
            return prompt.split(marker, maxsplit=1)[1].strip()
        return prompt


class DeepSeekLLMClient:
    """DeepSeek client using OpenAI-compatible chat completion API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int = 60,
    ) -> None:
        resolved_api_key = api_key if api_key is not None else os.getenv('DEEPSEEK_API_KEY')
        if resolved_api_key is None or resolved_api_key.strip() == '':
            raise ValueError('DEEPSEEK_API_KEY is required for DeepSeekLLMClient')

        resolved_base_url = base_url if base_url is not None else os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        resolved_model = model if model is not None else os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

        self.api_key = resolved_api_key
        self.base_url = resolved_base_url.rstrip('/')
        self.model = resolved_model
        self.timeout_seconds = timeout_seconds

    def complete(self, prompt: str) -> str:
        url = f'{self.base_url}/v1/chat/completions'
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': prompt},
            ],
            'temperature': 0.0,
        }

        req = request.Request(
            url=url,
            data=json.dumps(payload).encode('utf-8'),
            method='POST',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
        )

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                body = resp.read().decode('utf-8')
        except Exception as exc:  # pragma: no cover - network path
            raise ValueError(f'DeepSeek request failed: {exc}') from exc

        try:
            data = json.loads(body)
            return str(data['choices'][0]['message']['content'])
        except Exception as exc:  # pragma: no cover - network path
            raise ValueError('DeepSeek response is missing choices[0].message.content') from exc


def get_llm_client(provider: str = 'mock') -> LLMClient:
    normalized = provider.strip().lower()
    if normalized == 'mock':
        return MockLLMClient()
    if normalized == 'deepseek':
        return DeepSeekLLMClient()
    raise ValueError(f'Unknown llm provider: {provider}')
