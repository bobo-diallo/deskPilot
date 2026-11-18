from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.core.database import Base, init_database
from app.domains.conversations.models import Conversation, Message
from app.domains.documents.models import Chunk, Document
from app.domains.llm.models import ApiCall


def test_init_database_creates_all_tables():
    engine = create_engine("sqlite://")

    init_database(engine)

    tables = set(inspect(engine).get_table_names())
    assert tables == {
        "conversations",
        "messages",
        "documents",
        "chunks",
        "api_calls",
        "extractions",
        "transcriptions",
    }


def test_message_is_linked_to_its_conversation():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        conversation = Conversation(title="Test")
        conversation.messages.append(Message(role="user", content="Bonjour"))
        session.add(conversation)
        session.commit()

        assert conversation.messages[0].conversation_id == conversation.id


def test_document_has_chunks_and_api_call_is_recorded():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        document = Document(filename="facture.pdf", media_type="application/pdf")
        document.chunks.append(Chunk(position=0, text="Total : 100 €"))
        session.add(document)
        session.add(
            ApiCall(
                provider="anthropic",
                model="claude-sonnet-5-5",
                input_tokens=10,
                output_tokens=5,
                cost_usd=0.0001,
                latency_ms=120,
            )
        )
        session.commit()

        assert document.chunks[0].document_id == document.id
        assert session.query(ApiCall).count() == 1
