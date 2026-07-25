from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from enum import Enum
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy import Index, Numeric
from sqlalchemy.sql.sqltypes import Integer, DateTime, String
from core.models.base import Base

if TYPE_CHECKING:
    from .hotel import Room
    from .payment import Payment
    from .user import User


class ReservationStatus(str, Enum):
    PENDING = "pending"        # Ожидает подтверждения/оплаты
    CONFIRMED = "confirmed"    # Оплачено и подтверждено (номер забронирован)
    CANCELLED = "cancelled"    # Отменено (пользователем или по таймауту)
    COMPLETED = "completed"    # Завершено


class Reservation(Base):
    __tablename__ = "reservations"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rooms.id"), comment="Внешний ключ к номеру", nullable=False
    )
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="Сумма")
    status: Mapped[ReservationStatus] = mapped_column(
        String(20), nullable=False, default=ReservationStatus.PENDING, comment="Статус бронирования"
    )
    date_from: Mapped[date] = mapped_column(
        DateTime(timezone=True), comment="Дата от", nullable=False
    )
    date_to: Mapped[date] = mapped_column(
        DateTime(timezone=True), comment="Дата до", nullable=True
    )

    # Связи
    room: Mapped["Room"] = relationship("Room",
                                        uselist=False,
                                        back_populates="reservations",
                                        )
    payment: Mapped[Optional["Payment"]] = relationship(
        "Payment", back_populates="reservation", uselist=False
    )
    user: Mapped["User"] = relationship(
        "User",
        uselist=False,
        back_populates="reservations",
    )

    __table_args__ = (
        Index("idx_reservation_room_dates", "room_id", "date_from", "date_to"),
    )
