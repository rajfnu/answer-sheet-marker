# Full-Stack Architecture Plan: Answer Sheet Marker

## Overview

Restructure the monolithic application into a modern full-stack architecture with:
- **Backend**: FastAPI REST API (Python)
- **Frontend**: React SPA with modern UI/UX
- **Deployment**: Docker containers for independent deployment

---

## 1. Proposed Project Structure

```
answer-sheet-marker/
├── backend/
│   ├── src/
│   │   └── answer_marker/          # All current code
│   ├── tests/
│   ├── example/
│   ├── data/
│   ├── docs/
│   ├── pyproject.toml
│   ├── poetry.lock
│   ├── .env
│   ├── Dockerfile
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn/ui components
│   │   │   ├── AssessmentUpload.tsx
│   │   │   ├── AnswerSheetMarking.tsx
│   │   │   ├── ReportsDashboard.tsx
│   │   │   ├── AssessmentList.tsx
│   │   │   └── Layout.tsx
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── Assessments.tsx
│   │   │   ├── Marking.tsx
│   │   │   └── Reports.tsx
│   │   ├── hooks/
│   │   │   ├── useApi.ts
│   │   │   └── useUpload.ts
│   │   ├── lib/
│   │   │   ├── api.ts             # API client
│   │   │   └── utils.ts
│   │   ├── types/
│   │   │   └── api.ts             # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── .env.example
│   ├── .env.local
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── README.md
│
├── docker-compose.yml              # Full-stack deployment
├── docker-compose.dev.yml          # Development setup
├── .gitignore
└── README.md                       # Root documentation
```

---

## 2. Technology Stack

### Backend (No Changes)
- **Framework**: FastAPI (already implemented)
- **Language**: Python 3.11+
- **LLM**: Anthropic Claude Sonnet 4.5
- **Document Processing**: PyMuPDF, Tesseract OCR
- **Package Manager**: Poetry
- **Server**: Uvicorn

### Frontend (New)
- **Framework**: **React 18** with **TypeScript**
  - Industry standard, large ecosystem, excellent for complex UIs
  - TypeScript for type safety and better DX

- **Build Tool**: **Vite**
  - Fast HMR, modern build tooling
  - Better than Create React App (deprecated)

- **UI Library**: **shadcn/ui** + **Tailwind CSS**
  - Modern, accessible components
  - Highly customizable, copy-paste approach
  - Built on Radix UI primitives

- **State Management**: **React Query (TanStack Query)**
  - Perfect for API data fetching/caching
  - Built-in loading/error states

- **Routing**: **React Router v6**
  - Standard React routing solution

- **Form Handling**: **React Hook Form** + **Zod**
  - Performance and validation

- **HTTP Client**: **Axios**
  - Better than fetch for file uploads
  - Interceptors for auth/errors

### Deployment
- **Containerization**: Docker + Docker Compose
- **Backend Port**: 8001 (configurable)
- **Frontend Port**: 3000 (configurable)
- **Reverse Proxy**: Nginx (optional, for production)

---

## 3. Frontend Features & UI/UX

### Page 1: Dashboard (Home)
**Purpose**: Overview of system status and quick actions

**Components**:
- Stats cards: Total assessments, total reports, pending reviews
- Recent activity feed
- Quick action buttons: "Upload Assessment", "Mark Answer Sheet"
- System health indicator

**UX**:
- Clean, minimal design with cards layout
- Color-coded status indicators (green/yellow/red)
- Responsive grid layout

### Page 2: Assessments Management
**Purpose**: Upload and manage marking guides

**Components**:
- `AssessmentUpload`: Drag-drop PDF upload with progress bar
- `AssessmentList`: Table/grid showing all uploaded assessments
  - Assessment title, questions count, total marks, upload date
  - Actions: View details, Mark students, Delete
- `AssessmentDetails`: Modal showing full assessment breakdown

**UX**:
- Drag-and-drop file upload with visual feedback
- Real-time upload progress
- PDF preview thumbnail (optional)
- Search/filter assessments
- Toast notifications for success/errors

### Page 3: Answer Sheet Marking
**Purpose**: Mark student answer sheets

**Components**:
- `MarkingForm`:
  - Select assessment (dropdown with search)
  - Student ID input
  - PDF upload (drag-drop)
  - Submit button with loading state
- `MarkingProgress`: Real-time progress indicator
  - Processing status (Uploading → Analyzing → Evaluating → Scoring)
  - Estimated time remaining
- `MarkingResult`: Immediate results display
  - Score breakdown
  - Grade
  - Quick actions: View full report, Mark another

**UX**:
- Step-by-step wizard interface
- Instant validation feedback
- Processing animation during marking
- Success celebration animation

### Page 4: Reports & Analytics
**Purpose**: View all marking reports and analytics

**Components**:
- `ReportsTable`: Sortable, filterable table
  - Student ID, Assessment, Score, Grade, Date
  - Actions: View details, Download PDF
- `ReportFilters`: Filter by assessment, grade, date range
- `ReportDetails`: Modal with full question-by-question breakdown
- `Analytics`: Charts showing score distribution, pass rates

**UX**:
- Advanced filtering and sorting
- Export to CSV/PDF
- Visual charts using Recharts
- Pagination for large datasets

### Shared Components
- `Header`: Navigation bar with logo, menu, API status
- `Sidebar`: Quick navigation (collapsible on mobile)
- `FileUpload`: Reusable drag-drop upload component
- `LoadingSpinner`: Consistent loading states
- `ErrorBoundary`: Graceful error handling
- `Toast`: Notification system

---

## 4. Configuration Management

### Backend (.env)
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8001
API_CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# LLM Configuration
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5-20250929
ANTHROPIC_API_KEY=sk-ant-...

# Storage
UPLOAD_DIR=./data/uploads
MAX_FILE_SIZE=10485760  # 10MB
```

### Frontend (.env.local)
```bash
# Backend API URL (configurable)
VITE_API_BASE_URL=http://localhost:8001
VITE_API_TIMEOUT=300000  # 5 minutes for long operations

# Feature flags
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_PDF_PREVIEW=true
```

---

## 5. Docker Setup

### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application
COPY . .

# Expose port
EXPOSE 8001

# Run application
CMD ["poetry", "run", "uvicorn", "answer_marker.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Frontend Dockerfile
```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose (Production)
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8001
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./backend/data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=http://localhost:8001
    depends_on:
      - backend
    restart: unless-stopped
```

### Docker Compose (Development)
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    volumes:
      - ./backend:/app
      - /app/.venv  # Prevent overwriting
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8001
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    command: poetry run uvicorn answer_marker.api.main:app --host 0.0.0.0 --port 8001 --reload

  frontend:
    image: node:20-alpine
    working_dir: /app
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_BASE_URL=http://localhost:8001
    command: npm run dev -- --host 0.0.0.0
```

---

## 6. Development Workflow

### Initial Setup
```bash
# Clone repository
git clone <repo-url>
cd answer-sheet-marker

# Backend setup
cd backend
poetry install
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# Frontend setup
cd ../frontend
npm install
cp .env.example .env.local

# Start development servers
cd ..
docker-compose -f docker-compose.dev.yml up
```

### Development Commands
```bash
# Backend
cd backend
poetry run uvicorn answer_marker.api.main:app --reload

# Frontend
cd frontend
npm run dev

# Run tests
cd backend && poetry run pytest
cd frontend && npm run test

# Build for production
docker-compose build
```

---

## 7. Deployment Strategy

### Option 1: Docker Compose (Simple)
```bash
# Production deployment
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 2: Kubernetes (Advanced)
- Create K8s manifests for backend/frontend deployments
- Use persistent volumes for backend data
- Add ingress for routing

### Option 3: Cloud Platforms
- **AWS**: ECS/Fargate for containers, S3 for uploads
- **Google Cloud**: Cloud Run for containers
- **Azure**: Container Instances
- **Heroku**: Container registry

---

## 8. Migration Steps

### Step 1: Restructure (No Breaking Changes)
1. Create `backend/` directory
2. Move all current code to `backend/`
3. Update all absolute paths in config
4. Test backend still works
5. Commit: "Restructure: Move code to backend/"

### Step 2: Backend Docker
1. Create `backend/Dockerfile`
2. Create `docker-compose.yml` with backend service
3. Test Docker build and run
4. Commit: "Add Docker support for backend"

### Step 3: Frontend Scaffolding
1. Create `frontend/` directory
2. Initialize React + TypeScript + Vite project
3. Setup Tailwind CSS and shadcn/ui
4. Create basic layout and routing
5. Commit: "Initialize frontend application"

### Step 4: Frontend Implementation
1. Implement API client library
2. Create components (one page at a time)
3. Test each component with backend
4. Add error handling and loading states
5. Commit: "Implement frontend features"

### Step 5: Frontend Docker
1. Create `frontend/Dockerfile`
2. Update `docker-compose.yml` with frontend service
3. Configure nginx for production
4. Test full-stack deployment
5. Commit: "Add Docker support for frontend"

### Step 6: Documentation
1. Update README files
2. Add deployment guides
3. Create user documentation
4. Commit: "Update documentation"

---

## 9. API Integration Example

### Frontend API Client (`src/lib/api.ts`)
```typescript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes
});

// Upload marking guide
export const uploadMarkingGuide = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/api/v1/marking-guides/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      console.log(`Upload progress: ${percentCompleted}%`);
    },
  });

  return response.data;
};

// Mark answer sheet
export const markAnswerSheet = async (
  markingGuideId: string,
  studentId: string,
  file: File
) => {
  const formData = new FormData();
  formData.append('marking_guide_id', markingGuideId);
  formData.append('student_id', studentId);
  formData.append('file', file);

  const response = await apiClient.post('/api/v1/answer-sheets/mark', formData);
  return response.data;
};

// Get all assessments
export const getAssessments = async () => {
  const response = await apiClient.get('/api/v1/marking-guides');
  return response.data;
};

// Get all reports
export const getReports = async () => {
  const response = await apiClient.get('/api/v1/reports');
  return response.data;
};
```

---

## 10. Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| 1. Restructuring | Move to backend/, test | 30 minutes |
| 2. Backend Docker | Dockerfile, docker-compose | 30 minutes |
| 3. Frontend Setup | Initialize React app, install deps | 30 minutes |
| 4. UI Components | shadcn/ui setup, base components | 1 hour |
| 5. Assessment Upload | Component + API integration | 1 hour |
| 6. Answer Sheet Marking | Component + API integration | 1.5 hours |
| 7. Reports Dashboard | Component + API integration | 1.5 hours |
| 8. Frontend Docker | Dockerfile, nginx config | 30 minutes |
| 9. Testing | End-to-end testing | 1 hour |
| 10. Documentation | README, deployment guides | 30 minutes |
| **Total** | | **~8-9 hours** |

---

## 11. Advantages of This Architecture

✅ **Separation of Concerns**: Backend and frontend can be developed independently
✅ **Scalability**: Scale backend and frontend separately based on load
✅ **Technology Flexibility**: Can replace frontend framework without touching backend
✅ **Independent Deployment**: Deploy frontend updates without backend downtime
✅ **Better Developer Experience**: Modern tooling (Vite HMR, TypeScript, Tailwind)
✅ **Mobile Ready**: Can create React Native mobile app reusing same backend
✅ **Production Ready**: Docker containers for easy deployment anywhere
✅ **Maintainability**: Clear boundaries, easier to debug and test

---

## 12. Security Considerations

- **CORS**: Properly configured origins in backend
- **File Validation**: Frontend validates file types before upload
- **API Timeouts**: Handle long-running operations gracefully
- **Error Handling**: Don't expose sensitive backend errors to frontend
- **Environment Variables**: Never commit API keys or secrets
- **Rate Limiting**: Add rate limiting to backend endpoints (future)
- **Authentication**: Add JWT auth for multi-user system (future)

---

## Next Steps

Ready to proceed with implementation? The plan is:

1. ✅ Create this plan document
2. ⏭️ Restructure: Move code to `backend/`
3. ⏭️ Create backend Docker setup
4. ⏭️ Initialize frontend React application
5. ⏭️ Implement frontend UI components
6. ⏭️ Create frontend Docker setup
7. ⏭️ Test full-stack deployment
8. ⏭️ Update documentation

**Total estimated time: 8-9 hours of focused work**

Shall we begin with Step 1: Restructuring?
