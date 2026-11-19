from pathlib import Path

from sqlalchemy.orm import Session

from app.domains.agent.tools.base import ToolRegistry
from app.domains.agent.tools.invoices import CheckInvoiceTool, ExportInvoicesTool, ListInvoicesTool
from app.domains.agent.tools.search import SearchDocumentsTool
from app.domains.search.ports import Embedder
from app.domains.search.service import SearchService


def build_registry(session: Session, embedder: Embedder, export_dir: Path) -> ToolRegistry:
    """Les quatre outils de l'agent. Un seul endroit : l'API et l'évaluation utilisent le même."""
    return ToolRegistry(
        [
            SearchDocumentsTool(SearchService(session, embedder)),
            ListInvoicesTool(session),
            CheckInvoiceTool(session),
            ExportInvoicesTool(session, export_dir),
        ]
    )
