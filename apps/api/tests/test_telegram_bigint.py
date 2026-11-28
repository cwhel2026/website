from sqlalchemy import BigInteger
from app.models.notifications import TelegramConversationMessage, TelegramProcessedUpdate


def test_telegram_chat_id_columns_support_large_identifiers():
    for model in (TelegramConversationMessage, TelegramProcessedUpdate):
        assert isinstance(model.__table__.c.chat_id.type, BigInteger)
