import requests
from typing import List, Dict, Optional
import logging
import time
import re


class LLMClient:
    """Manages communication with the LLM provider."""

    def __init__(self, provider: str, api_key: str, model: str, endpoint: Optional[str]) -> None:
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint

    def get_response(self, messages: List[Dict[str, str]]) -> str:
        """Get a response from the configured LLM provider. 

        Delegates the request to the appropriate handler based on the provider 
        (ex. OpenAI, Bedrock, Vertex AI, Azure OpenAI, Ollama)

        Args:
            messages: A list of message dictionaries representing the chat history, 
            formatted as [{"role": "user | "system" | "assistant", "content":"..."}, ...]

        Returns:
            The LLM's response as a string.

        Raises:
            ValueError: If the configured provider is not supported. 
            RequestException: If the HTTP request to the provider fails (for supported providers).
        """
        if self.provider == "openai":
            return self._call_openai(messages)
        elif self.provider == "bedrock":
            return self._call_bedrock(messages)
        elif self.provider == "vertex":
            return self._call_vertex(messages)
        elif self.provider == "azure":
            return self._call_azure(messages)
        elif self.provider == "ollama":
            return self._call_ollama(messages)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _call_openai(self, messages):
        url = self.endpoint or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        return self._post(url, headers, payload)

    def _call_ollama(self, messages):
        url = self.endpoint or "ollama_url"
        payload = {
            "model": self.model,
            "messages": messages
        }
        return self._post(url, {}, payload)

    def _call_azure(self, messages):
        if not self.endpoint:
            raise ValueError("LLM_ENDPOINT must be set for Azure OpenAI")
        url = f"{self.endpoint}/openai/deployments/{self.model}/chat/completions?api-version=2024-02-15-preview"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        return self._post(url, headers, payload)

    # def _call_bedrock(self, messages):
        # Placeholder: you could use boto3/bedrock-runtime here

    # def _call_vertex(self, messages):
        # Placeholder: use google-cloud-aiplatform SDK

    def _post(self, url, headers, payload):
        max_retries = 5
        base_delay = 1.0  # seconds

        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data['choices'][0]['message']['content']

            except requests.exceptions.HTTPError as e:
                status_code = response.status_code if response else None

                if status_code == 429:
                    logging.warning(
                        "Rate limit hit on attempt %s", attempt + 1)

                    # Parse "Please try again in 1.538s" from the OpenAI error message
                    retry_after = self._get_retry_after_seconds(response)
                    if retry_after is None:
                        # fallback to exponential backoff
                        retry_after = base_delay * (2 ** attempt)

                    logging.warning(
                        f"Retrying after {retry_after:.2f} seconds...")
                    time.sleep(retry_after)
                    continue

                # Log other errors
                logging.error(f"HTTP error calling {self.provider}: {e}")
                logging.error(f"Status code: {status_code}")
                logging.error(
                    f"Response details: {response.text if response else 'No response'}")
                break

            except requests.exceptions.RequestException as e:
                logging.error(f"Non-HTTP error calling {self.provider}: {e}")
                break

        return "I encountered an error due to rate limits or network issues. Please try again later."

    def _get_retry_after_seconds(self, response) -> Optional[float]:
        try:
            error_json = response.json()
            message = error_json.get("error", {}).get("message", "")
            match = re.search(r"try again in ([\d.]+)s", message)
            if match:
                return float(match.group(1))
        except Exception as e:
            logging.debug(f"Failed to parse retry time from response: {e}")
        return None
