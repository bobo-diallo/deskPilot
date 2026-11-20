from app.domains.llm.schemas import LLMRequest, LLMResponse


class FakeProvider:
    """Fournisseur factice : répond toujours la même chose, sans réseau ni coût."""

    name = "fake"

    def __init__(
        self,
        reply: str = "Réponse factice",
        input_tokens: int = 10,
        output_tokens: int = 5,
        parsed: object | None = None,
    ):
        self._reply = reply
        self._input_tokens = input_tokens
        self._output_tokens = output_tokens
        self._parsed = parsed
        self.received: list[LLMRequest] = []

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.received.append(request)
        return LLMResponse(
            text=self._reply,
            model=request.model,
            input_tokens=self._input_tokens,
            output_tokens=self._output_tokens,
            parsed=self._parsed,
        )


class ScriptedProvider:
    """Fournisseur factice qui rejoue une suite de réponses préparées, dans l'ordre.

    Sert à tester un agent : à chaque appel du modèle, la réponse suivante du scénario est
    renvoyée (par exemple « je veux chercher », puis « voici la réponse »). Si l'agent fait plus
    d'appels que prévu, le test échoue clairement au lieu de boucler.
    """

    name = "scripted"

    def __init__(self, responses: list[LLMResponse]):
        self._responses = list(responses)
        self.received: list[LLMRequest] = []

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.received.append(request)
        assert self._responses, "Le script est épuisé : le code a fait plus d'appels que prévu"
        return self._responses.pop(0)
