from datetime import datetime, timedelta, timezone, date
import secrets
from abc import ABC, abstractmethod
from decimal import Decimal

from sqlalchemy import select, Result, update
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status

from core.utils.mailing import EmailService
from core.models.hotel import HotelBookStatus
from core.models.reservation import Reservation, ReservationStatus
from core.models.user import User
from core.models.payment import Payment, BankAccount, PaymentStatus, VerificationCode
from hotel_logic.dependencies import get_room_by_id
from payment_reservation_logic.crud.reservation import (
    room_reservation_check,
    calculate_price_booking_range,
)
from payment_reservation_logic.dependencies import get_bank_account_by_user_id, get_payment_by_id
from core.tasks.senders import send_verification_code_email_task, send_text_email_task


class AccountReplenishment(ABC):
    """ Интерфейс сервиса пополнения счета банковского аккаунта BankAccount """

    @abstractmethod
    async def process_top_up(self, amount: Decimal) -> Payment:
        """
        Стадия 1: Создание платежа со статусом PENDING,
        генерация одноразового кода и отправка его на почту.
        """
        pass

    @abstractmethod
    async def confirm_top_up(self, payment_id: int, code: str) -> BankAccount:
        """
        Стадия 2: Проверка введенного кода.
        При успехе: Payment.status -> PAID, BankAccount.balance += amount.
        """
        pass


class DefaultReplenishmentService(AccountReplenishment):
    """ """
    def __init__(self, user: User,
                 db: AsyncSession,
                 code_sender: EmailService):
        self.user = user
        self.db = db
        self.code_sender = code_sender

    @staticmethod
    def generate_verification_code() -> str:
        """Генерация 6-значного кода"""
        code = "".join(secrets.choice("0123456789") for _ in range(6))
        return code

    async def process_top_up(self, amount: Decimal) -> Payment:
        """ """
        bank_account = await get_bank_account_by_user_id(user_id=self.user.id, db=self.db)
        if bank_account.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Аккаунт платежного сервиса заблокирован.",
            )
        # Все предыдущие коды пользователя блокируем
        await self.db.execute(
            update(VerificationCode)
            .where(
                VerificationCode.user_id == self.user.id,
                VerificationCode.is_active == True,
            )
            .values(is_active=False)
        )

        new_payment = Payment(
            account_id=bank_account.id, amount=amount, status=PaymentStatus.PENDING
        )

        VERIFICATION_TIME_LIMIT = datetime.now(timezone.utc) + timedelta(
            minutes=10
        )  # 10 минут
        code = self.generate_verification_code()
        verification_code = VerificationCode(
            user_id=self.user.id,
            code=code,
            is_active=True,
            expires_at=VERIFICATION_TIME_LIMIT,
        )

        self.db.add_all([new_payment, verification_code])
        await self.db.commit()
        await self.db.refresh(new_payment)

        await send_verification_code_email_task.kiq(to_email=self.user.email, code=code)

        return new_payment

    async def confirm_top_up(self, payment_id: int, code: str) -> BankAccount:
        """Проверка кода подтверждения и проведение начисления суммы на аккаунт"""
        bank_account = await get_bank_account_by_user_id(
            user_id=self.user.id, db=self.db, block_update_column=True
        )
        if bank_account.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Аккаунт платежного сервиса заблокирован.",
            )

        payment = await get_payment_by_id(
            payment_id=payment_id,
            account_id=bank_account.id,
            db=self.db,
            block_update_column=True,
            payment_status=PaymentStatus.PENDING,
        )

        stmt_code = (
            select(VerificationCode)
            .where(
                VerificationCode.user_id == self.user.id,
                VerificationCode.code == code,
                VerificationCode.is_active == True,
                VerificationCode.expires_at > datetime.now(timezone.utc),
            )
            .with_for_update() # от race conditions
        )
        res_code: Result = await self.db.execute(stmt_code)
        code_obj = res_code.scalar_one_or_none()

        if not code_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный или просроченный код подтверждения.",
            )

        # Проведение операцию
        code_obj.is_active = False
        payment.status = PaymentStatus.PAID
        bank_account.balance += payment.amount

        await self.db.commit()
        await self.db.refresh(bank_account)
        return bank_account


class BookingService:
    """ """
    def __init__(self, user: User, db: AsyncSession):
        self.user = user
        self.db = db

    async def book_room(self, room_id: int, date_from: date, date_to: date) -> Reservation:
        room = await get_room_by_id(room_id=room_id, db=self.db, load_relationships=True, block_update_column=True)

        room_is_booked = await room_reservation_check(room_id=room_id,
                                                date_from=date_from,
                                                date_to=date_to,
                                                db=self.db)

        if room_is_booked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Комната уже забронирована на выбранные даты.",
            )

        price_per_night = room.room_information.price_per_night
        total_price = calculate_price_booking_range(date_from=date_from,
                                                    date_to=date_to,
                                                    price_per_night=price_per_night)

        bank_account = await get_bank_account_by_user_id(
            user_id=self.user.id, db=self.db, block_update_column=True
        )
        if bank_account.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Аккаунт платежного сервиса заблокирован.",
            )

        if bank_account.balance < total_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недостаточно средств. Требуется: {total_price}, баланс: {bank_account.balance}. "
                       f"Необходимо пополнить счет на {total_price - bank_account.balance} для бронирования.",
            )

        bank_account.balance -= total_price

        room.status = HotelBookStatus.OCCUPIED

        reservation = Reservation(
            user_id=self.user.id,
            room_id=room.id,
            date_from=date_from,
            date_to=date_to,
            total_price=total_price,
            status=ReservationStatus.CONFIRMED,
        )
        self.db.add(reservation)
        await self.db.flush()  # для получения reservation_id без коммита

        payment = Payment(
            account_id=bank_account.id,
            reservation_id=reservation.id,
            amount=total_price,
            status=PaymentStatus.PAID,
        )
        self.db.add(payment)

        # Коммитим всю транзакцию атомарно
        await self.db.commit()
        await self.db.refresh(reservation)
        return reservation
