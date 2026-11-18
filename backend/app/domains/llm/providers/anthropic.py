import base64

import anthropic
from pydantic import ValidationError

from app.domains.llm.errors import LLMInvalidOutputError, LLMRefusedError
from app.domains.llm.schemas import LLMAttachment, LLMRequest, LLMResponse


def _attachment_block(attachment: LLMAttachment) -> dict:
    """Traduit un fichier joint en bloc de contenu Anthropic (données encodées en base64)."""
    if attachment.media_type == "application/pdf":
        block_type = "document"
    elif attachment.media_type in ("image/png", "image/jpeg"):
        block_type = "image"
    else:
        raise ValueError(f"Type de fichier non pris en charge : {attachment.media_type}")
    return {
        "type": block_type,
        "source": {
            "type": "base64",
            "media_type": attachment.media_type,
            "data": base64.standard_b64encode(attachment.data).decode("ascii"),
        },
    }


def _build_messages(request: LLMRequest) -> list[dict]:
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    if request.attachments:
        # Les fichiers sont placés avant le texte du dernier message.
        last = messages[-1]
        blocks = [_attachment_block(a) for a in request.attachments]
        blocks.append({"type": "text", "text": last["content"]})
        last["content"] = blocks
    return messages


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
            "messages": _build_messages(request),
        }
        if request.system is not None:
            params["system"] = request.system

        if request.response_schema is not None:
            # `parse` contraint la réponse au schéma et la valide pour nous.
            try:
                message = self._client.messages.parse(
                    output_format=request.response_schema, **params
                )
            except ValidationError as error:
                # Le modèle a répondu, mais pas dans le format demandé (ex. « 12 euros 97 » dans
                # un champ décimal). Erreur du modèle, pas un bogue : on la nomme clairement.
                raise LLMInvalidOutputError(
                    f"La réponse de {request.model} ne respecte pas le schéma demandé"
                ) from error
            parsed = message.parsed_output
        else:
            message = self._client.messages.create(**params)
            parsed = None

        if message.stop_reason == "refusal":
            raise LLMRefusedError(f"Le modèle {request.model} a refusé de répondre")

        # La réponse est une liste de blocs (texte, réflexion...) : on ne garde que le texte.
        text = "".join(block.text for block in message.content if block.type == "text")
        return LLMResponse(
            text=text,
            model=message.model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            parsed=parsed,
        )
