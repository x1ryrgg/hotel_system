import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi import Request, status, HTTPException
from cashews import cache

from core.logging_system import logger
from users_logic.views.user import router as user_router
from users_logic.views.authentication import router as auth_router
from hotel_logic.views.hotels import router as hotel_router
from hotel_logic.views.rooms import router as room_router
from hotel_logic.views.room_information import router as room_information
from payment_reservation_logic.views.payment import router as payment_router
from payment_reservation_logic.views.reservation import router as reservation_router
from payment_reservation_logic.views.bank_account import router as bank_account_router
from core.config import settings
from core.broker_taskiq import broker


# uvicorn main:app --reload - запуск приложение на uvicron
# netstat -ano | findstr :8000 - нахождение активных процессов
# taskkill /PID 7348 /F - завершение активных процессов
# docker exec -it redis-container redis-cli - запуск redis-cli
# taskiq worker core.broker_taskiq:broker core.tasks.senders - запуск taskiq (при нескольких файлах перечислять их)

@asynccontextmanager
async def lifespan(app: FastAPI):
    cache.setup(settings.redis_url)

    if not broker.is_worker_process:
        await broker.startup()

    yield

    if not broker.is_worker_process:
        await broker.shutdown()
    await cache.close()

app = FastAPI(lifespan=lifespan, title='HOTEL API')

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(bank_account_router)
app.include_router(payment_router)
app.include_router(reservation_router)
app.include_router(hotel_router)
app.include_router(room_router)
app.include_router(room_information)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Логируем только важные ошибки (например, 500)
    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    else:
        logger.info(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Логируем полную ошибку с traceback
    logger.error(f"Global error on {request.url.path}: {exc}\n{traceback.format_exc()}")

    # Клиенту отдаем безопасный ответ
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. Please try again later."},
    )


@app.get("/ping/")
async def ping():
    return JSONResponse(content={"response": "PONG"})
