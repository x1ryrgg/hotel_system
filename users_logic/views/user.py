from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from starlette import status

from users_logic.dependencies import get_user_by_id
from core.models.user import UserRole
from core.utils.permissions import get_current_user, RoleChecker
from users_logic.schemas.schemas import UserResponse, UserUpdate
from fastapi import Depends, APIRouter
from core.models.user import User
from users_logic import crud


router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/all/", response_model=List[UserResponse])
async def get_all_users(_=Depends(RoleChecker(UserRole.ADMIN)), db: AsyncSession = Depends(get_db)):
    return await crud.get_all_users(db=db)


@router.get("/profile/", response_model=UserResponse)
async def user_info_view(user: User = Depends(get_current_user)):
    return user


@router.get("/{user_id}/", response_model=UserResponse)
async def view_get_user(user: User = Depends(get_user_by_id)):
    return user


# @router.post("/create/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
#     return await crud.create_user(user_in=user, db=db)


@router.delete("/{user_id}/delete/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.delete_user(user_id=user_id, db=db)


@router.patch("/{user_id}/update/", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def patch_user(user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    """
    Частичное обновление пользователя.
    Обновляются только переданные поля.
    """
    return await crud.update_user(user_id=user_id, user_in=user_update, db=db)
