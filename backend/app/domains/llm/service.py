import time

from sqlalchemy.orm import Session

from app.domains.llm.models import ApiCall
from app.domains.llm.ports import LLMProvider
from app.domains.llm.pricing import compute_cost_usd
from app.domains.llm.schemas import LLMRequest, LLMResponse


class LLMService:
    """Appelle un fournisseur et enregistre chaque appel dans le journal des coûts."""

    def __init__(self, provider: LLMProvider, session: Session):
        self._provider = provider
        self._session = session

    def complete(self, request: LLMRequest) -> LLMResponse:
        started_at = time.perf_counter()
        response = self._provider.complete(request)
        latency_ms = round((time.perf_counter() - started_at) * 1000)

        # Le coût est calculé avant d'écrire : un modèle sans tarif lève une erreur
        # et rien n'est enregistré.
        cost_usd = compute_cost_usd(response.model, response.input_tokens, response.output_tokens)
        self._session.add(
            ApiCall(
                provider=self._provider.name,
                model=response.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
                task=request.task.value if request.task else None,
            )
        )
        self._session.commit()
        return response
