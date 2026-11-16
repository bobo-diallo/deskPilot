# 03 — Base de données avec SQLAlchemy

## Les choix
- **SQLite** : une base dans un seul fichier, sans serveur à installer. Parfait pour démarrer.
  On migrera vers PostgreSQL en V2 (c'est prévu, et SQLAlchemy rend ça facile).
- **SQLAlchemy** : un ORM, c'est-à-dire un outil qui traduit des classes Python en tables.
  Équivalent de Doctrine. Alternative écartée : écrire du SQL à la main (plus de code
  répétitif, plus de risques d'erreurs).

## Un modèle = une table
`backend/app/domains/conversations/models.py` :

```python
class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
```
- `Base` : la classe mère de tous les modèles (définie dans `core/database.py`).
- `Mapped[int]` : « une colonne de type entier ». Sans `Optional`, la colonne est obligatoire
  (`NOT NULL`).
- `mapped_column(...)` : précise les détails de la colonne (clé primaire, valeur par défaut).
- `default=_now` : fonction appelée à l'insertion pour remplir la date.

## Les relations
Une conversation a plusieurs messages (relation « un à plusieurs »). Dans `Message` :

```python
conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
conversation: Mapped[Conversation] = relationship(back_populates="messages")
```
- `ForeignKey` : la clé étrangère réelle dans la base.
- `relationship` : le raccourci Python pour naviguer. `conversation.messages` donne la liste,
  `message.conversation` donne la conversation.
- `cascade="all, delete-orphan"` : supprimer une conversation supprime ses messages.

## Les cinq tables de la story 00
| Table | Rôle |
|---|---|
| `conversations`, `messages` | Les échanges avec l'agent |
| `documents` | Les fichiers déposés |
| `chunks` | Les extraits de texte d'un document (pour le RAG) |
| `api_calls` | Le journal de chaque appel à un modèle : tokens, coût, latence |

## Création des tables : `create_all`
`backend/app/core/database.py` contient `init_database`, appelée au démarrage :
```python
Base.metadata.create_all(engine)
```
Elle crée les tables qui n'existent pas encore. **Limite** : elle ne modifie pas une table
existante. Quand le schéma évoluera (V2, PostgreSQL), on introduira **Alembic**, l'outil de
migrations (comme les migrations Laravel ou Doctrine).

## La session
```python
with Session(engine) as session:
    session.add(conversation)
    session.commit()
```
Une **session** est une « unité de travail » : on y ajoute des objets, puis `commit()`
écrit tout d'un coup dans la base (ou rien, en cas de problème).

## À essayer
```bash
sqlite3 backend/data/deskpilot.db ".tables"
sqlite3 backend/data/deskpilot.db ".schema messages"
```

## Exercice
Ajoute à `Message` une colonne `model` (le nom du modèle qui a répondu). Écris d'abord un
test qui l'utilise. Que se passe-t-il pour la base existante ? (Indice : `create_all`
ne modifie pas une table déjà créée ; supprime le fichier `.db` pour la recréer.)
