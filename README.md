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

- **TODO: Add specific service description**

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

### Template Service
**Base URL**: `http://localhost:8080/api/v1`

#### Template Management
| Method | Endpoint | Description | Input | Output | Response Format |
|--------|----------|-------------|-------|--------|-----------------|
| POST | `/templates` | Create new template | `{name: string, description: string}` | `{template_id: string}` | JSON |
| GET | `/templates/{id}` | Get template details | Path: `id` | `{template_id: string, name: string, description: string}` | JSON |
| PUT | `/templates/{id}` | Update template | Path: `id`, Body: `{name: string, description: string}` | `{template_id: string}` | JSON |
| DELETE | `/templates/{id}` | Delete template | Path: `id` | `{success: boolean}` | JSON |
| **TODO** | **Add more endpoints** | | | | |

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