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
#         )




############## s2

class ParkingUser(HttpUser):

    ##wait_time = between(1, 2)

    @task(5)
    def get_parking_spots(self):
        self.client.get(
            "/s2/parking/spots",
            name="S2 GET /parking/spots"
        )

    @task(3)
    def get_available_spots(self):
        self.client.get(
            "/s2/parking/spots/available",
            name="S2 GET /parking/spots/available"
        )

    @task(2)
    def get_specific_spot(self):
        self.client.get(
            "/s2/parking/spots/2",
            name="S2 GET /parking/spots/{spot_id}"
        )