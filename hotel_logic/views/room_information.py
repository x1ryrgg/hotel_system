from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.models import RoomInformation
from core.models.user import UserRole, User
from core.utils.permissions import RoleChecker
from hotel_logic.dependencies import get_room_information_by_id
from hotel_logic.schemas import RoomInformationResponse, RoomInformationCreate, RoomInformationUpdate
from hotel_logic.cruds import room_crud


router = APIRouter(
    prefix="/room-information",
    tags=["Room Information"]
)


@router.post("/", response_model=RoomInformationResponse, status_code=status.HTTP_201_CREATED)
async def create_room_information(
    room_information_in: RoomInformationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker(UserRole.HOTEL_MANAGER))
):
    """ View создания RoomInformation """
    return await room_crud.create_room_information(room_information_in=room_information_in, db=db)


@router.get("/all/", response_model=List[RoomInformationResponse], status_code=status.HTTP_200_OK)
async def get_all_room_information(db: AsyncSession = Depends(get_db)):
    """ View получения всех RoomInformation  """
    return await room_crud.get_all_hotel_information(db=db)


@router.get("/{room_info_id}/", response_model=RoomInformationResponse, status_code=status.HTTP_200_OK)
async def get_room_information(room_info: RoomInformation = Depends(get_room_information_by_id)):
    """ View получения RoomInformation по его id """
    return room_info


@router.patch("/{room_info_id}/", response_model=RoomInformationResponse, status_code=status.HTTP_200_OK)
async def patch_room_information(
    room_info_id: int,
    room_info_in: RoomInformationUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker(UserRole.HOTEL_MANAGER))
):
    """ View частичного обновления RoomInformation """
    return await room_crud.update_room_information(room_info_id=room_info_id, room_info_in=room_info_in, db=db)


@router.delete("/{room_info_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room_information(
    room_info_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(RoleChecker(UserRole.HOTEL_MANAGER))
):
    """ View удаления RoomInformation """
    return await room_crud.delete_room_information(room_info_id=room_info_id, db=db)