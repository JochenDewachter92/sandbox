import os
from typing import List, Dict, Any
from openai import AzureOpenAI


class TextClassifier:
    """
    Reusable text classifier powered by Azure OpenAI Chat Completions.

    Configure via arguments or environment variables:
      - AZURE_OPENAI_API_KEY
      - AZURE_OPENAI_ENDPOINT
      - AZURE_OPENAI_API_VERSION (default: 2024-12-01-preview)
      - AZURE_OPENAI_MODEL_NAME
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        endpoint: str | None = None,
        api_version: str | None = None,
        model_name: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        self.model_name = model_name or os.getenv("AZURE_OPENAI_MODEL_NAME")

        if not self.api_key:
            raise ValueError("Missing Azure OpenAI API key. Set AZURE_OPENAI_API_KEY or pass api_key.")
        if not self.endpoint:
            raise ValueError("Missing Azure OpenAI endpoint. Set AZURE_OPENAI_ENDPOINT or pass endpoint.")
        if not self.model_name:
            raise ValueError("Missing model name. Set AZURE_OPENAI_MODEL_NAME or pass model_name.")

        self._client = AzureOpenAI(
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
        )

    def classify(
        self,
        text: str,
        labels: List[str],
        label_descriptions: Dict[str, str] | None = None,
    ) -> Dict[str, Any]:
        """
        Classify `text` into one of `labels` and return:
          {"label": "<one of labels>", "confidence": <0..1>}
        """
        if not labels:
            raise ValueError("`labels` must contain at least one label.")

        labels = [str(l) for l in labels]

        output_schema = {
            "type": "object",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "The chosen classification label",
                    "enum": labels,
                },
                "confidence": {
                    "type": "number",
                    "description": "Model's certainty for the chosen label between 0 and 1",
                    "minimum": 0,
                    "maximum": 1,
                },
            },
            "required": ["label", "confidence"],
            "additionalProperties": False,
        }

        # Compose label context for the user message
        if label_descriptions:
            # Build bullet list including optional description per label
            label_lines = []
            for label in labels:
                desc = label_descriptions.get(label)
                if desc:
                    label_lines.append(f"- {label}: {desc}")
                else:
                    label_lines.append(f"- {label}")
            labels_block = "\n".join(label_lines)
            labels_section = f"Labels (with descriptions):\n{labels_block}"
        else:
            labels_section = f"Labels: {labels}"

        response = self._client.chat.completions.create(
            model=self.model_name,
            temperature=0,
            top_p=1,
            max_tokens=50,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "classification_result",
                    "schema": output_schema,
                },
            },
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a deterministic text classifier. "
                        "Choose the single best label from the provided enum and estimate a confidence in [0,1]."
                    ),
                },
                {
                    "role": "user",
                    "content": f"{labels_section}\n\nText:\n{text}",
                },
            ],
        )

        msg = response.choices[0].message
        if hasattr(msg, "parsed") and msg.parsed:
            return msg.parsed  # type: ignore[return-value]
        import json as _json
        return _json.loads(msg.content)  # type: ignore[no-any-return]


