# Answer Sheet Marker - TODO List

## 🎯 Current Status
- ✅ Core marking functionality working
- ✅ Question ID normalization fixed
- ✅ MCQ scoring bug fixed
- ✅ Frontend UI with assessment upload
- ✅ Backend API with all endpoints
- ✅ File-based caching system

---

## 🔥 High Priority (Next Sprint)

### 1. Database Layer with In-Memory Storage
**Priority**: HIGH | **Effort**: 3-4 hours | **Status**: TODO

**Goal**: Avoid burning API tokens by storing parsed assessments and results in a database.

**Features**:
- [ ] Design database schema with tables:
  - `assessments` - Store parsed assessment data with LLM results
  - `questions` - Store individual questions with marks, rubrics, types
  - `students` - Store student information
  - `answer_sheets` - Store submitted answer sheets
  - `markings` - Store marking results and evaluations
  - `marking_sessions` - Track marking history and timestamps
- [ ] Implement SQLModel/SQLAlchemy models
- [ ] Use SQLite for in-memory database (production: PostgreSQL)
- [ ] Create database migrations (Alembic)
- [ ] Add CRUD operations for all tables
- [ ] Cache parsed marking guides to avoid re-analyzing same PDF
- [ ] Cache answer sheet results for review/export
- [ ] Add database backup/export functionality
- [ ] API endpoints for database queries

**Benefits**:
- Save API costs by not re-parsing same assessments
- Enable historical data analysis
- Support multi-user scenarios
- Allow editing/reviewing past markings

---

### 2. Admin Panel & Authentication System
**Priority**: HIGH | **Effort**: 4-5 hours | **Status**: TODO

**Features**:
- [ ] **User Authentication**
  - [ ] JWT-based authentication
  - [ ] Login/logout endpoints
  - [ ] Password hashing (bcrypt)
  - [ ] Session management
  - [ ] Role-based access control (Admin, Teacher, Student)

- [ ] **Admin Dashboard** (`/admin`)
  - [ ] Admin login page
  - [ ] System overview dashboard
  - [ ] User management interface
  - [ ] LLM configuration panel
  - [ ] Usage analytics and cost tracking

- [ ] **LLM Provider Management**
  - [ ] Dropdown to select LLM provider with 10-15 options:

    **FREE/LOCAL:**
    - Ollama (Mistral-7B, Llama-3-8B)
    - LM Studio
    - LocalAI

    **LOW COST ($0.20-$1.00 per million tokens):**
    - Together.ai (Llama-3-70B)
    - Groq (Llama-3-70B - very fast!)
    - Fireworks.ai
    - DeepInfra
    - Anyscale

    **MEDIUM COST ($2-$8 per million tokens):**
    - Anthropic Claude Haiku
    - OpenAI GPT-3.5 Turbo
    - Google Gemini Flash
    - Mistral Small
    - Cohere Command

    **HIGH COST ($15-$30 per million tokens):**
    - Anthropic Claude Sonnet 4.5 (current)
    - OpenAI GPT-4 Turbo
    - Google Gemini Pro 1.5
    - Anthropic Claude Opus
    - OpenAI o1-preview

  - [ ] API key input field (per provider)
  - [ ] Test connection button
  - [ ] Model selection within provider
  - [ ] Set system-wide default LLM
  - [ ] Cost estimation calculator
  - [ ] Token usage tracking per provider

- [ ] **User Management**
  - [ ] Create/edit/delete users
  - [ ] Assign roles (Admin, Teacher, Student)
  - [ ] Set credit limits per user
  - [ ] Track user usage (assessments marked, tokens used)
  - [ ] Reset user passwords
  - [ ] Enable/disable user accounts
  - [ ] Bulk user import (CSV)

- [ ] **Credit/Quota System**
  - [ ] Define credit units (1 credit = 1 assessment, or token-based)
  - [ ] Admin sets credit limit per user
  - [ ] Track credit usage
  - [ ] Automatic blocking when credits exhausted
  - [ ] Credit top-up by admin
  - [ ] Usage history and reports
  - [ ] Email notifications for low credits

**Database Schema Addition**:
```sql
users (id, username, email, password_hash, role, credits, created_at)
llm_configs (id, provider, model, api_key_encrypted, is_active)
usage_logs (id, user_id, assessment_id, tokens_used, cost, timestamp)
```

---

### 3. General User Login & Dashboard
**Priority**: HIGH | **Effort**: 2-3 hours | **Status**: TODO

**Features**:
- [ ] User login page (`/login`)
- [ ] User registration page (`/register`) - optional, or admin creates users
- [ ] User dashboard showing:
  - [ ] Remaining credits
  - [ ] Assessments marked (history)
  - [ ] Recent marking reports
  - [ ] Usage statistics
  - [ ] Account settings
- [ ] Credit balance indicator in header
- [ ] Warning when credits low
- [ ] Logout functionality
- [ ] Profile management (change password, email)

---

## 🚀 Medium Priority (Sprint 2)

### 4. Batch Marking
**Priority**: MEDIUM | **Effort**: 2-3 hours | **Status**: TODO

**Features**:
- [ ] Upload multiple answer sheets at once (ZIP file or multiple PDFs)
- [ ] Background job queue for batch processing
- [ ] Progress indicator for batch marking
- [ ] Email notification when batch complete
- [ ] Batch results summary page
- [ ] Export batch results as CSV/Excel

---

### 5. Enhanced Export & Reporting
**Priority**: MEDIUM | **Effort**: 2 hours | **Status**: TODO

**Features**:
- [ ] Export individual reports as PDF
- [ ] Export class results as Excel/CSV
- [ ] Export with custom fields (student names, IDs, grades)
- [ ] Bulk export all markings for an assessment
- [ ] Generate class analytics report:
  - Average score
  - Score distribution histogram
  - Pass/fail rates
  - Question-wise difficulty analysis
- [ ] Customizable report templates

---

### 6. Analytics Dashboard
**Priority**: MEDIUM | **Effort**: 3 hours | **Status**: TODO

**Features**:
- [ ] Overall statistics cards (total assessments, students, avg score)
- [ ] Score distribution charts (histogram, box plot)
- [ ] Question difficulty analysis
- [ ] Time-series data (markings over time)
- [ ] Teacher performance metrics
- [ ] Most common errors/feedback themes
- [ ] LLM cost analytics per assessment type

---

### 7. Question Bank & Template Library
**Priority**: MEDIUM | **Effort**: 3-4 hours | **Status**: TODO

**Features**:
- [ ] Store reusable questions in a question bank
- [ ] Tag questions by topic, difficulty, type
- [ ] Create assessments from question bank (drag-and-drop)
- [ ] Share question templates across teachers
- [ ] Import/export question banks
- [ ] Auto-suggest similar questions
- [ ] Version control for questions

---

### 8. Email Notifications
**Priority**: MEDIUM | **Effort**: 2 hours | **Status**: TODO

**Features**:
- [ ] Email when marking complete
- [ ] Email when credits low
- [ ] Weekly usage summary email
- [ ] Assessment deadline reminders
- [ ] Student result notifications
- [ ] Configurable email templates
- [ ] Email preferences per user

---

## 💡 Nice to Have (Sprint 3+)

### 9. Advanced Features

#### 9.1 Plagiarism Detection
**Effort**: 4-5 hours
- [ ] Compare answer sheets for similarity
- [ ] Highlight potentially plagiarized sections
- [ ] Generate plagiarism report
- [ ] Use embeddings + cosine similarity
- [ ] Threshold configuration

#### 9.2 Grading Curves & Normalization
**Effort**: 2-3 hours
- [ ] Apply bell curve to scores
- [ ] Set custom grading scale
- [ ] Curve adjustment tools
- [ ] Comparative grading (rank students)

#### 9.3 Answer Sheet Templates
**Effort**: 3 hours
- [ ] Define answer sheet layouts
- [ ] OCR region mapping
- [ ] QR code for auto-identification
- [ ] Printable blank answer sheets

#### 9.4 AI Teaching Assistant
**Effort**: 4-5 hours
- [ ] Chat with LLM about marking results
- [ ] Ask "Why did student X get this score?"
- [ ] Get suggestions for feedback improvement
- [ ] Generate practice questions based on weak areas

#### 9.5 Webhooks & Integrations
**Effort**: 2-3 hours
- [ ] Webhook triggers for events (marking complete, etc.)
- [ ] REST API for external systems
- [ ] LMS integration (Canvas, Moodle, Blackboard)
- [ ] Google Classroom integration
- [ ] Microsoft Teams integration

#### 9.6 Mobile App
**Effort**: 8-10 hours
- [ ] React Native mobile app
- [ ] Upload photos of answer sheets
- [ ] View markings on mobile
- [ ] Push notifications
- [ ] Offline mode

#### 9.7 Audit Logs & Compliance
**Effort**: 2 hours
- [ ] Log all user actions
- [ ] Track marking changes/edits
- [ ] Export audit logs
- [ ] GDPR compliance features
- [ ] Data retention policies

#### 9.8 Backup & Disaster Recovery
**Effort**: 2 hours
- [ ] Automated database backups
- [ ] Export all data (assessments, markings)
- [ ] Import from backup
- [ ] Cloud storage integration (S3, Azure Blob)

#### 9.9 Multi-tenancy
**Effort**: 4-5 hours
- [ ] Support multiple schools/organizations
- [ ] Tenant isolation
- [ ] Tenant-specific branding
- [ ] Cross-tenant reporting (for admins)

#### 9.10 Collaborative Marking
**Effort**: 3-4 hours
- [ ] Multiple teachers mark same answer sheet
- [ ] Moderation workflow
- [ ] Comments and discussions on markings
- [ ] Second marker review mode
- [ ] Conflict resolution interface

---

## 🛠️ Technical Improvements

### 10. Infrastructure & DevOps
**Priority**: LOW | **Status**: TODO

- [ ] Docker Compose for full-stack deployment
- [ ] Kubernetes manifests
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Automated testing in pipeline
- [ ] Production deployment guide (AWS, GCP, Azure)
- [ ] Load balancing configuration
- [ ] CDN setup for frontend assets
- [ ] Monitoring & alerting (Prometheus, Grafana)
- [ ] Log aggregation (ELK stack)

### 11. Performance Optimization
**Priority**: LOW | **Status**: TODO

- [ ] Add Redis for caching
- [ ] Implement rate limiting
- [ ] Database query optimization
- [ ] Lazy loading for large PDFs
- [ ] Image optimization for frontend
- [ ] Gzip compression
- [ ] API response pagination
- [ ] Background job processing (Celery/RQ)

### 12. Security Enhancements
**Priority**: MEDIUM | **Status**: TODO

- [ ] API key encryption in database
- [ ] Two-factor authentication (2FA)
- [ ] CAPTCHA on login
- [ ] API rate limiting per user
- [ ] SQL injection protection audit
- [ ] XSS protection audit
- [ ] CSRF token implementation
- [ ] File upload validation (check for malware)
- [ ] Security headers (CSP, HSTS, etc.)
- [ ] Penetration testing

### 13. Testing & Quality
**Priority**: MEDIUM | **Status**: TODO

- [ ] Increase test coverage to 90%+
- [ ] E2E tests with Playwright/Cypress
- [ ] Load testing (locust, k6)
- [ ] Frontend unit tests (Vitest)
- [ ] API integration tests
- [ ] Performance benchmarks
- [ ] Accessibility testing (WCAG 2.1)

---

## 📋 Estimation Summary

| Feature | Priority | Effort | Impact |
|---------|----------|--------|--------|
| Database Layer | HIGH | 3-4h | Very High |
| Admin Panel & Auth | HIGH | 4-5h | Very High |
| User Login & Dashboard | HIGH | 2-3h | High |
| Batch Marking | MEDIUM | 2-3h | High |
| Export & Reporting | MEDIUM | 2h | Medium |
| Analytics Dashboard | MEDIUM | 3h | Medium |
| Question Bank | MEDIUM | 3-4h | Medium |
| Email Notifications | MEDIUM | 2h | Medium |
| Plagiarism Detection | LOW | 4-5h | Medium |
| Mobile App | LOW | 8-10h | Low |
| **TOTAL (High Priority)** | | **9-12h** | |
| **TOTAL (Medium Priority)** | | **12-15h** | |
| **TOTAL (All)** | | **40-60h** | |

---

## 🎯 Recommended Implementation Order

### Phase 1: Foundation (Week 1)
1. Database Layer (3-4h)
2. Admin Authentication (2h)
3. Admin LLM Config Panel (2-3h)

### Phase 2: User Management (Week 2)
4. User Login System (2h)
5. User Dashboard (1h)
6. Credit/Quota System (2h)
7. Admin User Management (2h)

### Phase 3: Enhanced Features (Week 3)
8. Batch Marking (2-3h)
9. Export & Reporting (2h)
10. Email Notifications (2h)
11. Analytics Dashboard (3h)

### Phase 4: Advanced Features (Week 4+)
12. Question Bank (3-4h)
13. Plagiarism Detection (4-5h)
14. Other nice-to-have features

---

## 🔐 Security Considerations

- [ ] Store API keys encrypted (AES-256)
- [ ] Use environment variables for secrets
- [ ] Implement RBAC (Role-Based Access Control)
- [ ] Add rate limiting to prevent abuse
- [ ] Validate and sanitize all file uploads
- [ ] Use HTTPS only in production
- [ ] Implement CORS properly
- [ ] Add CSP headers
- [ ] Regular security audits
- [ ] Keep dependencies updated

---

## 📝 Notes

- Database feature is **highest priority** - will save significant API costs
- Admin panel is **critical** for multi-user deployment
- Focus on Phase 1 & 2 first (foundation + user management)
- Mobile app and advanced features can wait until core system is solid
- Consider cloud deployment (Heroku, AWS, Azure) after Phase 2

---

## 🤝 Contributing

When implementing features from this TODO:
1. Create a new branch for each feature
2. Write tests before/during implementation
3. Update documentation
4. Create PR with clear description
5. Get code review
6. Merge to main after approval

---

**Last Updated**: 2025-11-07
**Version**: 1.0
