# Ghost Hunters - Game System

A ghost hunting game built with microservices architecture for the PAD (Parallel and Distributed Programming) laboratory work at FAF, Technical University of Moldova.

## Table of Contents

- [Project Overview](#-project-overview)
- [Service Boundaries](#-service-boundaries)
- [Architecture Diagram](#-architecture-diagram)
- [Communication Contracts](#-communication-contracts)
- [API Endpoints](#-api-endpoints)
- [Development Guidelines](#-development-guidelines)
- [Project Management](#-project-management)
- [Team & Contributions](#-team--contributions)
- [License](#-license)

## Project Overview

Ghost Hunters is a multiplayer game, inspired by Phasmaphobia, that uses a microservices-oriented architecture. Players form teams to investigate haunted locations, gather evidence about supernatural entities and identify ghost types to earn currency in the game. The system handles real-time gameplay for multiple concurrent lobbies, with dynamic ghost AI, inventory management, location-based communication and game session tracking.

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


## Communication Contracts

### Service-to-Service Communication

- **TODO: Add specific communication contracts**


## API Endpoints

- **TODO: Add all endpoints for each api based on the template below**

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


## Team & Contributions

### Team Members
- **Vornic Daniela** - [@danielavornic](https://github.com/danielavornic)
- **Balamatiuc Eduard** - [@eduard-balamatiuc](https://github.com/eduard-balamatiuc)
- **Negai Marin** - [@MarinBizarreAdventure](https://github.com/MarinBizarreAdventure)
- **Plămădeală Maxim** - [@grumpycatyo-collab](https://github.com/grumpycatyo-collab)
- **Gusev Roman** - [@Ghenntoggy1](https://github.com/Ghenntoggy1)


---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---