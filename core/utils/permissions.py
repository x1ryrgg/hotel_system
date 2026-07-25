from typing import List, Union

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette import status

from core.database import get_db
from core.models import User
from core.models.user import UserRole

from users_logic.security import decode_token


security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Получение текущего пользователя из Bearer токена."""
    token = credentials.credentials

    # Декодируем токен
    payload = decode_token(token)

    # Проверяем тип токена
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # Извлекаем user_id
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Ищем пользователя в БД
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Проверяем, активен ли пользователь
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user

class RoleChecker:
    """ Ограничение доступа по role пользователя User. """
    def __init__(self, allowed_roles: Union[UserRole, List[UserRole]] = None):
        if allowed_roles is None:
            self.allowed_roles = list(UserRole)
        elif allowed_roles == UserRole.HOTEL_MANAGER:
            self.allowed_roles = [UserRole.HOTEL_MANAGER, UserRole.ADMIN]
        else:
            self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user


