
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.s2.database import get_db
from app.s2.models.parking import ParkingSpot
from app.s2.schemas.parking import (
    ParkingSpotCreate,
    ParkingSpotUpdate,
    ParkingSpotResponse,
)

router = APIRouter()


@router.post(
    "/parking/spots",
    response_model=ParkingSpotResponse
)
async def create_parking_spot(
    spot: ParkingSpotCreate,
    db: AsyncSession = Depends(get_db)
):
    new_spot = ParkingSpot(
        spot_number=spot.spot_number
    )

    db.add(new_spot)
    await db.commit()
    await db.refresh(new_spot)

    return new_spot


@router.get(
    "/parking/spots/available",
    response_model=list[ParkingSpotResponse]
)
async def get_available_parking_spots(
    db: AsyncSession = Depends(get_db)
):
    statement = select(ParkingSpot).where(
        ParkingSpot.occupied.is_(False)
    )

    result = await db.execute(statement)
    spots = result.scalars().all()

    return spots


@router.get(
    "/parking/spots",
    response_model=list[ParkingSpotResponse]
)
async def get_all_parking_spots(
    db: AsyncSession = Depends(get_db)
):
    statement = select(ParkingSpot)

    result = await db.execute(statement)
    spots = result.scalars().all()

    return spots


@router.get(
    "/parking/spots/{spot_id}",
    response_model=ParkingSpotResponse
)
async def get_parking_spot(
    spot_id: int,
    db: AsyncSession = Depends(get_db)
):
    statement = select(ParkingSpot).where(
        ParkingSpot.id == spot_id
    )

    result = await db.execute(statement)
    spot = result.scalar_one_or_none()

    if spot is None:
        raise HTTPException(
            status_code=404,
            detail="Parking spot not found"
        )

    return spot



@router.patch(
    "/parking/spots/{spot_id}",
    response_model=ParkingSpotResponse
)
async def update_parking_spot(
    spot_id: int,
    spot_update: ParkingSpotUpdate,
    db: AsyncSession = Depends(get_db)
):
    statement = select(ParkingSpot).where(
        ParkingSpot.id == spot_id
    )

    result = await db.execute(statement)
    spot = result.scalar_one_or_none()

    if spot is None:
        raise HTTPException(
            status_code=404,
            detail="Parking spot not found"
        )

    if spot_update.occupied:
        if spot_update.occupied_by is None:
            raise HTTPException(
                status_code=400,
                detail="An occupied spot requires occupied_by"
            )

        # Prevent another person from taking an occupied spot
        if (
            spot.occupied
            and spot.occupied_by != spot_update.occupied_by
        ):
            raise HTTPException(
                status_code=409,
                detail="Parking spot is already occupied"
            )

        # Generate entry time only when the spot becomes occupied
        if not spot.occupied:
            spot.entry_time = datetime.now(timezone.utc)

        spot.occupied = True
        spot.occupied_by = spot_update.occupied_by

    else:
        # Checkout: clear the current parking session
        spot.occupied = False
        spot.occupied_by = None
        spot.entry_time = None

    await db.commit()
    await db.refresh(spot)

    return spot



@router.delete("/parking/spots/{spot_id}")
async def delete_parking_spot(
    spot_id: int,
    db: AsyncSession = Depends(get_db)
):
    statement = select(ParkingSpot).where(
        ParkingSpot.id == spot_id
    )

    result = await db.execute(statement)
    spot = result.scalar_one_or_none()

    if spot is None:
        raise HTTPException(
            status_code=404,
            detail="Parking spot not found"
        )

    if spot.occupied:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete an occupied parking spot"
        )

    await db.delete(spot)
    await db.commit()

    return {
        "message": "Parking spot deleted successfully",
        "spot_id": spot_id
    }