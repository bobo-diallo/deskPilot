# Essai Docling en conteneur Linux : sur Mac Intel, PyTorch >= 2.3 n'existe pas, donc pas de
# Docling natif. Les paquets Linux, eux, existent.
FROM python:3.12-slim

# Bibliothèques système requises par OpenCV (utilisé par l'OCR de Docling).
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# PyTorch version CPU d'abord : la version par défaut embarque des bibliothèques GPU de plusieurs Go.
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir docling

WORKDIR /work
COPY convert.py .
CMD ["python", "convert.py"]
