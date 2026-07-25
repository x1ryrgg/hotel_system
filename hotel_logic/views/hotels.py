from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.models import Hotel
from core.models.user import UserRole, User
from core.utils.permissions import RoleChecker
from hotel_logic.dependencies import get_hotel_by_id, check_manager_permissions
from hotel_logic.schemas import HotelCreate, HotelResponse, HotelUpdate
from hotel_logic.cruds import hotel_crud

router = APIRouter(
    prefix="/hotels",
    tags=["Hotels"]
)


@router.post("/", response_model=HotelResponse, status_code=status.HTTP_201_CREATED)
async def create_hotel(
    hotel_in: HotelCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker(UserRole.HOTEL_MANAGER))
):
    """View создания Hotel"""
    return await hotel_crud.create_hotel(hotel_in=hotel_in, user_id=user.id, db=db)


@router.get("/", response_model=List[HotelResponse], status_code=status.HTTP_200_OK)
async def get_all_hotels(db: AsyncSession = Depends(get_db)):
    """View получения всех отелей  """
    return await hotel_crud.get_all_hotels(db=db)


@router.get("/{hotel_id}/", response_model=HotelResponse, status_code=status.HTTP_200_OK)
async def get_hotel(hotel: Hotel = Depends(get_hotel_by_id)):
    """ View получения Hotel по его id """
    return hotel


@router.patch("/{hotel_id}/", response_model=HotelResponse, status_code=status.HTTP_200_OK)
async def patch_hotel(
    hotel_id: int,
    hotel_in: HotelUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker(UserRole.HOTEL_MANAGER))
):
    """ View частичного изменения Hotel """
    hotel = await get_hotel_by_id(hotel_id=hotel_id, db=db, load_relationships=True)
    check_manager_permissions(hotel=hotel, user=user)
    return await hotel_crud.update_hotel(hotel_id=hotel_id, hotel_in=hotel_in, db=db)


@router.delete("/{hotel_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hotel(
    hotel_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker(UserRole.HOTEL_MANAGER))
):
    """ View удаления Hotel """
    hotel = await get_hotel_by_id(hotel_id=hotel_id, db=db, load_relationships=True)
    check_manager_permissions(hotel=hotel, user=user)
    return await hotel_crud.delete_hotel(hotel_id=hotel_id, db=db)
