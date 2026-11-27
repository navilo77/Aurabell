"""Payment router (BE-07)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import User, get_current_user
from app.core.database import get_db
from app.modules.payments.schema import PaymentInitiateRequest, PaymentRead, PaymentInitiateResponse, PaymentVerifyRequest
from app.modules.payments.service import PaymentError, PaymentService
from app.modules.payments.adapter import AmarPayGateway

router = APIRouter(prefix="/payments", tags=["Payments"])


def get_payment_service(db: AsyncSession = Depends(get_db)):
    return PaymentService(db)


@router.post("/initiate", response_model=PaymentInitiateResponse, status_code=status.HTTP_201_CREATED)
async def initiate_payment(
    data: PaymentInitiateRequest,
    user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    try:
        result = await service.initiate_payment(
            order_id=data.order_id,
            user_id=str(user.id),
            user_email=getattr(user, "email", "test@test.com"),
            user_name=getattr(user, "full_name", "Customer"),
        )
        return PaymentInitiateResponse(**result)
    except PaymentError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.get("/{payment_id}", response_model=PaymentRead)
async def get_payment(
    payment_id: str = Path(...),
    user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    try:
        data = await service.get_payment(payment_id, user)
        return PaymentRead(**{k: v for k, v in data.items() if k in PaymentRead.model_fields})
    except PaymentError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.post("/{payment_id}/verify")
async def verify_payment(
    payment_id: str = Path(...),
    user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    # Need tran_id; look up payment first
    try:
        payment = await service.get_payment(payment_id, user)
        tran_id = payment.get("provider_reference") or payment_id
        result = await service.verify_payment(tran_id)
        return result
    except PaymentError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.post("/callback/success")
async def callback_success(payload: dict = None, service: PaymentService = Depends(get_payment_service)):
    if payload is None:
        payload = {}
    try:
        return await service.handle_callback(payload)
    except PaymentError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.post("/callback/fail")
async def callback_fail(payload: dict = None, service: PaymentService = Depends(get_payment_service)):
    if payload is None:
        payload = {}
    try:
        return await service.handle_callback(payload)
    except PaymentError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.post("/callback/cancel")
async def callback_cancel(payload: dict = None, service: PaymentService = Depends(get_payment_service)):
    if payload is None:
        payload = {}
    try:
        return await service.handle_callback(payload)
    except PaymentError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.post("/ipn")
async def ipn(payload: dict = None, service: PaymentService = Depends(get_payment_service)):
    if payload is None:
        payload = {}
    try:
        return await service.handle_callback(payload)
    except PaymentError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e
