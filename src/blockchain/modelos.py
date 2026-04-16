from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.auth.baseDatos import Base


# clase de modelo para la tabla de bloques en la base de datos
class BloqueBlockchain(Base):
    __tablename__ = "bloques_blockchain"

    indice: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    senderId: Mapped[str | None] = mapped_column(String(36), nullable=True)
    recipientId: Mapped[str | None] = mapped_column(String(36), nullable=True)
    messageHash: Mapped[str] = mapped_column(String(64), nullable=False)
    previousHash: Mapped[str] = mapped_column(String(64), nullable=False)
    nonce: Mapped[int] = mapped_column(Integer, nullable=False)
    hashActual: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
