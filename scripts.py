import random

from core.database import async_session_maker
from core.models.hotel import Hotel, RoomInformation, UserHotel, Room, RoomType
from core.models.user import User, UserRole
import asyncio
from dotenv import load_dotenv
from sqlalchemy.sql import select
from sqlalchemy.orm import joinedload, selectinload
from users_logic.security import hash_password, verify_password
from core.utils.mailing import email_service

load_dotenv()


USER_NAMES = ["alex", "john", "maria", "elena", "dmitry"]

HOTELS_DATA = [
    {
        "name": "Grand Palace Hotel",
        "city": "Москва",
        "address": "ул. Тверская, д. 12",
        "region": "Московская область",
        "stars": 5,
        "phone": "+74951234567",
        "email": "info@grandpalace.ru",
        "description": "Роскошный отель в самом центре столицы."
    },
    {
        "name": "Seaside Resort & Spa",
        "city": "Сочи",
        "address": "Курортный проспект, д. 85",
        "region": "Краснодарский край",
        "stars": 4,
        "phone": "+78622998877",
        "email": "booking@seaside.ru",
        "description": "Отель на первой линии с собственным пляжем."
    },
    {
        "name": "Comfort Inn",
        "city": "Санкт-Петербург",
        "address": "Невский проспект, д. 45",
        "region": "Ленинградская область",
        "stars": 3,
        "phone": "+78125553322",
        "email": "stay@comfortinn.spb.ru",
        "description": "Уютный отель для бизнес-поездок и туристов."
    }
]

# Наборы характеристик номеров
ROOM_INFO_DATA = [
    {"type": RoomType.SINGLE, "price_per_night": 2500.0, "capacity": 1, "size": 18.0},
    {"type": RoomType.DOUBLE, "price_per_night": 4500.0, "capacity": 2, "size": 25.0},
    {"type": RoomType.TWIN, "price_per_night": 4200.0, "capacity": 2, "size": 24.0},
    {"type": RoomType.SUITE, "price_per_night": 9000.0, "capacity": 3, "size": 45.0},
    {"type": RoomType.FAMILY, "price_per_night": 7000.0, "capacity": 4, "size": 38.0},
]


async def seed_database():
    async with async_session_maker() as session:
        # 1. Проверяем, есть ли уже данные (чтобы не дублировать при повторном запуске)
        existing_user = await session.scalar(select(User).limit(1))
        if existing_user:
            print("⚠️ База данных уже содержит данные. Пропускаем сидирование.")
            return

        print("🚀 Начинаем заполнение базы данных...")
        password_hash = hash_password("12345678")

        # 2. Создаем системных пользователей
        root_user = User(
            username="root",
            password=password_hash,
            email="root@inbox.ru",
            role=UserRole.ADMIN
        )
        manager_user = User(
            username="manager",
            password=password_hash,
            email="manager@inbox.ru",
            role=UserRole.HOTEL_MANAGER
        )
        session.add_all([root_user, manager_user])

        # 3. Создаем обычных клиентов (Customers)
        created_customers = []
        for username in USER_NAMES:
            user = User(
                username=username,
                email=f"{username}@example.com",
                password=password_hash,
                role=UserRole.CUSTOMER
            )
            created_customers.append(user)
            session.add(user)

        # 4. Создаем типы комнат (RoomInformation)
        room_infos = [RoomInformation(**info) for info in ROOM_INFO_DATA]
        session.add_all(room_infos)

        # Флашим сессию, чтобы получить сгенерированные ID для связей
        await session.flush()

        # 5. Создаем отели и связываем их с Менеджером (M2M через UserHotel)
        for h_data in HOTELS_DATA:
            hotel = Hotel(**h_data)
            session.add(hotel)
            await session.flush()  # Получаем hotel.id

            # Привязываем отель к менеджеру через промежуточную таблицу
            user_hotel_link = UserHotel(user_id=manager_user.id, hotel_id=hotel.id)
            session.add(user_hotel_link)

            # 6. Создаем физические комнаты (Rooms) для каждого отеля
            # Например: 3 этажа по 4 комнаты на каждом
            for floor in range(1, 4):
                for num in range(1, 5):
                    room_number = floor * 100 + num  # 101, 102... 201, 202...
                    selected_info = random.choice(room_infos)

                    room = Room(
                        hotel_id=hotel.id,
                        info_id=selected_info.id,
                        floor=floor,
                        number=room_number
                    )
                    session.add(room)

        # 7. Финальный коммит всей транзакции
        await session.commit()
        print("База данных успешно заполнена тестовыми данными")


async def check_orm_results():
    async with async_session_maker() as session:
        result = await session.execute(select(User).options(joinedload(User.hotels)).where(User.id == 1))
        users = result.unique().scalars().all()

        for user in users:
            print(f"USER {user.username}")
            for hotel in user.hotels:
                print(f"HOTEL {hotel.name}")


async def check_selectinload():
    # selectinload работает хорошо к связи один ко многим и уникальные значения сразу берет не надо unique
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).options(
                selectinload(User.hotels)
            ).order_by(User.id)
        )

        users = result.scalars().all()

        for user in users:
            print(f"\nUSER {user.username}")
            for hotel in user.hotels:
                print(f"HOTEL {hotel.name}")


async def check_code_decode_system():
    async with async_session_maker() as session:
        stmt = await session.execute(select(User).where(User.id == 119))
        user = stmt.scalar_one_or_none()

        password = user.password

        decode_password = verify_password('12345678', password)

        print(decode_password)

        test_password = "test_password"

        print(hash_password(test_password))


async def send_email_message(to_email, text):
    return await email_service.send_text_email(to_email=to_email, text=text)


if __name__ == "__main__":
    asyncio.run(send_email_message(to_email="Roman.mostovoy.99@mail.ru", text="Ты идиот"))
