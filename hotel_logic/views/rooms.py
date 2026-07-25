from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.models.user import UserRole, User
from core.utils.permissions import RoleChecker
from hotel_logic.dependencies import get_hotel_by_id, get_room_by_id, check_manager_permissions
from hotel_logic.schemas import RoomCreate, RoomResponse, RoomUpdate
from hotel_logic.cruds import room_crud


router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"]
)


@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_in: RoomCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker(UserRole.HOTEL_MANAGER))
):
    """ View создания Room """
    hotel = await get_hotel_by_id(hotel_id=room_in.hotel_id, db=db, load_relationships=True)
    check_manager_permissions(hotel=hotel, user=user)
    return await room_crud.create_room(room_in=room_in, db=db)


@router.get("/hotel/{hotel_id}/", response_model=List[RoomResponse], status_code=status.HTTP_200_OK)
async def get_all_rooms_by_hotel(hotel_id: int, db: AsyncSession = Depends(get_db)):
    """ View получения всех номеров отеля """
    return await room_crud.get_all_rooms(hotel_id=hotel_id, db=db)


@router.get("/{room_id}/", response_model=RoomResponse, status_code=status.HTTP_200_OK)
async def get_room(room_id: int, db: AsyncSession = Depends(get_db)):
    """ View получения Room"""
    return await get_room_by_id(room_id=room_id, db=db, load_relationships=True)


@router.patch("/{room_id}/", response_model=RoomResponse, status_code=status.HTTP_200_OK)
async def patch_room(
    room_id: int,
    room_in: RoomUpdate,
    user: User = Depends(RoleChecker(UserRole.HOTEL_MANAGER)),
    db: AsyncSession = Depends(get_db)
):
    """ View частичного изменения Room """
    room = await get_room_by_id(room_id=room_id, db=db, load_relationships=True)
    check_manager_permissions(hotel=room.hotel, user=user)
    return await room_crud.update_room(room_id=room_id, room_in=room_in, db=db)


@router.delete("/{room_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker(UserRole.HOTEL_MANAGER))
):
    """ View удаления Room"""
    room = await get_room_by_id(room_id=room_id, db=db, load_relationships=True)
    check_manager_permissions(hotel=room.hotel, user=user)
    return await room_crud.delete_room(room_id=room_id, db=db)