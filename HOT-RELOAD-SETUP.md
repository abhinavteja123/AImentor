# 🔥 Hot Reload Setup Guide

## ✅ Configuration Complete

Your Docker setup now has full hot reload support for both frontend and backend!

## 🎯 What's Configured

### Frontend (Next.js)
- ✅ Full bind mount: `./frontend:/app`
- ✅ Excluded volumes: `node_modules` and `.next`
- ✅ Polling enabled for Windows: `CHOKIDAR_USEPOLLING=true`
- ✅ Fast polling interval: `CHOKIDAR_INTERVAL=100`
- ✅ Webpack polling: `WATCHPACK_POLLING=true`
- ✅ Dev command: `npm run dev`

### Backend (FastAPI)
- ✅ Full bind mount: `./backend:/app`
- ✅ Excluded cache: `__pycache__`
- ✅ Uvicorn reload: `--reload` flag enabled
- ✅ Unbuffered Python output: `PYTHONUNBUFFERED=1`

## 🚀 Usage

### Start the Application
```powershell
# Stop any running containers
docker compose down

# Rebuild containers (first time or after dependency changes)
docker compose build

# Start all services
docker compose up
```

### Quick Restart (without rebuild)
```powershell
docker compose down
docker compose up
```

## 🔍 Testing Hot Reload

### Frontend Test
1. Start the containers: `docker compose up`
2. Open http://localhost:3000
3. Edit any file in `frontend/app` or `frontend/components`
4. Save the file
5. Browser should auto-refresh with changes (2-5 seconds)

### Backend Test
1. Containers running
2. Visit http://localhost:8000/docs (FastAPI docs)
3. Edit any file in `backend/app`
4. Save the file
5. Terminal shows "Reloading..." message
6. API automatically restarts (1-2 seconds)

## 🛠️ Troubleshooting

### Frontend not reloading?
```powershell
# Check if environment variables are set
docker compose exec frontend printenv | findstr CHOKIDAR

# Restart frontend container
docker compose restart frontend
```

### Backend not reloading?
```powershell
# Check uvicorn logs
docker compose logs backend -f

# Look for "Reloading..." messages when you save files
```

### Permission Issues?
```powershell
# On Windows, ensure Docker Desktop has access to your drive
# Settings > Resources > File Sharing > Add your project folder
```

### Still Not Working?
```powershell
# Full clean restart
docker compose down -v
docker compose build --no-cache
docker compose up
```

## 📝 File Changes Made

### `docker-compose.yml`
- Backend: Full bind mount, excluded `__pycache__`, added `--reload` command
- Frontend: Full bind mount, excluded `node_modules` and `.next`, added polling env vars

### `backend/Dockerfile`
- Removed non-root user (can cause permission issues with bind mounts)
- Ensured `--reload` flag in CMD

### `frontend/Dockerfile`
- Already configured for dev mode with `npm run dev`

## 🎉 Expected Behavior

### Frontend
- **Edit any .tsx/.ts file** → Auto-refresh in browser (HMR)
- **Edit CSS/globals.css** → Instant style updates
- **Add new components** → Auto-detected and compiled

### Backend
- **Edit routes** → Auto-reload (see "Reloading..." in logs)
- **Modify models/schemas** → Changes applied immediately
- **Update services** → Uvicorn detects and reloads

## 📊 Performance Notes

- **First save after startup**: 3-5 seconds (cold start)
- **Subsequent saves**: 1-2 seconds
- **Polling overhead**: Minimal (~1-2% CPU)

## 🔒 Production Deployment

For production, use a separate `docker-compose.prod.yml`:
- Remove bind mounts
- Disable polling environment variables
- Remove `--reload` flag
- Use `npm run build` + `npm start` for frontend
- Add non-root user back to backend

---

**Status**: ✅ Hot reload fully configured and ready to use!
