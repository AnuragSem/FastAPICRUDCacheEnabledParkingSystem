from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session

from app.s2.database import get_db
from app.s2.models.parking import ParkingSpot
from app.s2.schemas.parking import ParkingSpotCreate,ParkingSpotUpdate,ParkingSpotResponse

router = APIRouter()

@router.post(
    "/parking/spots",
    response_model=ParkingSpotResponse
    )
def create_parking_spot(
    spot:ParkingSpotCreate,
    db:Session= Depends(get_db)
):
    new_spot = ParkingSpot(
        spot_number=spot.spot_number
    )
    db.add(new_spot)
    db.commit()
    db.refresh(new_spot)
    return new_spot

@router.get(
    "/parking/spots/available",
    response_model=list[ParkingSpotResponse]
)
def get_available_parking_spots(
    db: Session = Depends(get_db)
):
    spots = (
        db.query(ParkingSpot)
        .filter(ParkingSpot.occupied == False)
        .all()
    )

    return spots

@router.get(
    "/parking/spots",
    response_model=list[ParkingSpotResponse]
)
def get_all_parking_spots(
    db: Session = Depends(get_db)
):
    spots = db.query(ParkingSpot).all()

    return spots


@router.get(
    "/parking/spots/{spot_id}",
    response_model=ParkingSpotResponse
)
def get_parking_spot(
    spot_id: int,
    db: Session = Depends(get_db)
):
    spot = (
        db.query(ParkingSpot)
        .filter(ParkingSpot.id == spot_id)
        .first()
    )

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
def update_parking_spot(
    spot_id: int,
    spot_update: ParkingSpotUpdate,
    db: Session = Depends(get_db)
):
    spot = (
        db.query(ParkingSpot)
        .filter(ParkingSpot.id == spot_id)
        .first()
    )

    if spot is None:
        raise HTTPException(
            status_code=404,
            detail="Parking spot not found"
        )

    # Occupied state requires both person and entry time
    if spot_update.occupied:
        if (
            spot_update.occupied_by is None
            or spot_update.entry_time is None
        ):
            raise HTTPException(
                status_code=400,
                detail="Occupied spot requires occupied_by and entry_time"
            )

        # Don't allow a different person to overwrite an occupied spot
        if spot.occupied:
            if spot.occupied_by != spot_update.occupied_by:
                raise HTTPException(
                    status_code=409,
                    detail="Parking spot is already occupied"
                )

        spot.occupied = True
        spot.occupied_by = spot_update.occupied_by
        spot.entry_time = spot_update.entry_time

    # Empty state always clears person and entry time
    else:
        spot.occupied = False
        spot.occupied_by = None
        spot.entry_time = None

    db.commit()
    db.refresh(spot)

    return spot


@router.delete("/parking/spots/{spot_id}")
def delete_parking_spot(
    spot_id: int,
    db: Session = Depends(get_db)
):
    spot = (
        db.query(ParkingSpot)
        .filter(ParkingSpot.id == spot_id)
        .first()
    )

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

    db.delete(spot)
    db.commit()

    return {
        "message": "Parking spot deleted successfully",
        "spot_id": spot_id
    }