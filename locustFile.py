from locust import HttpUser, task, between


# class ParkingUser(HttpUser):

#     ### wait_time = between(1, 2)

#     @task(5)
#     def get_parking_spots(self):
#         self.client.get(
#             "/s1/parking/spots",
#             name="GET /parking/spots"
#         )

#     @task(3)
#     def get_available_spots(self):
#         self.client.get(
#             "/s1/parking/spots/available",
#             name="GET /parking/spots/available"
#         )

#     @task(2)
#     def get_specific_spot(self):
#         self.client.get(
#             "/s1/parking/spots/2",
#             name="GET /parking/spots/{spot_id}"
#          )


#####################################################################################

import random

from locust import HttpUser, task

# EDIT: ids of spots that already exist in your DB (and are normally free).
# Reads and PATCHes pick from these, so different keys get cached.
SEED_SPOT_IDS = [9, 2, 3]


def check(resp, ok=()):
    """Flag 4xx/5xx as failures, with a stable message that includes S1's
    `detail` (which now ends with the real cause, e.g. '| PoolTimeout').
    Codes listed in `ok` count as success (expected outcomes)."""
    code = resp.status_code
    if code < 400 or code in ok:
        resp.success()
        return

    try:
        detail = resp.json().get("detail", "")
    except Exception:
        detail = ""
    resp.failure(f"{code} {detail}".strip()[:120])


class ParkingUser(HttpUser):
    # no wait_time: every user fires its next request immediately

    def on_start(self):
        self.user_id = random.randint(1, 10**9)  # used as occupied_by

    # ---------------- reads (cached) ----------------

    @task(40)
    def get_all_spots(self):
        with self.client.get(
            "/s1/parking/spots", name="GET /parking/spots", catch_response=True
        ) as resp:
            check(resp)

    @task(25)
    def get_available_spots(self):
        with self.client.get(
            "/s1/parking/spots/available",
            name="GET /parking/spots/available",
            catch_response=True,
        ) as resp:
            check(resp)

    @task(25)
    def get_one_spot(self):
        spot_id = random.choice(SEED_SPOT_IDS)
        with self.client.get(
            f"/s1/parking/spots/{spot_id}",
            name="GET /parking/spots/{spot_id}",
            catch_response=True,
        ) as resp:
            check(resp)

    # ---------------- writes (each one invalidates cache keys) ----------------

    @task(5)
    def occupy_and_release(self):
        """PATCH a seed spot to occupied, then release it (state ends unchanged).
        409 = someone else holds it right now, which is an expected outcome."""
        spot_id = random.choice(SEED_SPOT_IDS)
        url = f"/s1/parking/spots/{spot_id}"

        with self.client.patch(
            url,
            json={"occupied": True, "occupied_by": self.user_id},
            name="PATCH /parking/spots/{spot_id} (occupy)",
            catch_response=True,
        ) as resp:
            check(resp, ok=(409,))
            got_it = resp.status_code == 200

        if got_it:
            with self.client.patch(
                url,
                json={"occupied": False},
                name="PATCH /parking/spots/{spot_id} (release)",
                catch_response=True,
            ) as resp:
                check(resp)

    @task(5)
    def create_and_delete(self):
        """POST a throwaway spot, then DELETE it using the id from the response."""
        spot_number = random.randint(10**6, 2 * 10**9)  # unique-ish, fits int4

        spot_id = None
        with self.client.post(
            "/s1/parking/spots",
            json={"spot_number": spot_number},
            name="POST /parking/spots",
            catch_response=True,
        ) as resp:
            check(resp)
            if resp.status_code == 200:
                spot_id = resp.json().get("id")

        if spot_id is not None:
            with self.client.delete(
                f"/s1/parking/spots/{spot_id}",
                name="DELETE /parking/spots/{spot_id}",
                catch_response=True,
            ) as resp:
                check(resp)

###################3############# s2 ###############################################

# class ParkingUser(HttpUser):

#     ##wait_time = between(1, 2)

#     @task(5)
#     def get_parking_spots(self):
#         self.client.get(
#             "/s2/parking/spots",
#             name="S2 GET /parking/spots"
#         )

#     @task(3)
#     def get_available_spots(self):
#         self.client.get(
#             "/s2/parking/spots/available",
#             name="S2 GET /parking/spots/available"
#         )

#     @task(2)
#     def get_specific_spot(self):
#         self.client.get(
#             "/s2/parking/spots/2",
#             name="S2 GET /parking/spots/{spot_id}"
#         )