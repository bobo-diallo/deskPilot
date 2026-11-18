import re

DEFAULT_MAX_CHARS = 600


def _split_sentences(paragraph: str) -> list[str]:
    # Coupe après « . », « ! » ou « ? » suivi d'une espace : la ponctuation reste à sa phrase.
    return re.split(r"(?<=[.!?])\s+", paragraph)


def _pack(sentences: list[str], max_chars: int) -> list[str]:
    """Regroupe des phrases consécutives tant que le morceau reste sous la limite."""
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}" if current else sentence
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def split_into_chunks(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> list[str]:
    """Découpe un texte en morceaux, un par paragraphe (ligne vide = séparateur).

    Dans un contrat, un paragraphe est une clause : la garder entière donne des morceaux qui
    veulent dire quelque chose. Un paragraphe trop long est coupé entre deux phrases, jamais
    au milieu d'un mot. Une phrase seule plus longue que la limite reste entière.
    """
    chunks: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = " ".join(paragraph.split())  # espaces et retours à la ligne normalisés
        if not paragraph:
            continue
        if len(paragraph) <= max_chars:
            chunks.append(paragraph)
        else:
            chunks.extend(_pack(_split_sentences(paragraph), max_chars))
    return chunks
