# Ghost Hunters - Game System

A ghost hunting game built with microservices architecture for the PAD (Parallel and Distributed Programming) laboratory work at FAF, Technical University of Moldova.

## Table of Contents

- [Project Overview](#-project-overview)
- [Team](#-team)
- [Service Boundaries](#-service-boundaries)
- [Architecture Diagram](#-architecture-diagram)
- [Tech Stack](#-tech-stack)
- [Communication Contracts](#-communication-contracts)
- [API Endpoints](#-api-endpoints)
- [Development Guidelines](#-development-guidelines)
- [Project Management](#-project-management)
- [License](#-license)

## Project Overview

Ghost Hunters is a multiplayer game, inspired by Phasmaphobia, that uses a microservices-oriented architecture. Players form teams to investigate haunted locations, gather evidence about supernatural entities and identify ghost types to earn currency in the game. The system handles real-time gameplay for multiple concurrent lobbies, with dynamic ghost AI, inventory management, location-based communication and game session tracking.

## Team

| Member | Service 1 | Service 2 |
|--------|-----------|-----------|
| [Negai Marin](https://github.com/MarinBizarreAdventure) | Ghost Service | Location Service |
| [Gusev Roman](https://github.com/Ghenntoggy1) | Shop Service | Journal Service |
| [Balamatiuc Eduard](https://github.com/eduard-balamatiuc) | Lobby Service | Map Service |
| [Plămădeală Maxim](https://github.com/grumpycatyo-collab) | User Service | Ghost AI Service |
| [Vornic Daniela](https://github.com/danielavornic) | Inventory Service | Chat Service |


## Service Boundaries

### User Management Service

- **TODO: Add specific service description**

### Ghost AI Service

- **TODO: Add specific service description**

### Shop Service 

- **TODO: Add specific service description**

### Journal Service

- **TODO: Add specific service description**

### Lobby Service

Microservice responsible for gathering all the information about the game session and keep track of it till the end of the game session, making it the source of truth, with data like:

- Players participating in the session
    - Items brought
    - Sanity level
    - Death status
- The difficulty level
- Ghost type
- Chosen map

This service will be interacting with the Gateway through any change.

And all other game session related services like Location Service and Ghost AI Service  will be using the game status information as the truth source.

### Map Service

- **TODO: Add specific service description**

### Ghost Service

- **TODO: Add specific service description**

### Location Service

- **TODO: Add specific service description**

### Inventory Service

- **TODO: Add specific service description**

### Chat Service

- **TODO: Add specific service description**


## Architecture Diagram

**TODO: Add detailed architecture diagram showing:**
- Service interactions
- Data flow
- Communication protocols
- Load balancers (if any)
- Message queues (if any)

## Tech Stack

### Programming Languages & Justification

#### Go

Used for Ghost Service, Location Service, Map Service, Lobby Service, User ManagementService. Strong typing ensures data validation accuracy, built-in JSON marshaling handles complex ghost data structures efficiently, and Go's simplicity reduces development overhead for validation-focused operations. Goroutines and channels are essential for handling real-time position tracking with microsecond precision, while built-in concurrency primitives allow efficient processing of high-frequency location updates from multiple players simultaneously.

#### Rust

Used for Ghost AI Service. Rust compiles to highly efficient native code, so the “AI” logic will have very low latencies. Also it quite sensationally deals with data races because of its architecture which is perfect for the case of multi-threading.

#### Typescript

Used for Chat Service, Inventory Service and Shop Service. It is a great choice since TypeScript is a typed language, which helps in handling complex data structures and preventing runtime errors. Using Nest.js, a Node.js framework built on TypeScript, the project benefits from built-in WebSocket support for the chat app, validation pipes for data handling and overall a modular architecture.

### Databases

#### PostgreSQL

- Inventory service `inventory_db`: For structured data with strong consistency requirements. Handles item ownership relationships, transaction history and durability tracking where data integrity is important.
- Shop Service `shop_db` : Since data in Shop is fixed and Items have a common strict structure and price history is recorded inside of a table in the DB, Relational Database - PostgreSQL, provides a way to enforce strict policy on contained data in it.
- Journal Service `journal_db` : Since data in Journal is fixed and Items have a common strict structure and price history is recorded inside of a table in the DB, Relational Database - PostgreSQL, provides a way to enforce strict policy on contained data in it.
- Ghost Service `ghost_db`: Relational structure perfectly fits the ghost type hierarchy with symptoms, behavioral rules, and validation logic. JSONB fields can store flexible behavioral templates for the AI service.
- User Service `user_db` : Since it’s a classic user DB, Postgres would be the best choice for its wide popularity, maintainability and forums.

#### MongoDB

- Chat Service: For flexible message storage with various metadata (timestamps, room info, radio status). Supports queries for room-based message fetching and handles different message types without schema constraints.

#### Redis

- Location Service `locations_db`: for high-frequency operations - storing current player positions, room occupancy, and real-time state data with sub-millisecond access times. Essential for handling simultaneous location updates from hundreds of players without bottlenecks.
- Ghost AI Service `ai_db` : since the ghost are recorded only session-wise, and some info can be optimized via caching, Redis would be the best option.
- Lobby Service: for transient session management - storing player lists, game settings, and real-time readiness status with extremely low-latency read/write access. Essential for managing thousands of concurrent pre-game lobbies and broadcasting instant updates to all players.
- Map Service: for real-time game state tracking - storing dynamic object states (e.g., `is_ghosted`) and live data  with millisecond-level update propagation. Essential for synchronizing the game world state for all players and the Ghost AI Service during an active session.

### Communication Patterns

#### REST APIs

REST APIs for standard service-to-service communication, providing simple HTTP-based integration for most business operations.

#### PubSub with RabbitMQ

Leveraged by Location and Ghost Services for effective communication, since one is responsible for the users and another one for the ghosts, fast messages and exchanged info is critical.

## Communication Contracts

### Lobby Service

> ℹ️ Microservice responsible for creating, managing, and tracking game sessions. It serves as the source of truth for lobby state, including players, selected items, map, difficulty, and active game status. It communicates state changes to all relevant services and the game client.

#### Consumed API Endpoints

- `GET /map` - Available in Map Service.
    
    **Description**: Retrieves a newly generated map for the player to interact with.
    
- `POST /ai/start`  - Available in Ai Service.
    - Payload
        
        ```json
        {
        "lobby_id": "lobby_xyz_789",
        "host_id": "player_host_123",
        "map_id": "map_id_farmhouse_123",
        "difficulty": "medium",
        "ghost_type": "demon",
        "session": "active",
        "players": ["player_1", "player_2"]
        }
        ```
        
    
    **Description:** Starts a ghost thread in AI Service
    
- `POST /ai/end`  - Available in Ai Service.
    - Payload
        
        ```json
        {
        "lobby_id": "lobby_xyz_789"
        }
        ```
        
    
    **Description: End** a ghost thread in AI Service
    
- `POST /location/start`  - Available in Location Service.
    - Payload
        
        ```json
        {
        "lobby_id": "lobby_xyz_789",
        "host_id": "player_host_123",
        "map_id": "map_id_farmhouse_123",
        "difficulty": "medium",
        "ghost_type": "demon",
        "session": "active",
        "players": ["player_1", "player_2"]
        }
        ```
        
    
    **Description:** Starts a location session in Location Service.
    
- `POST /location/end`  - Available in Location Service.
    - Payload
        
        ```json
        {
        "lobby_id": "lobby_xyz_789"
        }
        ```
        
    
    **Description: End** a location session in Location Service.
    

#### Exposed API Endpoints

- `POST /lobbies` - Consumed by Game Client/Gateway.
    - Description
        
        Creates a new game lobby.
        
    - Payload
        
        ```json
        {
          "host_id": "user_1",
          "difficulty": "medium",
          "ghost_type": "type-1",
        }
        ```
        
    - Response
        
        ```json
        {
          "lobby_id": "lobby_xyz_789",
          "host_id": "player_host_123",
          "map_id": "map_farmhouse_123",
          "difficulty": "medium",
          "ghost_type": "type-1",
          "session": "inactive",
        }
        ```
        
- `GET /lobbies/{lobbyId}` - Consumed by Game Client/Gateway, Ghost AI Service, Location Service.
    - Description
        
        Retrieves the current state and settings of a specific lobby.
        
    - Payload
        
        ```json
        None
        ```
        
    - Response
        
        ```json
        {
        "lobby_id": "lobby_xyz_789",
        "host_id": "player_host_123",
        "map_id": "map_id_farmhouse_123",
        "difficulty": "medium",
        "ghost_type": "demon",
        "session": "active",
        "players": ["player_1", "player_2"]
        }
        ```
        
- `POST /lobbies/{lobbyId}/start`  - Consumed by Game Client/Gateway.
    - Description
        
        Starts the game with the current lobby configuration.
        
    - Payload
        
        ```json
        None
        ```
        
    - Response
        
        ```json
        200 OK
        ```
        
- `POST /lobbies/{lobbyId}/user` - Consumed by Game Client/Gateway.
    - **Description**
        
        Adds a player to the specific lobby.
        
    - Payload
        
        ```json
        {
        "user_id": "user_2"
        }
        ```
        
    - Response
        
        ```json
        200 OK
        ```
        
- `DELETE /lobbies/{lobbyId}/users/{userId}` - Consumed by Game Client/Gateway
    - Description
        
        Removes a player from a lobby.
        
    - Payload
        
        ```json
        None
        ```
        
    - Response
        
        ```json
        200 OK
        ```
        
- `PUT /lobbies/{lobbyId}/users/{userId}` - Consumed by Game Client/Gateway
    - Description
        
        Updates a player’s loadout (items brought into the session).
        
    - Payload
        
        ```json
        {
        	"items": [
        		{"item_id": "temp_reader"},
        		{"item_id": "camera"}
        	]
        }
        ```
        
    - Response
        
        ```json
        200 OK
        ```
        
- `GET /lobbies/{lobbyId}/users` - Consumed by Location Service, Game Client
    - Description
        
        Gets a list of all players currently in the lobby.
        
    - Payload
        
        ```json
        None
        ```
        
    - Response
        
        ```json
        {
          "lobby_id": "lobby_xyz_789",
          "users": ["user_1", "user_2", "user_3"]
        }
        ```
        
- `GET /lobbies/{lobbyId}/users/{userId}/status` - Consumed by Location Service
    - Description
        
        Gets a specific player’s status, including sanity and death state.
        
    - Payload
        
        ```json
        None
        ```
        
    - Response
        
        ```json
        {
            "death_status": false,
            "sanity_level": 85
        }
        ```
        
- `PUT /lobbies/{lobbyId}/users/{userId}/status` - Consumed by Ghost AI Service, Location Service
    - Description
        
        Update a player’s status (e.g., sanity drop, death).
        
    - Payload
        
        ```json
        {
          "death_status": true, // optional
          "sanity_level": 0 // optional
        }
        ```
        
    - Response
        
        ```json
        200 OK
        ```
        
- `GET /lobbies/{lobbyId}/ghost` - Consumed by Journal Service
    - Description
        
        Retrieves the true ghost type for a given session for validation.
        
    - Payload
        
        ```json
        None
        ```
        
    - Response
        
        ```json
        {
          "lobby_id": "lobby_xyz_789",
          "true_ghost_id": "demon"
        }
        ```
        
- `GET  /lobbies/{lobbyId}/users/{userId}/items`  - Consumed by Location Service, Chat Service
    
    `/lobby/{lobbyId}/users/{userId}/items`
    
    - Description
        
        Retrieves all the items available to the player provided.
        
    - Payload
        
        ```json
        None
        ```
        
    - Response
        
        ```json
        {
        	"items": [
        		{"item_id": "emf"},
            {"item_id": "crucifix"}
        	]
        }
        ```


### Map Service

> ℹ️ Keeps track of the entire game map state throughout each game session. It provides the base layout of maps and manages the dynamic state of objects (e.g., `is_ghosted`) and hiding spots for each active lobby.


#### Consumed API Endpoints

`None` - Map Service is a data provider.

#### Exposed API Endpoints

- `GET /map` - Consumed by Lobby Service
    - Description
        
        Retrieves a newly generated map for the player to interact with.
        
    - Payload
        
        ```json
        None
        ```
        
    - Response
        
        ```json
        {
          "map_id": "map_farmhouse_123",
          "name": "User's Custom Farmhouse"
        }
        ```
        
- `GET /map/{mapId}` - Consumed by Game Client, Ghost AI Service
    - Description
        
        Retrieves the full, current map state for a specific, active lobby session.
        
    - Payload
        
        ```json
        None
        ```
        
    - Response
        
        ```json
        {
          "map_id": "map_farmhouse_123",
          "name": "User's Custom Farmhouse",
          "rooms": [
            {
              "room_id": "kitchen_01",
              "name": "Kitchen",
              "connections": ["hallway_01", "dining_room_01"],
              "objects": [
                {"name": "Fridge", "is_ghosted": true, "trigger": "any"},
                {"name": "Sink", "is_ghosted": false, "trigger": "uv_lamp"}
              ],
              "hiding_places": [
        	      {"name": "Pantry", "is_ghost_accessible": false}
        	    ]
            }
          ]
        }
        ```
        
- `GET /map/{mapId}/rooms/{roomId}` - Consumed by Location Service
    - Location
        
        Gets specific room data for the current map.
        
    - Payload
        
        ```json
        None
        ```
        
    - Response
        
        ```json
        {
            "room_id": "kitchen_01",
            "name": "Kitchen",
            "connections": ["hallway_01"],
            "objects": [
                {"name": "Fridge", "is_ghosted": true, "trigger": "any"},
                {"name": "Sink", "is_ghosted": false, "trigger": "uv_lamp"}
            ],
            "hiding_places": [
                {"name": "Pantry", "is_ghost_accessible": false}
            ]
        }
        ```
        
- `PUT /map/{mapId}/rooms/{roomId}/objects/{objectName}` - Consumed by Ghost AI Service
    - Description
        
        Updates the state of an object within a room for a the specific map.
        
    - Payload
        
        ```json
        {
        "is_ghosted": true
        }
        ```
        
    - Response
        
        ```json
        200 OK
        ```

## Development Guidelines

### Git Workflow & Branch Strategy

#### GitFlow Model
We follow the **GitFlow** model without releases:

```
main (production-ready code)
├── develop (integration branch)
    ├── feature/feature-name (new features)
    ├── bugfix/bug-description (bug fixes)
    └── hotfix/critical-fix (production hotfixes)
```

#### Branch Naming Convention
- **Feature branches**: `feature/add-player-authentication`
- **Bug fixes**: `bugfix/fix-lobby-connection-issue`
- **Hotfixes**: `hotfix/fix-critical-security-vulnerability`

#### Merging Strategy
- **Feature → Develop**: Squash and merge
- **Develop → Main**: Squash and merge

### Conventional Commits

We use [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Pull Request Guidelines

#### PR Title Format
```
<type>(scope): brief description of changes
```

#### PR Content Requirements
```
## What?
[what exactly did you do in this PR]

## Why?
[why was this done in the first place]

## How?
[how did you implement it]

## Testing?
[assuming I don't know anything, how can I test what you did]

## Screenshots (optional)
[is it caught in 4k]

## Anything Else?
[you got any bonus level]
```

#### Code Review Process
- **Minimum Approvals**: 1 team member
- **Required Reviewers**: At least one team member
- **Automated Checks**: All pipelines must pass
- **Review Criteria**:
  - Code quality and readability
  - Test coverage
  - Performance implications
  - Security considerations


## Project Management

#### GitHub Project Board
- **Project Board**: [Link to GitHub Project](https://github.com/users/eduard-balamatiuc/projects/12)



## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---