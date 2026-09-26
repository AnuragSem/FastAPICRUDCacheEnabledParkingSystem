import json
import time
from app.s1.redis import redis_client
from fastapi import APIRouter

from app.s1 import s2_client
from app.s1.schemas.parking import (
    ParkingSpotCreate,
    ParkingSpotResponse,
    ParkingSpotUpdate,
)

router = APIRouter()

@router.get(
    "/parking/spots/available",
    response_model=list[ParkingSpotResponse]
)
async def get_available_parking_spots():

    start_time = time.perf_counter()

    cache_key = "parking:available"

    cached_data = await redis_client.get(cache_key)

    if cached_data:
        elapsed_time = time.perf_counter() - start_time

        print(
            f"CACHE HIT: parking:available from Redis | "
            f"time={elapsed_time * 1000:.3f} ms"
        )

        return json.loads(cached_data)

    print(
        "CACHE MISS: parking:available "
        "fetching from S2"
    )

    spots = await s2_client.get(
        "/parking/spots/available"
    )

    await redis_client.set(
        cache_key,
        json.dumps(spots)
    )

    elapsed_time = time.perf_counter() - start_time

    print(
        f"CACHE SET: {cache_key} stored in Redis | "
        f"time={elapsed_time * 1000:.3f} ms"
    )

    return spots

################################## get all

@router.get(
    "/parking/spots",
    response_model=list[ParkingSpotResponse]
)
async def get_parking_spots():

    start_time = time.perf_counter()

    cached_data = await redis_client.get("parking:spots")

    if cached_data:
        elapsed_time = time.perf_counter() - start_time

        print(
            f"CACHE HIT: returning parking spots from Redis | "
            f"time={elapsed_time * 1000:.3f} ms"
        )

        return json.loads(cached_data)

    print("CACHE MISS: fetching parking spots from S2")

    spots = await s2_client.get("/parking/spots")

    await redis_client.set(
        "parking:spots",
        json.dumps(spots)
    )

    elapsed_time = time.perf_counter() - start_time

    print(
        f"CACHE SET: parking spots stored in Redis | "
        f"time={elapsed_time * 1000:.3f} ms"
    )

    return spots

################################## get specific 

@router.get(
    "/parking/spots/{spot_id}",
    response_model=ParkingSpotResponse
)
async def get_parking_spot(spot_id: int):

    start_time = time.perf_counter()

    cache_key = f"parking:spot:{spot_id}"

    cached_data = await redis_client.get(cache_key)

    if cached_data:
        elapsed_time = time.perf_counter() - start_time

        print(
            f"CACHE HIT: parking:spot:{spot_id} from Redis | "
            f"time={elapsed_time * 1000:.3f} ms"
        )

        return json.loads(cached_data)

    print(
        f"CACHE MISS: parking:spot:{spot_id} "
        f"fetching from S2"
    )

    spot = await s2_client.get(
        f"/parking/spots/{spot_id}"
    )

    await redis_client.set(
        cache_key,
        json.dumps(spot)
    )

    elapsed_time = time.perf_counter() - start_time

    print(
        f"CACHE SET: {cache_key} stored in Redis | "
        f"time={elapsed_time * 1000:.3f} ms"
    )

    return spot

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

    await redis_client.delete(
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

    await redis_client.delete(
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

    await redis_client.delete(
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