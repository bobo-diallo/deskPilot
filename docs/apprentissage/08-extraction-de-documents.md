# 08 — Extraire des données d'un document (story 02)

## Le problème
Une facture est un document non structuré (un PDF, une photo). Un programme a besoin de
données structurées : fournisseur, numéro, date, lignes, totaux. L'extraction est le pont
entre les deux. Avec un LLM, c'est facile à faire **et** facile à mal faire : le modèle peut
répondre une valeur plausible mais fausse. Toute la story tourne autour de cette phrase.

```
fichier → POST /extractions → ClaudeExtractor → Invoice (Pydantic)
                                                    │
                                   validation.py : les montants se recoupent-ils ?
                                                    │
                               table extractions : status = validated | needs_review
```

## Les fichiers
| Fichier | Rôle |
|---|---|
| `domains/extraction/schemas.py` | `Invoice` et `InvoiceLine` : la forme des données voulues |
| `domains/extraction/validation.py` | Règles de cohérence, liste d'anomalies |
| `domains/extraction/ports.py` | `DocumentExtractor` : le contrat d'un extracteur |
| `domains/extraction/extractors/claude.py` | Extracteur qui demande à Claude de lire le fichier |
| `domains/extraction/service.py` | Extraire, valider, enregistrer |
| `domains/extraction/models.py` | Table `extractions` |
| `domains/documents/file_types.py` | Détection du vrai type d'un fichier |
| `domains/documents/storage.py` | Rangement des fichiers sur disque |
| `api/extractions.py` | Routes `POST /extractions` et `GET /extractions/{id}` |
| `backend/scripts/generate_demo_invoices.py` | Génère les factures de démonstration |

## Notions

### Pydantic : décrire et valider des données
```python
class Invoice(BaseModel):
    supplier_name: str | None = Field(default=None, description="Nom du fournisseur")
    total: Decimal | None = None
```
Une classe Pydantic décrit une forme de données. Elle sert à trois choses à la fois :
1. **valider** ce qui arrive (un texte à la place d'un nombre est rejeté) ;
2. **documenter** pour FastAPI (la page `/docs` est générée à partir d'elle) ;
3. **contraindre le LLM** : le schéma est envoyé à l'API, qui force la réponse à le respecter.

`str | None` signifie « texte ou absent ». Un champ absent du document vaut `None` :
on demande au modèle de ne jamais inventer.

### Sortie structurée
Sans contrainte, un modèle répond du texte libre, qu'il faudrait parser avec des regex.
Avec `messages.parse(output_format=Invoice, ...)`, l'API garantit un JSON conforme au schéma
et le SDK le transforme en objet `Invoice`. C'est le coeur de `AnthropicProvider`.

### `Decimal` pour l'argent
En Python comme en PHP, `0.1 + 0.2` donne `0.30000000000000004` avec des flottants. Pour
l'argent, on utilise `Decimal`, qui calcule en base 10 exacte. Piège vu en pratique : le JSON
`45.00` revient comme `Decimal("45")` (les zéros inutiles disparaissent), ce qui est
mathématiquement identique. On compare des valeurs, pas des textes.

### Valider ≠ avoir raison
`validate_invoice` recoupe les montants :
- chaque ligne : quantité × prix unitaire = total de la ligne ;
- somme des lignes = total hors taxes ;
- hors taxes + taxes = total ;
- champs obligatoires présents.

Une tolérance d'un centime absorbe les arrondis. S'il y a une anomalie, le statut devient
`needs_review` : un humain relit (c'est l'écran « Revue » à venir). Honnêtement, l'API ne
donne pas de probabilité par champ ; **ces recoupements sont notre mesure de confiance**.
Limite : une erreur cohérente (le modèle lit 45 au lieu de 54 partout) passe entre les
mailles. C'est pourquoi la story 03 mesurera la précision sur des factures annotées.

### Envoyer un fichier à une API (multipart)
Un formulaire avec fichier utilise `multipart/form-data`. FastAPI le lit avec `UploadFile`
(le fichier) et `Form()` (les autres champs) ; il faut le paquet `python-multipart`.

### Ne pas croire le client
Le nom `facture.pdf` et le type déclaré peuvent mentir. `detect_media_type` lit les premiers
octets : un PDF commence toujours par `%PDF-`, un PNG par `\x89PNG`. Un fichier qui ne
correspond à rien reçoit une erreur 415. La taille est limitée (10 Mo, erreur 413) : on lit un
octet de plus que la limite pour savoir si le fichier la dépasse sans tout charger.

### Pourquoi `DocumentExtractor` est une interface
Aujourd'hui Claude lit le document. En story 03, un extracteur local (Docling, open source)
pourra s'ajouter derrière la même interface, et on comparera les deux sur les mêmes factures.
Le service et les routes ne changeront pas.

## Les données de démonstration
`demo-data/invoices/` contient 3 factures fictives : deux PDF (dont une canadienne avec TPS et
TVQ) et une image légèrement inclinée qui simule un scan. Chacune a un fichier
`.expected.json` : la **vérité terrain**. Le script qui les génère vérifie lui-même que les
totaux sont cohérents. Les tests réels comparent ce que Claude extrait à ces fichiers.

## Coût et vitesse mesurés
> **Mis à jour en story 03 :** l'extraction utilise maintenant Haiku 5.5 (environ 0,0006 $ par
> facture). Les chiffres ci-dessous sont ceux de Sonnet 5.5, mesurés en story 02.

Une facture PDF d'une page : environ 3 200 tokens en entrée, 200 en sortie, soit 0,008 $ et
3 secondes avec Sonnet 5.5. Un PDF compte en tokens à la fois pour son texte et pour ses
images de page.

## À essayer
1. Ouvre `http/extractions.http`, envoie la première requête, observe `status` et `data`.
2. Envoie l'image `facture-quincaillerie-dupont.png` : un scan lu aussi bien qu'un PDF.
3. Relis le journal : `sqlite3 backend/data/deskpilot.db "select * from extractions;"`
   (le nom du fichier est `deskpilot.db`).
4. Lance les tests réels : `ANTHROPIC_API_KEY=... pytest tests/extraction/test_real_extraction.py`.

## Exercice
Modifie une copie de `facture-atelier-nord.expected.json` (change un total) et passe-la à
`validate_invoice` dans un test : quelle anomalie est détectée ? Puis imagine une erreur
que les règles **ne** détecteraient pas, et note-la : elle servira de cas de test à la story 03.
