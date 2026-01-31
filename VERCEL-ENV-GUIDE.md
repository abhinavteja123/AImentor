# Vercel Environment Variables Configuration

This document lists all required environment variables for deploying AI Life Mentor to Vercel.

## Required Environment Variables

### Backend API Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` | ✅ Yes |
| `MONGODB_URL` | MongoDB connection URL | `mongodb://host:27017` or Atlas URL | ✅ Yes |
| `MONGODB_DB` | MongoDB database name | `ai_mentor` | ✅ Yes |
| `REDIS_URL` | Redis connection URL | `redis://host:6379` or Upstash URL | ✅ Yes |
| `GOOGLE_API_KEY` | Google Gemini API key | `AIza...` | ✅ Yes |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Strong random string (min 32 chars) | ✅ Yes |
| `CORS_ORIGINS` | Allowed CORS origins | `https://yourdomain.com` | ✅ Yes |

### Optional Backend Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GEMINI_MODEL` | Gemini model version | `gemini-2.0-flash-exp` | ❌ No |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` | ❌ No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry in minutes | `1440` (24 hours) | ❌ No |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | `30` | ❌ No |
| `APP_NAME` | Application name | `AI Life Mentor` | ❌ No |
| `APP_VERSION` | Application version | `1.0.0` | ❌ No |
| `DEBUG` | Debug mode | `false` | ❌ No |

### Frontend Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `https://your-project.vercel.app` | ✅ Yes |

## Recommended Managed Services for Vercel

Since Vercel is a serverless platform, you'll need managed database services:

### 1. **PostgreSQL Options**
- **Neon** (Recommended) - Serverless PostgreSQL
  - Free tier available
  - Auto-scaling
  - URL: https://neon.tech
  
- **Supabase** - PostgreSQL with additional features
  - Free tier available
  - URL: https://supabase.com
  
- **Railway** - PostgreSQL hosting
  - Free trial, then paid
  - URL: https://railway.app

### 2. **MongoDB Options**
- **MongoDB Atlas** (Recommended)
  - Free tier (M0) available
  - Fully managed
  - URL: https://www.mongodb.com/cloud/atlas

### 3. **Redis Options**
- **Upstash** (Recommended for Vercel)
  - Serverless Redis
  - Free tier available
  - Vercel Integration available
  - URL: https://upstash.com
  
- **Redis Cloud**
  - Free tier available
  - URL: https://redis.com/cloud

### 4. **Google Gemini API**
- **Google AI Studio**
  - Get your API key
  - URL: https://makersuite.google.com/app/apikey

## Setting Environment Variables

### Method 1: Using Vercel CLI (Automated)

```bash
# For Windows
scripts\setup-vercel-env.bat production

# For Linux/Mac
./scripts/setup-vercel-env.sh production
```

### Method 2: Using Vercel Dashboard (Manual)

1. Go to your project on Vercel Dashboard
2. Navigate to **Settings** → **Environment Variables**
3. Add each variable with the appropriate value
4. Select the environment (Production, Preview, Development)
5. Click **Save**

### Method 3: Using Vercel CLI (Manual)

```bash
# Add a single environment variable
vercel env add DATABASE_URL production

# Add for all environments
vercel env add DATABASE_URL
```

## Environment-Specific Configuration

### Production Environment
- Use production database URLs
- Set `DEBUG=false`
- Use strong JWT secret
- Configure production CORS origins

### Preview Environment
- Can use staging databases
- Set `DEBUG=true` for testing
- Use preview-specific origins

### Development Environment
- Use development databases
- Set `DEBUG=true`
- Allow localhost origins

## Security Best Practices

1. **Never commit** environment variables to Git
2. **Use strong secrets** for JWT_SECRET_KEY (min 32 characters)
3. **Rotate secrets** regularly
4. **Limit CORS origins** to specific domains
5. **Use SSL/TLS** for all database connections
6. **Enable IP whitelisting** on database services if possible
7. **Use separate databases** for production and preview environments

## Generating Secure Secrets

### JWT Secret Key
```bash
# Linux/Mac
openssl rand -hex 32

# Windows (PowerShell)
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

## Verifying Environment Variables

```bash
# List all environment variables for production
vercel env ls production

# Pull environment variables to local .env file (for testing)
vercel env pull .env.local
```

## Troubleshooting

### Variables Not Loading
- Ensure variables are set for the correct environment
- Redeploy after adding new variables
- Check variable names match exactly (case-sensitive)

### Database Connection Errors
- Verify connection strings are correct
- Check database is accessible from Vercel's region
- Ensure database allows connections from Vercel IPs

### CORS Errors
- Add your Vercel deployment URL to CORS_ORIGINS
- Include both with and without trailing slash
- Format: `https://yourdomain.com,https://www.yourdomain.com`

## Example .env.production (Template)

```bash
# DO NOT COMMIT THIS FILE - Template only
DATABASE_URL=postgresql://user:password@neon.tech:5432/dbname?sslmode=require
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net
MONGODB_DB=ai_mentor
REDIS_URL=rediss://default:password@upstash-redis.com:6379
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-characters-long
CORS_ORIGINS=https://your-project.vercel.app,https://www.your-domain.com
NEXT_PUBLIC_API_URL=https://your-project.vercel.app
```

## Additional Resources

- [Vercel Environment Variables Documentation](https://vercel.com/docs/concepts/projects/environment-variables)
- [Vercel CLI Documentation](https://vercel.com/docs/cli)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
