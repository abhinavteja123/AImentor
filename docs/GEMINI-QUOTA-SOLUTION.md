# Gemini API Free Tier Quota Limits

## Understanding the Error

The error you're seeing means:
- ✅ Your API key is **VALID** (authentication passed)
- ❌ You've **exceeded the free tier quota**
- ⏰ Daily quota limit reached

## Free Tier Quotas by Model

| Model | Requests Per Day (RPD) | Requests Per Minute (RPM) |
|-------|----------------------|---------------------------|
| `gemini-1.5-flash` | **1,500** | 15 |
| `gemini-1.5-pro` | 50 | 2 |
| `gemini-2.0-flash-exp` | 10 | 10 |
| `gemini-2.5-flash` | **20** | 2 |

**Your app was using**: `gemini-2.5-flash` (only 20 requests/day)
**Now switched to**: `gemini-1.5-flash` (1,500 requests/day)

## What I Fixed

✅ Changed model from `gemini-2.5-flash-preview-09-2025` to `gemini-1.5-flash`
✅ This gives you **75x more requests** per day (1,500 vs 20)
✅ Still fast and efficient for your use case

## How to Apply the Fix

### Option 1: Restart Backend Manually
```bash
cd backend
# Stop current server (Ctrl+C)
# Restart
uvicorn app.main:app --reload --port 8000
```

### Option 2: Docker Restart
```bash
docker-compose restart backend
```

## Quota Reset Schedule

- **Rate limit** (RPM): Resets every minute
- **Daily quota** (RPD): Resets at **midnight Pacific Time**

## Alternative Solutions

### 1. **Get More Free API Keys**
- Go to https://aistudio.google.com/
- Create a new project
- Generate a new API key
- Each key gets its own quota

### 2. **Upgrade to Paid Tier**
- Much higher limits
- Pay-as-you-go pricing
- Visit Google AI Studio → Billing

### 3. **Use Multiple Models**
You can configure fallback models:
```python
# Try gemini-1.5-flash first (1500 RPD)
# If quota exceeded, fallback to gemini-1.5-pro (50 RPD)
```

## Monitor Your Usage

Check current usage at: https://ai.dev/rate-limit

## Why gemini-2.5-flash Has Low Quota

- It's a newer preview model
- Google limits usage during preview period
- Production apps should use stable models like `gemini-1.5-flash`

---

**Recommended Action**: Restart your backend server now. You'll have 1,500 requests per day instead of 20!
