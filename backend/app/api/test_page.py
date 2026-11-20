from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

# Page de test pour le développement : elle appelle les mêmes routes que n'importe quel client.
# Elle n'est pas l'interface du produit (voir story 06b).
router = APIRouter(tags=["test"])

_PAGE = Path(__file__).parent / "test_page.html"


@router.get("/test-page", include_in_schema=False)
def test_page() -> FileResponse:
    return FileResponse(_PAGE, media_type="text/html")
