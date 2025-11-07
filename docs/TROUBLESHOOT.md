# Troubleshooting Guide

This document contains solutions to common issues encountered during development.

## Table of Contents
- [Module Import Errors](#module-import-errors)
- [Vite Dev Server Issues](#vite-dev-server-issues)
- [Backend API Issues](#backend-api-issues)
- [Build Issues](#build-issues)

---

## Module Import Errors

### Issue: "The requested module does not provide an export named 'MarkingGuideResponse'"

**Symptoms:**
- Blank white page in browser
- Console error: `Uncaught SyntaxError: The requested module '/src/types/api.ts' does not provide an export named 'MarkingGuideResponse'`
- Error occurs across different browsers (Arc, Safari, Chrome)

**Root Cause:**
- Duplicate type definitions in multiple files creating module conflicts
- TypeScript interfaces defined inline in component files conflicting with centralized types

**Solution:**
1. **Remove all inline type definitions** - Check for duplicate interface definitions:
   ```bash
   grep -r "interface MarkingGuideResponse" src/
   ```

2. **Create a barrel export file** - Create `src/types/index.ts`:
   ```typescript
   // Re-export all types from api.ts
   export * from './api';
   ```

3. **Update all imports** to use type-only imports from the barrel file:
   ```typescript
   // Before
   import { MarkingGuideResponse } from '../types/api';

   // After
   import type { MarkingGuideResponse } from '../types';
   ```

4. **Clear all caches and restart**:
   ```bash
   # In frontend directory
   rm -rf node_modules/.vite dist .vite
   pkill -9 -f vite
   npm run dev
   ```

5. **Hard refresh browser**: `Cmd + Shift + R` (Mac) or `Ctrl + Shift + R` (Windows/Linux)

**Files to Check:**
- `src/types/api.ts` - Central type definitions
- `src/types/index.ts` - Barrel export file
- `src/lib/api/*.ts` - API client files
- `src/pages/*.tsx` - Page components

**Prevention:**
- Always import types from `../types` (barrel file)
- Use `import type` for type-only imports
- Never define interfaces inline in component files if they exist in central types
- Run TypeScript check before committing: `npx tsc --noEmit`

---

## Vite Dev Server Issues

### Issue: Port Already in Use

**Symptoms:**
- Vite starts on different port (5174 instead of 5173)
- Multiple dev servers running simultaneously

**Solution:**
```bash
# Kill all Vite processes
pkill -9 -f vite

# Kill process on specific port
lsof -ti :5173 | xargs kill -9

# Restart dev server
npm run dev
```

### Issue: Hot Module Replacement (HMR) Not Working

**Symptoms:**
- Changes not reflecting in browser
- Need to manually refresh after every change

**Solution:**
1. **Clear Vite cache**:
   ```bash
   rm -rf node_modules/.vite
   ```

2. **Check Vite logs** for HMR updates:
   ```bash
   # You should see:
   # [vite] (client) hmr update /src/pages/YourFile.tsx
   ```

3. **Touch the file** to trigger HMR:
   ```bash
   touch src/types/api.ts
   ```

4. **Restart Vite** if HMR still not working

### Issue: Browser Caching Old Modules

**Symptoms:**
- Error persists after fixing code
- Different browsers show same error
- Changes not visible even after hard refresh

**Solution:**
1. **Complete cache clear**:
   ```bash
   # Backend
   cd backend
   rm -rf node_modules/.vite dist .vite

   # Frontend
   cd frontend
   rm -rf node_modules/.vite dist .vite
   ```

2. **Browser cache clear**:
   - Open DevTools (F12)
   - Right-click refresh button → "Empty Cache and Hard Reload"
   - Or use Incognito/Private mode

3. **Nuclear option** - Close ALL browser windows and restart browser completely

---

## Backend API Issues

### Issue: Backend Not Running or Wrong Port

**Symptoms:**
- Frontend can't connect to backend
- CORS errors in console
- 404 errors on API calls

**Solution:**
1. **Check if backend is running**:
   ```bash
   lsof -i :8000  # Default port
   lsof -i :8001  # Alternative port
   ```

2. **Start backend if not running**:
   ```bash
   cd backend
   poetry run uvicorn answer_marker.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Check backend logs** in `backend/logs/` folder

4. **Verify CORS configuration** in `backend/src/answer_marker/api/main.py`:
   ```python
   origins = [
       "http://localhost:5173",
       "http://localhost:3000",
       "http://localhost:8000",
   ]
   ```

### Issue: API Response Schema Mismatch

**Symptoms:**
- TypeScript errors in frontend
- Data not displaying correctly
- Console errors about missing properties

**Solution:**
1. **Check backend response models** in `backend/src/answer_marker/api/models/responses.py`

2. **Compare with frontend types** in `frontend/src/types/api.ts`

3. **Update types to match**:
   ```bash
   # Test backend endpoint
   curl http://localhost:8000/api/v1/marking-guides | python -m json.tool

   # Compare with TypeScript interface
   cat frontend/src/types/api.ts
   ```

4. **Restart both servers** after type changes

---

## Build Issues

### Issue: TypeScript Compilation Errors

**Symptoms:**
- Build fails
- Type errors in terminal

**Solution:**
1. **Check for errors**:
   ```bash
   cd frontend
   npx tsc --noEmit
   ```

2. **Common fixes**:
   - Ensure all imports are correct
   - Check for missing type definitions
   - Verify interface properties match usage

### Issue: Missing Dependencies

**Symptoms:**
- Module not found errors
- Import errors

**Solution:**
```bash
# Frontend
cd frontend
npm install

# Backend
cd backend
poetry install
```

---

## Development Workflow Best Practices

### Before Starting Development

```bash
# Start backend
cd backend
poetry run uvicorn answer_marker.api.main:app --reload --host 0.0.0.0 --port 8000

# In new terminal, start frontend
cd frontend
npm run dev
```

### Before Committing

```bash
# Check TypeScript
cd frontend
npx tsc --noEmit

# Check backend tests
cd backend
poetry run pytest

# Clear all caches
rm -rf frontend/node_modules/.vite
```

### If Something Breaks

1. **Check logs first**: `backend/logs/` and browser console
2. **Clear all caches**: Vite + browser
3. **Restart both servers**
4. **Check this troubleshooting guide**
5. **Check git diff** to see what changed

---

## Quick Fixes Checklist

When encountering any issue, try these in order:

- [ ] Hard refresh browser (`Cmd + Shift + R`)
- [ ] Clear Vite cache: `rm -rf node_modules/.vite`
- [ ] Restart dev server
- [ ] Check backend is running: `lsof -i :8000`
- [ ] Check for TypeScript errors: `npx tsc --noEmit`
- [ ] Check browser console for errors (F12)
- [ ] Check backend logs in `logs/` folder
- [ ] Try different browser or incognito mode
- [ ] Restart computer (last resort)

---

## Getting Help

If none of these solutions work:

1. Check the error message carefully
2. Look at the full stack trace in browser DevTools
3. Check backend logs in `backend/logs/`
4. Search for the error message online
5. Check if there are any uncommitted changes: `git status`
6. Try reverting recent changes: `git diff`

## Common Error Messages

### "Failed to fetch"
- Backend not running
- CORS issue
- Wrong API endpoint URL

### "Cannot read property of undefined"
- API response structure changed
- Missing data in response
- Type definitions don't match response

### "Module not found"
- Missing dependency - run `npm install`
- Wrong import path
- File moved or deleted

### "Port already in use"
- Another server running on same port
- Previous server didn't shut down properly
- Use `lsof -i :<port>` to find and kill process
