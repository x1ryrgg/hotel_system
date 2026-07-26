from fastapi import APIRouter

from core.utils.permissions import RoleChecker
from payment_reservation_logic.crud.reservation import get_user_reservations
from payment_reservation_logic.dependencies import *
from payment_reservation_logic.schemas.reservation import (
    ReservationResponse,
    SimpleReservationResponse, CreateReservationRequest,
)
from payment_reservation_logic.service import BookingService
from core.tasks import send_text_email_task

router = APIRouter(
    prefix='/reservation',
    tags=['reservations']
)


@router.get("/", response_model=List[SimpleReservationResponse], status_code=status.HTTP_200_OK)
async def get_reservations(user: User = Depends(RoleChecker()), db: AsyncSession = Depends(get_db)):
    """ View Возвращает бранирования пользователя """
    return await get_user_reservations(user=user, db=db)


@router.get("/{reservation_id}", response_model=ReservationResponse, status_code=status.HTTP_200_OK)
async def get_user_reservation(reservation_id: int,
                               user: User = Depends(RoleChecker()),
                               db: AsyncSession = Depends(get_db)):
    """ View Получение информации по бронированию """
    return await get_user_reservation_by_id(reservation_id=reservation_id, user_id=user.id, db=db, load_relationships=True)


@router.post("/book", response_model=SimpleReservationResponse, status_code=status.HTTP_201_CREATED)
async def book_hotel_room(dto: CreateReservationRequest,
                          user: User = Depends(RoleChecker()),
                          db: AsyncSession = Depends(get_db)):
    booking_service = BookingService(user=user, db=db)
    reservation = await booking_service.book_room(
        room_id=dto.room_id,
        date_from=dto.date_from,
        date_to=dto.date_to,
    )

    await cache.delete(f"reservations:user:{user.id}")

    await send_text_email_task.kiq(
        to_email=user.email, text="Оплата номера отеля успешна."
    )

    return reservation
