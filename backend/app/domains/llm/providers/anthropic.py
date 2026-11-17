import anthropic

from app.domains.llm.errors import LLMRefusedError
from app.domains.llm.schemas import LLMRequest, LLMResponse


class AnthropicProvider:
    """Fournisseur qui appelle les modèles Claude via le SDK officiel."""

    name = "anthropic"

    def __init__(self, client: anthropic.Anthropic | None = None):
        # Sans client fourni, le SDK lit la clé dans la variable d'environnement ANTHROPIC_API_KEY.
        self._client = client or anthropic.Anthropic()

    def complete(self, request: LLMRequest) -> LLMResponse:
        params = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        }
        if request.system is not None:
            params["system"] = request.system

        message = self._client.messages.create(**params)

        if message.stop_reason == "refusal":
            raise LLMRefusedError(f"Le modèle {request.model} a refusé de répondre")

        # La réponse est une liste de blocs (texte, réflexion...) : on ne garde que le texte.
        text = "".join(block.text for block in message.content if block.type == "text")
        return LLMResponse(
            text=text,
            model=message.model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )
