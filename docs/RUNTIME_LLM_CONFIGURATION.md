# Runtime LLM Configuration for Admin Panel

## Current Architecture Analysis

### How Environment Variables Work with the Browser/API

**Short Answer:** Yes, the API server will still use environment variables if they're set in the shell where the server starts.

**How it Works:**

1. **When you start the API server:**
   ```bash
   cd backend
   npm run dev  # (or uvicorn/poetry commands)
   ```

2. **The server inherits environment variables from that shell session**

3. **The browser/frontend doesn't use env vars directly** - it just makes HTTP requests to the API

4. **The API server uses whatever configuration was loaded at startup** from:
   - Environment variables in the shell (highest priority)
   - `.env` file (lower priority)
   - Default values in code (lowest priority)

### Current LLM Initialization Flow

```
Server Startup
    ↓
Load Settings from .env + env vars (via Pydantic Settings)
    ↓
MarkingService.__init__() creates singleton instance
    ↓
First API request triggers MarkingService.initialize()
    ↓
create_llm_client_from_config(settings) - USES STARTUP CONFIG
    ↓
LLM client stays the same for entire server lifetime
```

**Key Point:** The LLM client is created ONCE at initialization and reused for all requests.

---

## Problem: Runtime Configuration

For your admin panel, you want to:
1. Let admin select LLM provider (Google, Anthropic, OpenAI, etc.)
2. Let admin enter API key
3. Apply changes **without restarting the server**
4. Possibly have different users use different LLMs (multi-tenancy)

**Current Issue:** The LLM client is created once from `.env` at startup and can't be changed at runtime.

---

## Solution: Database-Backed Runtime Configuration

Here's the recommended architecture for your admin panel:

### Architecture Changes Needed

```
┌─────────────────────────────────────────────────────────┐
│                    Admin Panel UI                        │
│  - Select LLM Provider dropdown                         │
│  - Enter API Key input                                  │
│  - Save button                                          │
└────────────────┬────────────────────────────────────────┘
                 │ POST /api/admin/llm-config
                 ↓
┌─────────────────────────────────────────────────────────┐
│              LLM Config API Endpoint                     │
│  - Validate provider & API key                          │
│  - Save to database                                     │
│  - Return success                                       │
└────────────────┬────────────────────────────────────────┘
                 │ Save to DB
                 ↓
┌─────────────────────────────────────────────────────────┐
│                  Database Table                          │
│  llm_configs (id, user_id, provider, model, api_key,    │
│               is_active, created_at, updated_at)        │
└────────────────┬────────────────────────────────────────┘
                 │ Load on each request
                 ↓
┌─────────────────────────────────────────────────────────┐
│            Modified MarkingService                       │
│  - Create LLM client PER REQUEST (not at startup)       │
│  - Load config from database (not from .env)            │
│  - Support per-user or global configuration             │
└─────────────────────────────────────────────────────────┘
```

### Database Schema

```sql
-- Table to store LLM configurations
CREATE TABLE llm_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,           -- "Production Config", "Test Config"
    provider VARCHAR(50) NOT NULL,        -- "google", "anthropic", "openai"
    model VARCHAR(100) NOT NULL,          -- "gemini-2.0-flash-exp"
    api_key TEXT NOT NULL,                -- Encrypted API key
    base_url VARCHAR(255),                -- For custom endpoints (Ollama, Together)
    max_tokens INTEGER DEFAULT 8192,
    temperature FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,       -- Currently selected config
    is_default BOOLEAN DEFAULT FALSE,     -- Fallback if no user config
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optional: Per-user configurations for multi-tenancy
CREATE TABLE user_llm_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,             -- Foreign key to users table
    llm_config_id INTEGER NOT NULL,       -- Foreign key to llm_configs
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (llm_config_id) REFERENCES llm_configs(id),
    UNIQUE(user_id)                       -- One config per user
);
```

### Implementation Steps

#### Step 1: Create Database Models

```python
# backend/src/answer_marker/models/llm_config.py

from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class LLMConfig(SQLModel, table=True):
    """Database model for LLM configurations."""

    __tablename__ = "llm_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    provider: str = Field(max_length=50)  # "google", "anthropic", "openai"
    model: str = Field(max_length=100)
    api_key: str  # Should be encrypted in production!
    base_url: Optional[str] = Field(default=None, max_length=255)
    max_tokens: int = Field(default=8192)
    temperature: float = Field(default=0.0)
    is_active: bool = Field(default=True)
    is_default: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

#### Step 2: Create LLM Config Repository

```python
# backend/src/answer_marker/repositories/llm_config_repo.py

from typing import Optional
from sqlmodel import Session, select
from answer_marker.models.llm_config import LLMConfig

class LLMConfigRepository:
    """Repository for LLM configuration CRUD operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_active_config(self) -> Optional[LLMConfig]:
        """Get the currently active LLM configuration."""
        stmt = select(LLMConfig).where(LLMConfig.is_active == True)
        return self.session.exec(stmt).first()

    def get_default_config(self) -> Optional[LLMConfig]:
        """Get the default LLM configuration."""
        stmt = select(LLMConfig).where(LLMConfig.is_default == True)
        return self.session.exec(stmt).first()

    def get_config_for_user(self, user_id: int) -> Optional[LLMConfig]:
        """Get LLM config for a specific user (for multi-tenancy)."""
        # Implementation depends on your user system
        pass

    def create_config(self, config: LLMConfig) -> LLMConfig:
        """Create a new LLM configuration."""
        # If setting as active, deactivate others
        if config.is_active:
            self._deactivate_all()

        self.session.add(config)
        self.session.commit()
        self.session.refresh(config)
        return config

    def update_config(self, config_id: int, updates: dict) -> Optional[LLMConfig]:
        """Update an existing LLM configuration."""
        config = self.session.get(LLMConfig, config_id)
        if not config:
            return None

        # If setting as active, deactivate others
        if updates.get("is_active"):
            self._deactivate_all()

        for key, value in updates.items():
            setattr(config, key, value)

        config.updated_at = datetime.now()
        self.session.commit()
        self.session.refresh(config)
        return config

    def set_active_config(self, config_id: int) -> Optional[LLMConfig]:
        """Set a configuration as active."""
        self._deactivate_all()
        config = self.session.get(LLMConfig, config_id)
        if config:
            config.is_active = True
            config.updated_at = datetime.now()
            self.session.commit()
            self.session.refresh(config)
        return config

    def _deactivate_all(self):
        """Deactivate all configurations."""
        stmt = select(LLMConfig).where(LLMConfig.is_active == True)
        configs = self.session.exec(stmt).all()
        for config in configs:
            config.is_active = False
        self.session.commit()
```

#### Step 3: Modify MarkingService to Use Database Config

```python
# backend/src/answer_marker/api/services/marking_service.py

class MarkingService:
    """Service for handling marking operations via API."""

    def __init__(self):
        """Initialize the marking service."""
        # Don't initialize LLM client at startup anymore
        self.llm_client = None
        # ... rest of init

    def _create_llm_client_from_db(self, db_session: Session) -> LLMClientCompat:
        """Create LLM client from database configuration.

        Args:
            db_session: Database session

        Returns:
            Configured LLM client
        """
        from answer_marker.repositories.llm_config_repo import LLMConfigRepository
        from answer_marker.llm.factory import create_llm_client

        # Get active configuration from database
        repo = LLMConfigRepository(db_session)
        llm_config = repo.get_active_config()

        if not llm_config:
            # Fallback to .env configuration
            from answer_marker.config import settings
            llm_config_dict = settings.get_llm_config()
            llm_client = create_llm_client(
                provider=llm_config_dict["provider"],
                model=llm_config_dict["model"],
                api_key=llm_config_dict["api_key"],
                base_url=llm_config_dict.get("base_url"),
            )
        else:
            # Use database configuration
            llm_client = create_llm_client(
                provider=llm_config.provider,
                model=llm_config.model,
                api_key=llm_config.api_key,  # Decrypt in production!
                base_url=llm_config.base_url,
            )

        return LLMClientCompat(llm_client)

    async def upload_marking_guide(
        self,
        file_path: Path,
        filename: str,
        # ... other params
        db_session: Session,  # ADD THIS
    ) -> tuple[str, MarkingGuide, bool]:
        """Process and store an uploaded marking guide."""

        # Create LLM client from database config
        llm_client = self._create_llm_client_from_db(db_session)

        # Create temporary doc processor with this client
        doc_processor = DocumentProcessor(llm_client)

        # ... rest of the method uses doc_processor
```

#### Step 4: Create Admin API Endpoints

```python
# backend/src/answer_marker/api/routes/admin.py

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from pydantic import BaseModel
from typing import List

from answer_marker.models.llm_config import LLMConfig
from answer_marker.repositories.llm_config_repo import LLMConfigRepository
from answer_marker.api.dependencies import get_db_session

router = APIRouter(prefix="/api/admin", tags=["admin"])


class LLMConfigCreate(BaseModel):
    """Request model for creating LLM config."""
    name: str
    provider: str  # "google", "anthropic", "openai", "ollama", "together"
    model: str
    api_key: str
    base_url: str | None = None
    max_tokens: int = 8192
    temperature: float = 0.0
    is_active: bool = False


class LLMConfigResponse(BaseModel):
    """Response model for LLM config (without API key)."""
    id: int
    name: str
    provider: str
    model: str
    api_key_masked: str  # Show only last 4 chars
    base_url: str | None
    max_tokens: int
    temperature: float
    is_active: bool
    created_at: str


@router.get("/llm-configs", response_model=List[LLMConfigResponse])
async def list_llm_configs(
    db: Session = Depends(get_db_session)
):
    """List all LLM configurations."""
    repo = LLMConfigRepository(db)
    # TODO: Implement list_all in repo
    configs = db.query(LLMConfig).all()

    return [
        LLMConfigResponse(
            id=c.id,
            name=c.name,
            provider=c.provider,
            model=c.model,
            api_key_masked=f"...{c.api_key[-4:]}" if c.api_key else "",
            base_url=c.base_url,
            max_tokens=c.max_tokens,
            temperature=c.temperature,
            is_active=c.is_active,
            created_at=c.created_at.isoformat()
        )
        for c in configs
    ]


@router.post("/llm-configs", response_model=LLMConfigResponse)
async def create_llm_config(
    config: LLMConfigCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new LLM configuration."""

    # TODO: Validate API key by testing a simple call
    # TODO: Encrypt API key before storing

    repo = LLMConfigRepository(db)
    db_config = LLMConfig(
        name=config.name,
        provider=config.provider,
        model=config.model,
        api_key=config.api_key,  # Should encrypt!
        base_url=config.base_url,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        is_active=config.is_active,
    )

    created = repo.create_config(db_config)

    return LLMConfigResponse(
        id=created.id,
        name=created.name,
        provider=created.provider,
        model=created.model,
        api_key_masked=f"...{created.api_key[-4:]}",
        base_url=created.base_url,
        max_tokens=created.max_tokens,
        temperature=created.temperature,
        is_active=created.is_active,
        created_at=created.created_at.isoformat()
    )


@router.put("/llm-configs/{config_id}/activate")
async def activate_llm_config(
    config_id: int,
    db: Session = Depends(get_db_session)
):
    """Set a configuration as active."""
    repo = LLMConfigRepository(db)
    config = repo.set_active_config(config_id)

    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    return {"message": f"Configuration '{config.name}' is now active"}


@router.post("/llm-configs/test")
async def test_llm_config(config: LLMConfigCreate):
    """Test an LLM configuration before saving."""
    from answer_marker.llm.factory import create_llm_client

    try:
        # Try to create client
        client = create_llm_client(
            provider=config.provider,
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url,
        )

        # Test with a simple message
        response = client.create_message(
            system="You are a test assistant.",
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=10,
            temperature=0.0
        )

        return {
            "success": True,
            "message": "LLM configuration is valid",
            "test_response": response.content[:50]
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Configuration test failed: {str(e)}"
        }
```

#### Step 5: Update API Routes to Use Database Session

```python
# backend/src/answer_marker/api/routes/marking.py

# Add dependency injection for database session
from answer_marker.api.dependencies import get_db_session

@router.post("/upload-marking-guide")
async def upload_marking_guide(
    # ... existing parameters
    db: Session = Depends(get_db_session),  # ADD THIS
):
    """Upload and process a marking guide."""

    # Pass db session to service
    guide_id, marking_guide, cached = await marking_service.upload_marking_guide(
        file_path=temp_path,
        filename=file.filename,
        title=title,
        description=description,
        subject=subject,
        grade=grade,
        job_id=job_id,
        db_session=db,  # ADD THIS
    )

    # ... rest of the code
```

---

## Implementation Roadmap

### Phase 1: Basic Runtime Configuration (Week 1)
1. ✅ Create `LLMConfig` database model
2. ✅ Create `LLMConfigRepository`
3. ✅ Add admin API endpoints
4. ✅ Modify `MarkingService` to use database config
5. ⬜ Add database migration scripts
6. ⬜ Test with different providers

### Phase 2: Admin UI (Week 2)
1. ⬜ Create Admin page in frontend
2. ⬜ LLM provider dropdown (Google, Anthropic, OpenAI, Ollama)
3. ⬜ API key input with validation
4. ⬜ Test configuration button
5. ⬜ List of saved configurations
6. ⬜ Activate/deactivate configurations

### Phase 3: Security & Production (Week 3)
1. ⬜ Encrypt API keys in database (use Fernet or similar)
2. ⬜ Add authentication/authorization to admin endpoints
3. ⬜ Add audit logging for config changes
4. ⬜ Add role-based access control
5. ⬜ Add rate limiting for admin endpoints

### Phase 4: Advanced Features (Week 4+)
1. ⬜ Per-user LLM configurations (multi-tenancy)
2. ⬜ Cost tracking per configuration
3. ⬜ Automatic failover to backup LLM
4. ⬜ A/B testing different LLMs
5. ⬜ LLM performance metrics dashboard

---

## Quick Start: Testing Runtime Config

To test that runtime configuration works with browser:

1. **Start API server normally:**
   ```bash
   cd backend
   poetry run uvicorn answer_marker.api.main:app --reload
   ```

2. **The server will use .env configuration** (or env vars if set)

3. **Browser calls API** - it uses whatever config the server loaded

4. **To avoid env var issues for testing:**
   ```bash
   # Option 1: Unset in current shell
   unset LLM_PROVIDER LLM_MODEL LLM_API_KEY
   poetry run uvicorn answer_marker.api.main:app --reload

   # Option 2: Use env -u
   env -u LLM_PROVIDER -u LLM_MODEL -u LLM_API_KEY \
       poetry run uvicorn answer_marker.api.main:app --reload
   ```

---

## Summary

**Your Question:** "Will browser still use wrong environment variables?"

**Answer:**
- The browser doesn't use env vars - it calls your API
- The API server uses env vars from the shell that started it
- Currently, config is loaded ONCE at startup and never changes
- For admin panel, you need to:
  1. Store LLM config in database (not .env)
  2. Create LLM client per-request (or add reload endpoint)
  3. Add admin API endpoints to manage configs
  4. Build admin UI to select provider and enter API key

**Next Steps:**
1. Implement database-backed LLM configuration
2. Modify `MarkingService` to create client per-request
3. Add admin API endpoints
4. Build admin UI for configuration management

This approach allows **true runtime configuration** without server restarts!
