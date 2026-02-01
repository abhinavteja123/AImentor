# Build Reproducibility Checklist

This document provides a step-by-step checklist to ensure reproducible builds of the AI Life Mentor application.

## 📋 Pre-Build Checklist

### Environment Setup
- [ ] Python 3.10+ installed and in PATH
- [ ] Node.js 18+ installed and in PATH
- [ ] Git installed for cloning repository
- [ ] Access to PostgreSQL, MongoDB, and Redis (local or cloud)
- [ ] Google Gemini API key obtained from https://aistudio.google.com/

### System Dependencies
```bash
# Verify installations
python --version    # Should show 3.10+
node --version      # Should show 18+
npm --version       # Should be included with Node
git --version
```

---

## 🔧 Backend Build Steps

### 1. Clone Repository
```bash
git clone <your-repository-url>
cd AImentor/backend
```

### 2. Python Environment Setup
```bash
# Create isolated virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Verify activation
which python  # Should point to venv
```

### 3. Install Dependencies
```bash
# Install exact versions from requirements.txt
pip install --no-cache-dir -r requirements.txt

# Verify critical packages
python -c "import fastapi, sqlalchemy, google.generativeai; print('✓ Dependencies OK')"
```

### 4. Environment Configuration
```bash
# Copy example environment file
cp .env.example .env  # Or create manually

# Required variables (edit .env):
GOOGLE_API_KEY=your_api_key_here
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/
REDIS_URL=redis://default:pass@host:6379
JWT_SECRET_KEY=$(openssl rand -hex 32)  # Generate secure key
```

### 5. Database Initialization
```bash
# Connect to PostgreSQL and create database
createdb aimentor

# Run initialization scripts
python -m scripts.seed_database
python -m scripts.seed_skills
```

### 6. Verify Backend Build
```bash
# Test import chain
python -c "from app.main import app; print('✓ Backend imports OK')"

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test health endpoint (in new terminal)
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

---

## 🎨 Frontend Build Steps

### 1. Navigate to Frontend
```bash
cd ../frontend  # From backend directory
```

### 2. Install Dependencies
```bash
# Use npm ci for reproducible install (uses package-lock.json)
npm ci

# Alternative: If package-lock doesn't exist
npm install

# Verify critical packages
npm list next react typescript
```

### 3. Environment Configuration
```bash
# Create environment file
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
```

### 4. Build for Production
```bash
# Create optimized production build
npm run build

# Output should show:
# - Routes compiled successfully
# - No build errors
# - Build completed in X seconds
```

### 5. Verify Frontend Build
```bash
# Test production build locally
npm run start

# Should start on port 3000
# Visit http://localhost:3000

# Alternative: Run development mode
npm run dev
```

---

## 🐳 Docker Build (Alternative)

### 1. Build Images
```bash
cd .. # Return to project root

# Build all services
docker-compose build

# Or build specific service
docker-compose build backend
docker-compose build frontend
```

### 2. Start Services
```bash
# Start all containers
docker-compose up -d

# Check container status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Verify Docker Build
```bash
# Test backend
curl http://localhost:8000/docs

# Test frontend
curl http://localhost:3000

# Check databases
docker-compose exec postgres psql -U postgres -d aimentor -c "SELECT version();"
docker-compose exec mongodb mongosh --eval "db.version()"
docker-compose exec redis redis-cli PING
```

---

## ✅ Build Verification Tests

### Backend Tests
```bash
cd backend

# Test 1: Import all modules
python -c "
from app.main import app
from app.database.postgres import get_db
from app.database.mongodb import get_mongodb
from app.services.ai.gemini_service import GeminiService
print('✓ All imports successful')
"

# Test 2: API health
curl -f http://localhost:8000/health || echo "✗ Health check failed"

# Test 3: API documentation
curl -f http://localhost:8000/docs || echo "✗ Docs not accessible"

# Test 4: Database connectivity (if running)
python scripts/test_connections.py
```

### Frontend Tests
```bash
cd frontend

# Test 1: Build output exists
test -d .next && echo "✓ Build output exists" || echo "✗ Build failed"

# Test 2: Access local server
curl -f http://localhost:3000 || echo "✗ Frontend not accessible"

# Test 3: TypeScript compilation
npm run type-check || echo "✗ Type errors found"
```

---

## 🔒 Security Checklist

Before deploying or sharing:

- [ ] All API keys are in .env files (not committed to git)
- [ ] .gitignore includes .env, .env.local, __pycache__, node_modules
- [ ] JWT_SECRET_KEY is cryptographically secure (32+ characters)
- [ ] Database passwords are strong (16+ characters)
- [ ] CORS origins are properly configured (not wildcard in production)
- [ ] Debug mode is disabled in production (DEBUG=False)

---

## 📊 Build Troubleshooting

### Common Build Failures

**Python Dependencies Conflict**
```bash
# Clear pip cache and reinstall
pip cache purge
pip install --no-cache-dir --force-reinstall -r requirements.txt
```

**Node Modules Corruption**
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

**Port Conflicts**
```bash
# Find and kill process on port
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Database Connection Timeout**
```bash
# Test connectivity
pg_isready -h hostname -p 5432
mongosh "mongodb://host:27017" --eval "db.version()"
redis-cli -h host -p 6379 PING
```

---

## 📝 Build Log Template

Document your build process:

```
Date: YYYY-MM-DD
Builder: [Your Name]
Environment: [Windows/macOS/Linux]
Python Version: [e.g., 3.11.5]
Node Version: [e.g., 18.17.0]

Backend Build:
- [✓] Virtual environment created
- [✓] Dependencies installed (X packages)
- [✓] Environment configured
- [✓] Database initialized
- [✓] Server starts successfully
- [✓] Health check passed

Frontend Build:
- [✓] Dependencies installed (X packages)
- [✓] Environment configured
- [✓] Build completed without errors
- [✓] Server starts successfully
- [✓] Can access homepage

Issues Encountered: [None/Describe]
Time to Complete: [X minutes]
```

---

## 🚀 Deployment Build

For production deployment:

### Vercel Deployment
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy backend
cd backend
vercel --prod

# Deploy frontend
cd frontend
vercel --prod
```

See [VERCEL-DEPLOYMENT-GUIDE.md](VERCEL-DEPLOYMENT-GUIDE.md) for detailed instructions.

---

## 📞 Build Support

If you encounter issues:

1. Check the [Troubleshooting](#-build-troubleshooting) section above
2. Review main [README.md](../README.md) troubleshooting section
3. Search existing GitHub issues
4. Create a new issue with:
   - Your build log
   - System information (OS, versions)
   - Error messages (full stack trace)
   - Steps to reproduce

---

**Last Updated**: February 2026
