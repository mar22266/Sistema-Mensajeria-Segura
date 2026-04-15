import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.auth.baseDatos import Base


# clase de modelo para la tabla de grupos en la base de datos
class Grupo(Base):
    __tablename__ = "grupos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    creadoPor: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False
    )
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# clase de modelo para la tabla de miembros de grupos en la base de datos
class GrupoMiembro(Base):
    __tablename__ = "grupos_miembros"
    __table_args__ = (
        UniqueConstraint("groupId", "userId", name="uq_grupos_miembros_group_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    groupId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grupos.id"), nullable=False, index=True
    )
    userId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True
    )
    addedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# clase de modelo para la tabla de mensajes en la base de datos
class Mensaje(Base):
    __tablename__ = "mensajes"
    __table_args__ = (
        CheckConstraint(
            '(("recipientId" IS NOT NULL AND "groupId" IS NULL) OR ("recipientId" IS NULL AND "groupId" IS NOT NULL))',
            name="ck_mensajes_individual_o_grupal",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    senderId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True
    )
    recipientId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True, index=True
    )
    groupId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grupos.id"), nullable=True, index=True
    )
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    encryptedKey: Mapped[str | None] = mapped_column(Text, nullable=True)
    nonce: Mapped[str] = mapped_column(String(24), nullable=False)
    authTag: Mapped[str] = mapped_column(String(24), nullable=False)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# clase de modelo para la tabla de destinatarios de mensajes en la base de datos
class MensajeDestinatario(Base):
    __tablename__ = "mensajes_destinatarios"
    __table_args__ = (
        UniqueConstraint(
            "messageId", "userId", name="uq_mensajes_destinatarios_message_user"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    messageId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mensajes.id"), nullable=False, index=True
    )
    userId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True
    )
    encryptedKey: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
