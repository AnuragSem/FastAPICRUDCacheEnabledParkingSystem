from fastapi import APIRouter

from app.s1 import s2_client
from app.s1.redis import cached_fetch, cache_delete
from app.s1.schemas.parking import (
    ParkingSpotCreate,
    ParkingSpotResponse,
    ParkingSpotUpdate,
)

router = APIRouter()

################################## get available
@router.get(
    "/parking/spots/available",
    response_model=list[ParkingSpotResponse]
)
async def get_available_parking_spots():
    return await cached_fetch(
        "parking:available",
        lambda: s2_client.get("/parking/spots/available"),
    )


################################## get all

@router.get(
    "/parking/spots",
    response_model=list[ParkingSpotResponse]
)
async def get_parking_spots():
    return await cached_fetch(
        "parking:spots",
        lambda: s2_client.get("/parking/spots"),
    )


################################## get specific

@router.get(
    "/parking/spots/{spot_id}",
    response_model=ParkingSpotResponse
)
async def get_parking_spot(spot_id: int):
    return await cached_fetch(
        f"parking:spot:{spot_id}",
        lambda: s2_client.get(f"/parking/spots/{spot_id}"),
    )


########################### CREATE

@router.post(
    "/parking/spots",
    response_model=ParkingSpotResponse
)
async def create_parking_spot(
    spot: ParkingSpotCreate
):
    result = await s2_client.post(
        "/parking/spots",
        spot.model_dump(mode="json")
    )

    await cache_delete(
        "parking:spots",
        "parking:available"
    )

    print(
        "CACHE INVALIDATED: parking:spots and "
        "parking:available deleted after POST"
    )

    return result


############################## Update spot

@router.patch(
    "/parking/spots/{spot_id}",
    response_model=ParkingSpotResponse
)
async def update_parking_spot(
    spot_id: int,
    spot: ParkingSpotUpdate
):
    result = await s2_client.patch(
        f"/parking/spots/{spot_id}",
        spot.model_dump(mode="json")
    )

    await cache_delete(
        "parking:spots",
        "parking:available",
        f"parking:spot:{spot_id}"
    )

    print(
        f"CACHE INVALIDATED: parking:spots, "
        f"parking:available and parking:spot:{spot_id} "
        f"deleted after PATCH"
    )

    return result


########################### delete a spot

@router.delete("/parking/spots/{spot_id}")
async def delete_parking_spot(spot_id: int):

    result = await s2_client.delete(
        f"/parking/spots/{spot_id}"
    )

    await cache_delete(
        "parking:spots",
        "parking:available",
        f"parking:spot:{spot_id}"
    )

    print(
        f"CACHE INVALIDATED: parking:spots, "
        f"parking:available and parking:spot:{spot_id} "
        f"deleted after DELETE"
    )

    return result