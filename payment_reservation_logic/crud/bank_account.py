import random

from fastapi import HTTPException, status

from core.logging_system import logger
from sqlalchemy import select
from core.models.payment import BankAccount
from core.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession


async def generate_account_number(db: AsyncSession) -> str:
    """ Генерация номера счета """
    prefix = "40817810"  # Стандартный префикс физических лиц
    while True:
        random_digits = "".join([str(random.randint(0, 9)) for _ in range(12)])
        acc_number = f"{prefix}{random_digits}"

        # Проверяем, существует ли уже такой номер в БД
        result = await db.execute(
            select(BankAccount).where(BankAccount.account_number == acc_number)
        )
        if not result.scalar_one_or_none():
            return acc_number

async def create_user_bank_account(user: User, db: AsyncSession) -> BankAccount:
    """ Создание личного внутреннего счета для пользователя"""

    result = await db.execute(select(BankAccount).where(BankAccount.user_id == user.id))
    existing_account = result.scalar_one_or_none()

    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У вас уже есть открытый банковский счёт",
        )

    account_number = await generate_account_number(db=db)

    bank_account = BankAccount(user_id=user.id, account_number=account_number)

    db.add(bank_account)
    await db.commit()
    await db.refresh(bank_account, attribute_names=["payments"])
    logger.info(f"[create_user_bank_account] Пользователь #{user.id} (username: {user.username}) "
                f"created BankAccount with number {account_number}")
    return bank_account

