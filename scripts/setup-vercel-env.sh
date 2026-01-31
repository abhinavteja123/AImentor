#!/bin/bash
# AI Mentor - Vercel Environment Variables Setup Script (Linux/Mac)
# This script helps you set up environment variables for Vercel deployment

set -e

echo "🔧 AI Mentor - Vercel Environment Setup"
echo "========================================"
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed"
    echo "Please run: npm install -g vercel"
    exit 1
fi

# Check if user is logged in
if ! vercel whoami &> /dev/null; then
    echo "❌ Not logged in to Vercel"
    echo "Please run: vercel login"
    exit 1
fi

# Parse environment argument
ENV="${1:-production}"

echo "📋 Setting up environment variables for: $ENV"
echo ""
echo "⚠️  You'll need the following information:"
echo "   • PostgreSQL Database URL"
echo "   • MongoDB URL"
echo "   • Redis URL"
echo "   • Google API Key (Gemini)"
echo "   • JWT Secret Key"
echo ""

read -p "🤔 Do you want to continue? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Setup cancelled"
    exit 1
fi

echo ""
echo "🔐 Setting environment variables..."
echo ""

# Function to set environment variable
set_env_var() {
    local key=$1
    local prompt=$2
    local secret=$3
    
    echo "📝 $prompt"
    read -p "   Value: " value
    
    if [ -n "$value" ]; then
        if [ "$secret" = "true" ]; then
            vercel env add "$key" "$ENV" <<< "$value" > /dev/null 2>&1
        else
            vercel env add "$key" "$ENV" <<< "$value" > /dev/null 2>&1
        fi
        echo "   ✅ $key set"
    else
        echo "   ⚠️  Skipped $key"
    fi
    echo ""
}

# Set environment variables
set_env_var "DATABASE_URL" "PostgreSQL URL (e.g., postgresql://user:pass@host:5432/db)" "true"
set_env_var "MONGODB_URL" "MongoDB URL (e.g., mongodb://host:27017 or MongoDB Atlas)" "true"
set_env_var "MONGODB_DB" "MongoDB Database Name (e.g., ai_mentor)" "false"
set_env_var "REDIS_URL" "Redis URL (e.g., redis://host:6379 or Upstash Redis)" "true"
set_env_var "GOOGLE_API_KEY" "Google Gemini API Key" "true"
set_env_var "JWT_SECRET_KEY" "JWT Secret Key (generate a strong random string)" "true"
set_env_var "CORS_ORIGINS" "CORS Origins (e.g., https://yourdomain.com)" "false"
set_env_var "NEXT_PUBLIC_API_URL" "Public API URL (e.g., https://your-project.vercel.app)" "false"

echo "✅ Environment setup complete!"
echo ""
echo "📝 Next Steps:"
echo "   1. Verify variables in Vercel Dashboard"
echo "   2. Deploy your application: npm run vercel:deploy"
echo "   3. Test the deployment"
echo ""
