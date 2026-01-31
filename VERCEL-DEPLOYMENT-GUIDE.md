# AI Life Mentor - Vercel Deployment Guide

Complete guide for deploying the AI Life Mentor application to Vercel with manual deployment (auto-deploy disabled).

## 📋 Table of Contents
- [Prerequisites](#prerequisites)
- [Project Architecture](#project-architecture)
- [Pre-Deployment Setup](#pre-deployment-setup)
- [Deployment Process](#deployment-process)
- [Disabling Auto-Deploy](#disabling-auto-deploy)
- [Post-Deployment](#post-deployment)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- ✅ Node.js 18+ and npm
- ✅ Vercel CLI (`npm install -g vercel`)
- ✅ Git (for repository management)
- ✅ Vercel account (https://vercel.com)

### Required Services
- ✅ PostgreSQL database (Neon, Supabase, or Railway)
- ✅ MongoDB database (MongoDB Atlas)
- ✅ Redis cache (Upstash)
- ✅ Google Gemini API key

## Project Architecture

This is a monorepo with two main components:

```
AImentor/
├── frontend/          # Next.js 14 application
├── backend/           # FastAPI Python application
├── vercel.json        # Root Vercel configuration
├── scripts/           # Deployment scripts
└── VERCEL-ENV-GUIDE.md  # Environment variables guide
```

### Deployment Structure
- **Frontend**: Deployed as Next.js app
- **Backend**: Deployed as Vercel Serverless Functions
- **Routing**: API routes (`/api/v1/*`) → Backend, all others → Frontend

## Pre-Deployment Setup

### 1. Install Vercel CLI

```bash
# Install globally
npm install -g vercel

# Verify installation
vercel --version
```

### 2. Login to Vercel

```bash
vercel login
```

This will open a browser for authentication.

### 3. Set Up Managed Services

Before deploying, set up the required cloud services:

#### PostgreSQL (Choose one)
- **Neon** (Recommended): https://neon.tech
  - Create a project
  - Copy the connection string
  - Format: `postgresql://user:pass@host.neon.tech:5432/dbname?sslmode=require`

- **Supabase**: https://supabase.com
  - Create a project
  - Get connection string from Settings → Database

#### MongoDB
- **MongoDB Atlas**: https://www.mongodb.com/cloud/atlas
  - Create a free M0 cluster
  - Create database user
  - Whitelist Vercel IPs (or allow all: 0.0.0.0/0)
  - Copy connection string

#### Redis
- **Upstash** (Recommended): https://upstash.com
  - Create a Redis database
  - Choose "Global" for best performance
  - Copy the Redis URL with password

#### Google Gemini
- Get API key from: https://makersuite.google.com/app/apikey

### 4. Configure Environment Variables

Create a `.env.production` file locally (for reference only, DO NOT commit):

```bash
DATABASE_URL=postgresql://...
MONGODB_URL=mongodb+srv://...
MONGODB_DB=ai_mentor
REDIS_URL=rediss://...
GOOGLE_API_KEY=AIza...
JWT_SECRET_KEY=<generate-32-char-random-string>
CORS_ORIGINS=https://your-project.vercel.app
NEXT_PUBLIC_API_URL=https://your-project.vercel.app
```

**Generate secure JWT secret:**
```bash
# Linux/Mac
openssl rand -hex 32

# Windows PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

## Deployment Process

### Option 1: Automated Script (Recommended)

#### Windows:
```bash
# Navigate to project root
cd C:\Users\ABHINAV TEJA\Downloads\AImentor

# Deploy to production
scripts\deploy-vercel.bat production

# Or deploy to preview
scripts\deploy-vercel.bat preview
```

#### Linux/Mac:
```bash
# Make script executable
chmod +x scripts/deploy-vercel.sh

# Deploy to production
./scripts/deploy-vercel.sh production

# Or deploy to preview
./scripts/deploy-vercel.sh preview
```

### Option 2: Manual Deployment

```bash
# Navigate to project root
cd C:\Users\ABHINAV TEJA\Downloads\AImentor

# Login if not already
vercel login

# Deploy to preview first (recommended)
vercel

# After testing, deploy to production
vercel --prod
```

### Setting Environment Variables

#### Method 1: Automated Script

**Windows:**
```bash
scripts\setup-vercel-env.bat production
```

**Linux/Mac:**
```bash
chmod +x scripts/setup-vercel-env.sh
./scripts/setup-vercel-env.sh production
```

#### Method 2: Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Add each variable:
   - `DATABASE_URL`
   - `MONGODB_URL`
   - `MONGODB_DB`
   - `REDIS_URL`
   - `GOOGLE_API_KEY`
   - `JWT_SECRET_KEY`
   - `CORS_ORIGINS`
   - `NEXT_PUBLIC_API_URL`
5. Select environment (Production, Preview, Development)
6. Save and redeploy

#### Method 3: Vercel CLI

```bash
# Add variables one by one
vercel env add DATABASE_URL production
vercel env add MONGODB_URL production
vercel env add MONGODB_DB production
# ... continue for all variables

# List all variables
vercel env ls production
```

## Disabling Auto-Deploy

Auto-deploy on push is **DISABLED BY DEFAULT** in the `vercel.json` configuration:

```json
{
  "github": {
    "enabled": false,
    "autoAlias": false,
    "autoJobCancelation": false,
    "silent": true
  },
  "git": {
    "deploymentEnabled": false
  }
}
```

### Verify Auto-Deploy is Disabled

1. Go to Vercel Dashboard
2. Select your project
3. Go to **Settings** → **Git**
4. Ensure these are **DISABLED**:
   - ❌ "Enable Automatic Deployments"
   - ❌ "Auto-expose System Environment Variables"
   - ❌ "Automatically deploy Preview Deployments"

### Manual Deployment Only

With auto-deploy disabled, you must manually trigger deployments:

```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

### Re-enabling Auto-Deploy (If Needed)

If you want to enable auto-deploy later:

1. Update `vercel.json`:
```json
{
  "github": {
    "enabled": true
  },
  "git": {
    "deploymentEnabled": true
  }
}
```

2. Or use Vercel Dashboard:
   - Settings → Git → Enable Automatic Deployments

## Post-Deployment

### 1. Verify Deployment

```bash
# Your deployment URL will be shown after deployment
# Example: https://ai-life-mentor-xxxxx.vercel.app

# Test frontend
curl https://your-project.vercel.app

# Test backend API
curl https://your-project.vercel.app/api/v1/skills/master?limit=5
```

### 2. Update CORS Origins

Add your production URL to `CORS_ORIGINS`:
```bash
vercel env add CORS_ORIGINS production
# Enter: https://your-project.vercel.app
```

Then redeploy:
```bash
vercel --prod
```

### 3. Initialize Database

Run database initialization scripts from your local machine:

```bash
# Set your production database URL
$env:DATABASE_URL="postgresql://..." # Windows PowerShell
export DATABASE_URL="postgresql://..."  # Linux/Mac

# Run initialization
cd backend
python scripts/init_database.py
python scripts/seed_skills.py
```

### 4. Test All Features

- ✅ User registration
- ✅ User login
- ✅ Profile management
- ✅ Skills assessment
- ✅ Roadmap generation
- ✅ Resume builder
- ✅ Progress tracking
- ✅ AI chat mentor

### 5. Set Up Custom Domain (Optional)

1. Go to Project Settings → Domains
2. Add your custom domain
3. Configure DNS records
4. Update `CORS_ORIGINS` and `NEXT_PUBLIC_API_URL`

## Monitoring and Maintenance

### View Logs
```bash
# View deployment logs
vercel logs <deployment-url>

# View production logs
vercel logs --prod
```

### Check Deployment Status
```bash
vercel list
```

### Rollback Deployment
```bash
# List deployments
vercel list

# Promote a previous deployment to production
vercel promote <deployment-url>
```

## Troubleshooting

### Issue: Backend API Returns 404

**Solution:**
- Verify `vercel.json` routes are correct
- Check backend files are in `backend/app/` directory
- Ensure `backend/vercel.json` exists

### Issue: Environment Variables Not Working

**Solution:**
- Verify variables are set for the correct environment
- Redeploy after adding new variables
- Check variable names are exact (case-sensitive)

### Issue: Database Connection Timeout

**Solution:**
- Verify database allows connections from Vercel
- Check connection string format
- For MongoDB Atlas, whitelist 0.0.0.0/0
- For PostgreSQL, ensure `?sslmode=require` is added

### Issue: CORS Errors

**Solution:**
- Add your Vercel URL to `CORS_ORIGINS`
- Format: `https://yourdomain.com` (no trailing slash)
- Redeploy after updating
- Check browser console for exact origin

### Issue: Build Fails

**Solution:**
- Check build logs in Vercel Dashboard
- Ensure all dependencies are in `package.json` or `requirements.txt`
- Verify Node.js and Python versions
- Check for syntax errors

### Issue: Serverless Function Timeout

**Solution:**
- Optimize database queries
- Add indexes to frequently queried fields
- Use Redis caching
- Consider upgrading Vercel plan for longer timeouts

## Performance Optimization

### 1. Enable Caching
- Use Redis for session data and frequently accessed data
- Implement API response caching

### 2. Database Optimization
- Add indexes on frequently queried fields
- Use connection pooling
- Optimize queries

### 3. CDN Usage
- Static assets are automatically served via Vercel CDN
- Optimize images using Next.js Image component

### 4. Monitoring
- Set up Vercel Analytics
- Monitor serverless function execution time
- Track error rates

## Cost Estimation

### Vercel
- **Hobby (Free)**: Personal projects, 100 GB bandwidth/month
- **Pro ($20/month)**: Production apps, 1 TB bandwidth/month
- More info: https://vercel.com/pricing

### Database Services (Free Tiers)
- **Neon**: 0.5 GB storage, 100 hours compute/month
- **MongoDB Atlas**: 512 MB storage, shared cluster
- **Upstash Redis**: 10,000 commands/day
- **Google Gemini**: Free tier with rate limits

## Security Checklist

- ✅ Strong JWT secret (32+ characters)
- ✅ HTTPS enforced (automatic with Vercel)
- ✅ Environment variables secured
- ✅ Database connections use SSL/TLS
- ✅ CORS properly configured
- ✅ Rate limiting implemented
- ✅ Input validation on all endpoints
- ✅ Dependencies regularly updated

## Useful Commands

```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod

# View deployment URL
vercel ls

# View logs
vercel logs

# Promote deployment to production
vercel promote <deployment-url>

# Remove deployment
vercel rm <deployment-url>

# List environment variables
vercel env ls

# Pull environment variables locally
vercel env pull .env.local

# Alias a deployment
vercel alias <deployment-url> <custom-domain>
```

## Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel CLI Reference](https://vercel.com/docs/cli)
- [FastAPI on Vercel](https://vercel.com/docs/frameworks/python)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Environment Variables Guide](./VERCEL-ENV-GUIDE.md)

## Support

For issues specific to this deployment:
1. Check [VERCEL-ENV-GUIDE.md](./VERCEL-ENV-GUIDE.md)
2. Review Vercel deployment logs
3. Check database connection strings
4. Verify all environment variables are set

For Vercel platform issues:
- [Vercel Support](https://vercel.com/support)
- [Vercel Community](https://github.com/vercel/vercel/discussions)

---

**Last Updated**: February 2026  
**Version**: 1.0.0
