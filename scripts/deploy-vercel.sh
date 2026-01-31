#!/bin/bash
# AI Mentor - Vercel Deployment Script (Linux/Mac)
# This script deploys the application to Vercel with auto-deploy disabled

set -e

echo "🚀 AI Mentor - Vercel Deployment Script"
echo "========================================"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed"
    echo "📦 Installing Vercel CLI globally..."
    npm install -g vercel
fi

echo "✅ Vercel CLI is installed"
echo ""

# Check if user is logged in
echo "🔐 Checking Vercel authentication..."
if ! vercel whoami &> /dev/null; then
    echo "❌ Not logged in to Vercel"
    echo "🔑 Please login to Vercel..."
    vercel login
else
    echo "✅ Already logged in to Vercel"
fi
echo ""

# Parse command line arguments
DEPLOYMENT_TYPE="${1:-production}"
PROJECT_NAME="${2:-ai-life-mentor}"

echo "📋 Deployment Configuration:"
echo "   • Environment: $DEPLOYMENT_TYPE"
echo "   • Project Name: $PROJECT_NAME"
echo ""

# Confirm deployment
read -p "🤔 Do you want to proceed with deployment? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Deploy based on type
if [ "$DEPLOYMENT_TYPE" = "production" ]; then
    echo "🚀 Deploying to PRODUCTION..."
    vercel --prod --yes --name "$PROJECT_NAME"
else
    echo "🧪 Deploying to PREVIEW..."
    vercel --yes --name "$PROJECT_NAME"
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Next Steps:"
echo "   1. Verify deployment at the provided URL"
echo "   2. Set up environment variables: npm run vercel:env"
echo "   3. Configure database connections"
echo ""
echo "⚠️  Note: Auto-deploy on push is DISABLED by default in vercel.json"
echo "   To enable it, go to Vercel Dashboard → Project Settings → Git"
