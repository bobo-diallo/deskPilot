"""Tests réels : appellent vraiment Claude (quelques centimes). Ignorés sans clé API."""

import os
from pathlib import Path

import pytest

from app.domains.extraction.extractors.claude import ClaudeExtractor
from app.domains.extraction.schemas import Invoice
from app.domains.extraction.validation import validate_invoice
from app.domains.llm.providers.anthropic import AnthropicProvider
from app.domains.llm.service import LLMService

DEMO_DIR = Path(__file__).resolve().parents[3] / "demo-data" / "invoices"
MEDIA_TYPES = {".pdf": "application/pdf", ".png": "image/png"}
DEMO_FILES = sorted(p for p in DEMO_DIR.iterdir() if p.suffix in MEDIA_TYPES)


@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY absente")
@pytest.mark.parametrize("path", DEMO_FILES, ids=lambda p: p.name)
def test_demo_invoice_is_extracted_as_expected(session, path):
    expected = Invoice.model_validate_json(path.with_suffix(".expected.json").read_text())
    extractor = ClaudeExtractor(LLMService(AnthropicProvider(), session))

    result = extractor.extract(path.read_bytes(), MEDIA_TYPES[path.suffix]).data

    assert result.invoice_number == expected.invoice_number
    assert result.issue_date == expected.issue_date
    assert result.currency == expected.currency
    assert result.subtotal == expected.subtotal
    assert result.total == expected.total
    assert len(result.lines) == len(expected.lines)
    assert result.supplier_name.lower() == expected.supplier_name.lower()
    assert validate_invoice(result) == []
