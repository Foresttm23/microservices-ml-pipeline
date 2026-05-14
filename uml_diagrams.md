# UML Diagrams — ML Microservices

---

| # | Diagram                        | Type                                                                                                                                                           |
|---|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | **Global System Architecture** | Sequence diagram — full request lifecycle: auth → task submit → Redis queue → ML Worker → result consumer → WebSocket delivery                                 |
| 2 | **Gateway Service**            | Component graph — middleware stack, API routes (auth/query/websocket/health), HTTPX pool, rate limiter, Redis Pub/Sub bridge                                   |
| 3 | **Orchestrator Service**       | Layered component graph — API → Services (`QueryService`, `ResultProcessor`) → Repositories (`Query`, `Log`, `Response`) → DB + Redis queues                   |
| 4 | **ML Worker Service**          | Process/component graph — strategy pattern for generator init, `InferenceRunner`, `TaskProcessor`, `GeminiTextGenerator`/Mock, queue consumer/publisher wiring |
| 5 | **Auth Service**               | Component graph — middleware stack, all auth endpoints, `AuthService`, `UserRepository`, `TokenRepository`, JWT utilities, Postgres                            |
| 6 | **Shared Library**             | Dependency graph — shows which shared components (`messaging`, `schemas`, `db`, `middlewares`, `utils`) each service imports                                   |

## 1. Global System Architecture

End-to-end data flow from client to result delivery.

```mermaid
sequenceDiagram
    autonumber
    actor Client

box "Host: :8080" #1a1a2e
participant GW as Gateway<br/>(FastAPI)
end

box "Host: :8083"#16213e
participant Auth as Auth Service<br/>(FastAPI)
end

box "Host: :8081"#0f3460
participant Orch as Orchestrator<br/>(FastAPI)
end

participant Redis as Redis<br/>(Broker + Pub/Sub)

box "Host: :8082"#1b4332
participant ML as ML Worker<br/>(asyncio)
end

participant AuthDB as Auth DB<br/>(Postgres)
participant OrchDB as Orch DB<br/>(Postgres)
participant Gemini as Gemini API

%% --- Authentication ---
Client->>GW: POST /api/auth/login
GW->>Auth: Proxy → POST /auth/login
Auth->>AuthDB: Validate credentials
AuthDB-->>Auth: User record
Auth-->>GW: {access_token, refresh_token}
GW-->>Client: 200 OK {access_token, refresh_token}

%% --- Task Submission ---
Client->>GW: POST /api/run/{pipeline_id} + Bearer token
Note over GW: JWTAuthMiddleware validates token
GW->>Orch: Proxy → POST /api/run/{pipeline_id}
Orch->>OrchDB: INSERT query (PENDING)
Orch->>Redis: LPUSH task_queue {TaskMessage}
Orch-->>GW: 202 Accepted {query_id}
GW-->>Client: 202 Accepted {query_id}

%% --- WebSocket subscribe ---
Client->>GW: WS /ws/{user_id}
GW->>Redis: SUBSCRIBE results:{user_id}

%% --- ML Worker processing ---
Redis-->>ML: BRPOP task_queue
ML->>Gemini: generate_content(prompt, history)
Gemini-->>ML: Generated text
ML->>Redis: LPUSH result_queue {ResultMessage}

%% --- Result processing ---
Redis-->>Orch: BRPOP result_queue
Orch->>OrchDB: UPDATE query → COMPLETED
Orch->>Redis: PUBLISH results:{user_id} {ResultMessage}

%% --- Result delivery ---
Redis-->>GW: Message on results:{user_id}
GW-->>Client: WebSocket frame {result}
```

---

## 2. Gateway Service

```mermaid
graph TB
    subgraph GW["Gateway Service (:8000)"]
        direction TB

        subgraph MW["Middleware Stack"]
            CORS["CORSMiddleware"]
            LOG["LoggingContextMiddleware"]
            JWT["JWTAuthMiddleware"]
            RLOG["ResponseLogMiddleware"]
        end

        subgraph API["API Layer (api/v1)"]
            ARTR["auth.py<br/>POST /api/auth/*"]
            QRTR["query.py<br/>POST /api/run/{pipeline_id}"]
            WS["websocket.py<br/>WS /ws/{user_id}"]
            HEALTH["health.py<br/>GET /health"]
        end

        subgraph INFRA["Infrastructure (infra/)"]
            HTTPX["httpx_client.py<br/>init_httpx / close_httpx<br/>AsyncClient pool"]
        end

        subgraph DEPS["Dependencies"]
            RL["RateLimiterGlobalDep<br/>(FastAPILimiter + Redis)"]
            CTX["context_helpers.py<br/>request_id / user_id"]
        end

        PROXY["shared/utils/proxy_helper.py<br/>forward_to_service()"]
        PUBSUB["shared/messaging/RedisPubSub<br/>subscribe / listen"]
    end

    Client(["Client"])
    AuthSvc(["Auth Service :8003"])
    OrchSvc(["Orchestrator :8001"])
    Redis(["Redis"])
    Client -->|HTTP| CORS
    CORS --> LOG --> JWT --> RLOG
    RLOG --> API
    ARTR -->|via HTTPX pool| PROXY --> AuthSvc
    QRTR -->|via HTTPX pool| PROXY --> OrchSvc
    WS -->|subscribe| PUBSUB
    PUBSUB <-->|Pub/Sub| Redis
    RL -->|token bucket| Redis
    HTTPX -.->|pooled connections| PROXY
```

---

## 3. Orchestrator Service

```mermaid
graph TB
    subgraph ORCH["Orchestrator Service (:8001)"]
        direction TB

        subgraph API["API Layer (api/v1)"]
            RUN["run.py<br/>POST /api/run/{pipeline_id}"]
            CHATS["chats.py<br/>GET /api/chats/*"]
        end

        subgraph SVC["Service Layer (services/)"]
            QS["QueryService<br/>query_service.py<br/>• create_query()<br/>• get_chat_history()"]
            RP["ResultProcessor<br/>result_processor.py<br/>• process() → DB update + Pub/Sub"]
        end

        subgraph REPO["Repository Layer (repositories/)"]
            QR["QueryRepository<br/>query_repository.py<br/>• save() / get() / list()"]
            LR["LogRepository<br/>log_repository.py"]
            RR["ResponseRepository<br/>response_repository.py"]
        end

        subgraph SCH["Domain Schemas (schemas/)"]
            QSch["query.py<br/>QueryModel / QueryCreateRequest<br/>/ QueryDetailedResponse"]
            LSch["log.py<br/>LogEntry"]
            RSch["response.py<br/>ResponseModel"]
        end

        subgraph INFRA["Infrastructure"]
            DB["shared/db<br/>SQLAlchemy + Alembic<br/>(Postgres)"]
            TQUEUE["shared/messaging<br/>get_task_queue()<br/>QueuePublisher"]
            RQUEUE["shared/messaging<br/>get_result_queue()<br/>QueueConsumer"]
            PUBSUB["shared/messaging<br/>RedisPubSub<br/>PUBLISH results:{user_id}"]
        end
    end

    GW(["Gateway"])
    Redis(["Redis"])
    OrchDB(["Postgres<br/>orch-db"])
    GW -->|HTTP POST| RUN
    GW -->|HTTP GET| CHATS
    RUN --> QS
    CHATS --> QS
    QS -->|enqueue task| TQUEUE --> Redis
    QS --> QR --> DB --> OrchDB
    RQUEUE -->|dequeue result| RP
    RP --> QR
    RP -->|publish| PUBSUB --> Redis
    Redis -->|BRPOP result_queue| RQUEUE
    QR -.-> SCH
    LR -.-> SCH
    RR -.-> SCH
```

---

## 4. ML Worker Service

```mermaid
graph TB
    subgraph MLW["ML Worker Service (asyncio process)"]
        direction TB

        subgraph ENTRY["Entry Point (main.py)"]
            INIT["_init_generator()<br/>Strategy: Real vs. Mock"]
            INITP["_init_processor()<br/>Wires runner + publisher"]
        end

        subgraph WORKER["Worker Layer (worker/)"]
            RUNNER["InferenceRunner<br/>runner.py<br/>run(task) → result"]
        end

        subgraph SVC["Service Layer (services/)"]
            TP["TaskProcessor<br/>task_processor.py<br/>process(TaskMessage) → ResultMessage"]
        end

        subgraph INFRA["Infrastructure (infra/)"]
            GA["GeminiTextGenerator<br/>gemini_adapter.py<br/>generate(prompt, history)"]
            MOCK["MockTextGenerator<br/>gemini_adapter.py<br/>(DRY_RUN mode)"]
        end

        subgraph CORE["Core (core/)"]
            LOADER["GeminiModelLoader<br/>loader.py<br/>load model / config"]
            CFG["GeminiSettings<br/>config.py"]
        end

        subgraph MESSAGING["Shared Messaging"]
            TQ["get_task_queue()<br/>QueueConsumer<br/>BRPOP task_queue"]
            RQ["get_result_queue()<br/>QueuePublisher<br/>LPUSH result_queue"]
        end
    end

    Redis(["Redis"])
    Gemini(["Gemini API"])
    Redis -->|" BRPOP task_queue\n{TaskMessage JSON} "| TQ
    TQ -->|" TaskMessage "| TP
    TP --> RUNNER
    RUNNER --> GA
    GA -->|REST| Gemini
    Gemini -->|Generated text| GA
    GA --> RUNNER
    RUNNER -->|ResultMessage| TP
    TP --> RQ
    RQ -->|" LPUSH result_queue\n{ResultMessage JSON} "| Redis
    CFG --> LOADER
    LOADER --> RUNNER
    INIT -->|" settings.ML_WORKER_DRY_RUN "| GA
    INIT --> MOCK
    INITP --> TP
```

---

## 5. Auth Service

```mermaid
graph TB
    subgraph AUTH["Auth Service (:8003)"]
        direction TB

        subgraph MW["Middleware Stack"]
            CORS["CORSMiddleware"]
            LOG["LoggingContextMiddleware"]
            JWT_MW["JWTAuthMiddleware"]
            RLOG["ResponseLogMiddleware"]
        end

        subgraph API["API Layer (api/v1)"]
            REG["POST /auth/register"]
            LOGIN["POST /auth/login"]
            REFRESH["POST /auth/refresh"]
            ME["GET /auth/me"]
            LOGOUT["POST /auth/logout"]
        end

        subgraph SVC["Service Layer (services/)"]
            AS["AuthService<br/>auth_service.py<br/>• register_user()<br/>• login()<br/>• refresh_tokens()<br/>• get_current_user()"]
        end

        subgraph REPO["Repository Layer (repositories/)"]
            UR["UserRepository<br/>user_repository.py<br/>• get_by_email()<br/>• create()"]
            TR["TokenRepository<br/>token_repository.py<br/>• save_refresh()<br/>• revoke()<br/>• validate()"]
        end

        subgraph SCH["Schemas (schemas/)"]
            ASch["auth.py<br/>LoginRequest / RegisterRequest<br/>TokenResponse / UserResponse"]
        end

        subgraph CORE["Core (core/)"]
            JWT["JWT utilities<br/>create_access_token()<br/>create_refresh_token()<br/>verify_token()"]
            CFG["AuthSettings<br/>config.py"]
        end

        subgraph INFRA["Infrastructure"]
            DB["shared/db<br/>SQLAlchemy + Alembic<br/>(Postgres)"]
        end
    end

    Client(["Client / Gateway"])
    AuthDB(["Postgres<br/>auth-db"])
    Client -->|HTTP| CORS
    CORS --> LOG --> JWT_MW --> RLOG
    RLOG --> API
    REG --> AS
    LOGIN --> AS
    REFRESH --> AS
    ME --> AS
    LOGOUT --> AS
    AS --> UR --> DB --> AuthDB
    AS --> TR --> DB
    AS --> JWT
    JWT --> CFG
    UR -.-> SCH
    TR -.-> SCH
```

---

## 6. Shared Library Components

```mermaid
graph LR
    subgraph SHARED["shared/"]
        direction TB

        subgraph MSG["messaging/"]
            Q["RedisQueue<br/>queue.py<br/>enqueue / dequeue"]
            PS["RedisPubSub<br/>pubsub.py<br/>publish / subscribe / listen"]
            CON["QueueConsumer[T,R]<br/>consumer.py<br/>run() loop"]
            PUB["QueuePublisher<br/>publisher.py<br/>publish(msg)"]
            NAMES["names.py<br/>task_queue / result_queue<br/>results:{user_id}"]
            PROTO["protocols.py<br/>Processor[T,R] protocol"]
        end

        subgraph SCH["schemas/"]
            TM["TaskMessage<br/>task.py"]
            RM["ResultMessage<br/>result.py"]
            AM["Auth schemas<br/>auth.py"]
            QM["Query schemas<br/>query.py"]
        end

        subgraph DB["db/"]
            INIT_DB["init_db()<br/>SQLAlchemy engine + session"]
            CLOSE_DB["close_db()"]
        end

        subgraph CORE["core/"]
            EX["exceptions/<br/>global_exception_handler()"]
            LOG["logging/<br/>setup_logging()"]
        end

        subgraph MW["middlewares/"]
            LCM["LoggingContextMiddleware"]
            RLM["ResponseLogMiddleware"]
            JWM["JWTAuthMiddleware"]
        end

        subgraph UTILS["utils/"]
            PH["proxy_helper.py<br/>forward_to_service()"]
        end
    end

    GW(["Gateway"])
    ORCH(["Orchestrator"])
    MLW(["ML Worker"])
    AUTH(["Auth"])
    GW -->|imports| MSG
    GW -->|imports| MW
    GW -->|imports| UTILS
    ORCH -->|imports| MSG
    ORCH -->|imports| DB
    ORCH -->|imports| SCH
    MLW -->|imports| MSG
    MLW -->|imports| SCH
    AUTH -->|imports| DB
    AUTH -->|imports| MW
```
