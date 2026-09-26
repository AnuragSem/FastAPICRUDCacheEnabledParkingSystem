# FastAPI CRUD Parking System with Redis Caching

A small parking management system built with **FastAPI**, **PostgreSQL**, and **Redis**, using a two-service architecture.

The project demonstrates CRUD operations for parking spots along with a **cache-aside Redis caching strategy** implemented in the client-facing service.

---

## 1. Project Overview

This project manages parking spots and their occupancy state.

The application is divided into two services:

* **S1 — Client/API Service**

  * Handles client requests.
  * Provides the public API.
  * Owns and manages the Redis cache.
  * Calls S2 when cached data is unavailable.
  * Invalidates stale cache entries after successful write operations.

* **S2 — Database Service**

  * Handles database-related operations.
  * Performs CRUD operations using SQLAlchemy.
  * Communicates with PostgreSQL.
  * Has no knowledge of Redis.

The main purpose of the architecture is to keep **caching concerns separate from database responsibilities**.

---

# 2. Architecture

```text
                    Client
                      |
                      v
              +---------------+
              |      S1       |
              | FastAPI       |
              | API + Redis   |
              +-------+-------+
                      |
              +-------+-------+
              |               |
              v               v
            Redis             S2
                              |
                              v
                         PostgreSQL
```

### Responsibilities

| Component  | Responsibility                                    |
| ---------- | ------------------------------------------------- |
| Client     | Sends API requests                                |
| S1         | Public API, validation, caching, S2 communication |
| Redis      | Stores frequently accessed responses              |
| S2         | Database operations                               |
| PostgreSQL | Persistent application data                       |

### Important architectural decision

S2 does **not** communicate with Redis.

Redis belongs to S1 because caching is treated as part of the API/request-handling layer rather than the database layer.

This keeps S2 focused on database operations and allows the caching implementation to be changed independently later.

---

# 3. Request Flow

## Cache HIT

When requested data already exists in Redis:

```text
Client
  |
  v
S1
  |
  v
Redis
  |
  v
Response
```

S2 and PostgreSQL are not contacted.

---

## Cache MISS

When requested data is not present in Redis:

```text
Client
  |
  v
S1
  |
  v
Redis ---- MISS
  |
  v
S2
  |
  v
PostgreSQL
  |
  v
S2
  |
  v
S1
  |
  v
Redis ---- SET
  |
  v
Client
```

S1 retrieves the data through S2, stores the result in Redis, and then returns the response to the client.

---

# 4. Cache Strategy

The project uses a **cache-aside pattern**.

The application checks Redis first.

If the value exists:

```text
Redis → return data
```

If the value does not exist:

```text
Redis MISS
    ↓
S2
    ↓
PostgreSQL
    ↓
S1
    ↓
Redis SET
    ↓
Response
```

---

## Redis Cache Keys

| API operation               | Redis key                |
| --------------------------- | ------------------------ |
| Get all parking spots       | `parking:spots`          |
| Get available parking spots | `parking:available`      |
| Get specific parking spot   | `parking:spot:{spot_id}` |

Example:

```text
parking:spot:2
```

stores the cached representation of parking spot ID `2`.

---

# 5. Cache Invalidation

Database writes can make cached data stale, so S1 invalidates affected cache entries after a successful write operation.

| Operation | `parking:spots` | `parking:available` | Specific spot         |
| --------- | --------------- | ------------------- | --------------------- |
| GET       | Read/Set        | Read/Set            | Read/Set              |
| POST      | Invalidate      | Invalidate          | —                     |
| PATCH     | Invalidate      | Invalidate          | Invalidate changed ID |
| DELETE    | Invalidate      | Invalidate          | Invalidate deleted ID |

### POST

Creating a new parking spot changes:

* the complete parking spot list
* the available parking spot list

Therefore both caches are invalidated.

### PATCH

Updating a parking spot can change:

* its data in the complete list
* whether it appears in the available list
* the cached representation of that specific spot

Therefore all three affected views are invalidated.

### DELETE

Deleting a spot changes:

* the complete list
* the available list
* the specific spot's cached data

Therefore all three affected cache entries are invalidated.

Unrelated specific spot caches are left untouched because their underlying data has not changed.

---

# 6. Project Structure

```text
FastAPICRUDCacheEnabledParkingSystem/
│
├── app/
│   ├── __init__.py
│   │
│   ├── s1/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── redis.py
│   │   ├── s2_client.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── parking.py
│   │   │
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── parking.py
│   │
│   └── s2/
│       ├── __init__.py
│       ├── main.py
│       ├── database.py
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   └── parking.py
│       │
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── parking.py
│       │
│       └── routes/
│           ├── __init__.py
│           └── parking.py
│
├── compose.yml
├── .env
├── .gitignore
└── requirements.txt
```

---

# 7. Tools and Technologies

| Technology    | Purpose                          |
| ------------- | -------------------------------- |
| Python        | Application programming language |
| FastAPI       | REST API framework               |
| Uvicorn       | ASGI server                      |
| SQLAlchemy    | ORM/database interaction         |
| PostgreSQL    | Persistent database              |
| Redis         | In-memory cache                  |
| HTTPX         | Communication between S1 and S2  |
| Pydantic      | Request/response validation      |
| python-dotenv | Environment variable loading     |
| Docker        | Running PostgreSQL and Redis     |
| Git           | Version control                  |

---

# 8. Versions

The project was developed and tested with the following versions:

| Component               | Version |
| ----------------------- | ------- |
| Python                  | 3.13.7  |
| FastAPI                 | 0.141.1 |
| Uvicorn                 | 0.53.0  |
| SQLAlchemy              | 2.0.54  |
| psycopg                 | 3.3.6   |
| Redis Python client     | 8.1.0   |
| python-dotenv           | 1.x     |
| HTTPX                   | 0.28.1  |
| PostgreSQL Docker image | 18      |
| Redis Docker image      | 8.10.2  |

> Dependency versions can also be checked in `requirements.txt`. Docker image versions are defined in `compose.yml`.

---

# 9. Port Configuration

The project uses the following ports:

| Service    |   Port | Purpose                       |
| ---------- | -----: | ----------------------------- |
| S1         | `8000` | Client-facing FastAPI service |
| S2         | `8001` | Internal database service     |
| PostgreSQL | `5432` | PostgreSQL database           |
| Redis      | `6379` | Redis cache                   |

### Default ports

These are the standard/default ports used by the respective technologies:

```text
FastAPI/Uvicorn : 8000
PostgreSQL      : 5432
Redis           : 6379
```

S2 is intentionally configured to use `8001` so that it can run alongside S1.

---

# 10. Environment Variables

The project uses a `.env` file for configuration.

Example:

```env
POSTGRES_DB=parking_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/parking_db

REDIS_HOST=localhost
REDIS_PORT=6379

S2_BASE_URL=http://localhost:8001
```

The `.env` file should **not** be committed to Git.

A developer setting up the project should create their own `.env` file using the above structure.

---

# 11. Docker Setup

Only PostgreSQL and Redis are containerized.

S1 and S2 run locally using Python/Uvicorn.

The Docker Compose configuration contains:

```yaml
services:
  postgres:
    image: postgres:18
    container_name: parking-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - parking_postgres_data:/var/lib/postgresql

  redis:
    image: redis:8.10.2
    container_name: parking-redis
    ports:
      - "6379:6379"

volumes:
  parking_postgres_data:
```

---

# 12. Setting Up the Project

## Prerequisites

Install:

* Python 3.13+
* Docker
* Git

Verify:

```cmd
python --version
docker --version
git --version
```

---

## Step 1 — Clone the repository

```cmd
git clone <repository-url>
cd FastAPICRUDCacheEnabledParkingSystem
```

---

## Step 2 — Create a virtual environment

```cmd
python -m venv .venv
```

Activate it on Windows Command Prompt:

```cmd
.venv\Scripts\activate
```

---

## Step 3 — Install dependencies

```cmd
python -m pip install -r requirements.txt
```

---

## Step 4 — Create `.env`

Create a `.env` file in the project root:

```env
POSTGRES_DB=parking_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/parking_db

REDIS_HOST=localhost
REDIS_PORT=6379

S2_BASE_URL=http://localhost:8001
```

---

## Step 5 — Start PostgreSQL and Redis

From the project root:

```cmd
docker compose up -d
```

Check the containers:

```cmd
docker ps
```

Expected containers:

```text
parking-postgres
parking-redis
```

---

# 13. Starting S2

S2 should be started before S1 because S1 communicates with S2.

Run:

```cmd
python -m uvicorn app.s2.main:app --reload --port 8001
```

S2 Swagger documentation:

```text
http://localhost:8001/docs
```

S2 root endpoint:

```text
http://localhost:8001/
```

---

# 14. Starting S1

Open another terminal, activate the virtual environment, and run:

```cmd
.venv\Scripts\activate
python -m uvicorn app.s1.main:app --reload --port 8000
```

S1 Swagger documentation:

```text
http://localhost:8000/docs
```

S1 is the public/client-facing API.

---

# 15. API Endpoints

## S1

### Get all parking spots

```http
GET /s1/parking/spots
```

### Get available parking spots

```http
GET /s1/parking/spots/available
```

### Get a specific parking spot

```http
GET /s1/parking/spots/{spot_id}
```

### Create a parking spot

```http
POST /s1/parking/spots
```

### Update a parking spot

```http
PATCH /s1/parking/spots/{spot_id}
```

### Delete a parking spot

```http
DELETE /s1/parking/spots/{spot_id}
```

---

# 16. S2 Endpoints

S2 exposes equivalent database-service endpoints under the `/s2` prefix:

```http
GET    /s2/parking/spots
GET    /s2/parking/spots/available
GET    /s2/parking/spots/{spot_id}

POST   /s2/parking/spots
PATCH  /s2/parking/spots/{spot_id}
DELETE /s2/parking/spots/{spot_id}
```

S1 communicates with these endpoints internally.

Clients should normally use S1 rather than directly accessing S2.

---

# 17. Parking Spot Data Model

A parking spot contains:

```text
id
spot_number
occupied
occupied_by
entry_time
```

An empty spot has the following state:

```text
occupied = false
occupied_by = NULL
entry_time = NULL
```

An occupied spot contains:

```text
occupied = true
occupied_by = <id>
entry_time = <timestamp>
```

The application prevents deleting an occupied parking spot.

An occupied spot must first be checked out before another occupant can use it.

---

# 18. Redis Debugging

Redis can be accessed directly using the Docker container:

```cmd
docker exec -it parking-redis redis-cli
```

View existing keys:

```redis
KEYS *
```

View a cached value:

```redis
GET parking:spots
```

Check whether a key exists:

```redis
EXISTS parking:spots
```

Delete a cache entry manually:

```redis
DEL parking:spots
```

Redis cache operations are also printed by S1 for debugging:

```text
CACHE HIT
CACHE MISS
CACHE SET
CACHE INVALIDATED
```

---

# 19. Example Cache Lifecycle

A typical request sequence looks like this:

### First GET

```text
GET /s1/parking/spots

Redis → MISS
S1 → S2
S2 → PostgreSQL
PostgreSQL → S2
S2 → S1
S1 → Redis SET
S1 → Client
```

### Second GET

```text
GET /s1/parking/spots

Redis → HIT
Redis → S1
S1 → Client
```

### Update

```text
PATCH /s1/parking/spots/1

S1 → S2
S2 → PostgreSQL
PostgreSQL → S2
S2 → S1
S1 → Redis INVALIDATION
```

### Next GET

```text
GET /s1/parking/spots

Redis → MISS
S1 → S2
S2 → PostgreSQL
...
S1 → Redis SET
```

This ensures that stale cached data is not served after a successful database modification.

---

# 20. Current Redis Configuration

Redis currently uses its default configuration.

No TTL or custom eviction policy has been introduced yet.

This is intentional for the current demonstration project because the expected dataset is small.

Possible future configuration considerations include:

* TTL policies
* `maxmemory`
* eviction policies
* Redis persistence
* cache expiration strategy
* protection against cache stampedes
* production logging/monitoring

---

# 21. Design Decisions

### Why two services?

The application separates API/cache responsibilities from database responsibilities.

```text
S1 = API + Cache
S2 = Database
```

### Why does S1 own Redis?

Caching is part of how S1 handles client requests. Keeping Redis out of S2 prevents the database service from becoming dependent on a specific caching implementation.

### Why cache GET requests?

Parking information may be read much more frequently than it is modified. Caching reduces repeated database requests for frequently accessed data.

### Why invalidate instead of immediately updating the cache?

The current implementation follows a simple cache-aside strategy.

After a successful write, affected cached representations are removed. The next read retrieves the latest data from S2 and repopulates Redis.

This keeps the implementation straightforward and avoids maintaining multiple copies of updated data manually.

---

# 22. Development Notes

S1 uses asynchronous FastAPI endpoints and communicates with S2 using HTTPX.

S2 currently uses synchronous SQLAlchemy database operations.

The current architecture is:

```text
S1 async
   ↓
HTTPX
   ↓
S2 sync
   ↓
SQLAlchemy
   ↓
PostgreSQL
```

This is sufficient for the current project and keeps the implementation relatively simple.

---

# 23. Stopping the Project

Stop the FastAPI services using:

```text
CTRL + C
```

Stop the Docker containers:

```cmd
docker compose down
```

The PostgreSQL data is stored in the Docker volume and is therefore preserved when the containers are stopped and removed.

---

# 24. Project Goal

The project is primarily intended to demonstrate:

* FastAPI CRUD development
* Service separation
* REST API communication between services
* PostgreSQL persistence
* SQLAlchemy ORM usage
* Redis caching
* Cache-aside architecture
* Cache invalidation
* Docker-based infrastructure
* Environment-based configuration
* Basic performance measurement

The project can later be extended with more advanced caching and production-oriented features such as TTLs, eviction policies, centralized cache helpers, connection pooling, concurrency handling, monitoring, and more realistic parking/vehicle/session modeling.
