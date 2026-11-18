# 10 — De la voix au texte (story 04)

## Pourquoi c'est le seul endroit où on sort de Claude
Claude lit des textes, des PDF et des images, mais **ne transcrit pas l'audio**. Pour une
facture dictée, il faut d'abord un modèle de reconnaissance vocale (ASR). On prend **Whisper**,
un modèle ouvert, qui tourne **sur ta machine** : gratuit, et l'enregistrement ne part pas en
ligne. Seul le texte transcrit est envoyé à Claude.

## Les notions
| Notion | En une phrase | Où dans le projet |
|---|---|---|
| ASR | Reconnaissance vocale : audio en entrée, texte en sortie | `FasterWhisperTranscriber` |
| Taille du modèle | tiny, base, small… : plus gros = plus juste, plus lent, plus lourd | `WHISPER_MODEL_SIZE` |
| Quantification `int8` | Poids du modèle compressés : rapide sur processeur, peu de perte | `compute_type="int8"` |
| Chargement paresseux | On charge la bibliothèque seulement quand on s'en sert | import dans `_load_model` |
| WER | Taux d'erreurs sur les mots : (substitutions + insertions + suppressions) / mots attendus | `word_error_rate` |
| Générateur Python | Un résultat calculé au fil du parcours, comme `yield` en PHP | `segments` de Whisper |
| Interface (port) | Un contrat que plusieurs implémentations respectent | `Transcriber` |

## Le parcours d'une dictée
`POST /extractions` → type détecté par les premiers octets (`audio/mpeg`…) →
`MediaTypeExtractor` aiguille vers `AudioExtractor` → Whisper transcrit → Claude Haiku structure
le texte → contrôle des montants → extraction **et** transcription enregistrées ensemble.

## Fichiers
- `domains/transcription/` : `ports.py`, `schemas.py`, `errors.py`, `models.py`, `transcribers/`
- `domains/extraction/extractors/audio.py` et `dispatch.py`
- `evaluation/spoken.py` (texte dicté), `audio_render.py` (voix de synthèse), `scripts/generate_eval_audio.py`

## Ce que l'évaluation a appris (rapport `docs/evaluation/2026-11-17-audio-whisper-sizes.md`)
1. **Une phrase courte trompe.** Mon premier essai (une phrase de 11 s) était presque parfait.
   Une facture de 50 s pleine de chiffres fait dire à `base` « 671 euros 25 centimes » pour
   « 6 à 31,25 euros ». *Un essai sur un exemple facile ne prouve rien.*
2. **La taille compte beaucoup.** Sur 24 essais, tiny en réussit 11, base 13 et small 22.
   `small` devient la valeur par défaut. Écart d'exactitude moyenne par champ, small contre
   tiny : +51,2 points, intervalle [+37,1 ; +64,2].
3. **Même `small` ne donne aucune facture parfaite.** Les noms propres (« Morrow » pour Moreau)
   et les descriptions (« langue de bureau ») s'entendent mal. Montants et date exacts : 25 %.
4. **La règle posée à l'avance ne servait à rien.** Elle demandait la facture parfaite ; tout
   étant à 0 %, elle n'aurait rien départagé. J'ai ajouté la colonne « montants et date
   exacts » **après coup** et je l'ai signalée comme telle dans le rapport : c'est honnête, mais
   à confirmer sur un jeu neuf.
5. **L'évaluation a trouvé un vrai défaut.** Quand Claude recopiait « 671 euros 25 centimes »
   dans un champ décimal, l'API plantait en 500. Maintenant : `LLMInvalidOutputError`, réponse 502.
6. **La validation voit mal les erreurs de voix.** 8 extractions sur 22 « validées » étaient
   fausses, dont 2 sur les montants ou la date ; le reste sur des noms, invisibles pour un
   contrôle de montants.
7. **Une mesure de vitesse dépend de la machine.** La charge moyenne était à 149 (Docker d'un
   autre projet) : `small` a fait 0,55 fois la durée audio, puis 1,30. Ne pas se fier à ces temps.

## À essayer
1. `http/extractions.http`, exemple « Facture dictée » : regarde le champ `transcript` de la
   réponse, puis compare avec `demo-data/audio/…` (la phrase lue).
2. `.venv/bin/python -m app.evaluation --dataset ../demo-data/eval-audio --variants whisper-small-haiku --runs 1 --limit 2`
   : lis l'estimation avant de dépenser quoi que ce soit.
3. `pytest tests/transcription tests/evaluation/test_spoken.py -v`.

## Exercices
1. Écris un test (d'abord) pour `word_error_rate` : deux mots identiques dans un ordre
   différent, que doit donner la mesure ?
2. Ajoute au texte dicté une ligne « adresse » et observe l'effet sur le taux d'erreurs.
3. Propose une règle pour que les extractions audio soient toujours marquées « à relire », avec
   son test. Quels cas légitimes perdrait-on ?
4. Enregistre ta propre voix pour une facture (téléphone, MP3) et compare avec la voix de
   synthèse : que remarques-tu sur le rapport ?
