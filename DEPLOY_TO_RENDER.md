# Deploy Aurora Q&A System to Render.com (Free Tier)

## Quick Deployment Steps

### Step 1: Add Payment Information (Required for MCP)
1. Go to https://dashboard.render.com/billing
2. Add a credit card (no charges for free tier)
3. Once added, the MCP can deploy automatically

### Step 2: Manual Deployment via Dashboard

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Sign in or create an account

2. **Create New Web Service**
   - Click "New +" button
   - Select "Web Service"

3. **Connect Repository**
   - Connect your GitHub account if not already connected
   - Select repository: `vivek-tiwari-vt/aurora-assessment`
   - Click "Connect"

4. **Configure Service**
   - **Name**: `aurora-qa-system`
   - **Region**: `Oregon` (or closest to you)
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: (leave empty)
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `docker/Dockerfile`
   - **Docker Build Context**: (leave empty or set to `.`)
   - **Plan**: Select `Free` (750 hours/month free)

5. **Environment Variables**
   Click "Advanced" and add:
   - `LOG_LEVEL` = `INFO`
   - `GEMINI_API_KEYS` = `your_actual_gemini_api_key_here` (comma-separated for multiple keys)

6. **Deploy**
   - Click "Create Web Service"
   - Wait for build to complete (5-10 minutes first time)
   - Your app will be live at: `https://aurora-qa-system.onrender.com`

### Step 3: Using render.yaml (Alternative Method)

If Render supports Blueprint import:
1. Go to https://dashboard.render.com
2. Click "New +" → "Blueprint"
3. Connect repository and select `render.yaml`
4. Render will auto-configure from the YAML file

## Important Notes

### Free Tier Limitations:
- ⚠️ Services spin down after 15 minutes of inactivity
- ⚠️ First request after spin-down may take 30-60 seconds
- ⚠️ 750 free instance hours per month
- ⚠️ Limited bandwidth included

### After Deployment:
1. Update `GEMINI_API_KEYS` environment variable with your actual API key
2. Test the deployment: `https://aurora-qa-system.onrender.com/api`
3. The service will auto-deploy on every git push (if auto-deploy is enabled)

## Troubleshooting

### Build Fails:
- Check Dockerfile path is correct: `docker/Dockerfile`
- Ensure all dependencies are in `requirements.txt`
- Check build logs in Render dashboard

### Service Won't Start:
- Verify `GEMINI_API_KEYS` is set correctly
- Check application logs in Render dashboard
- Ensure port 8000 is exposed (already configured in Dockerfile)

### Slow First Request:
- Normal for free tier (service spins up from sleep)
- Subsequent requests are faster

## Your Deployment URL

Once deployed, your service will be available at:
**https://aurora-qa-system.onrender.com**

API endpoints:
- `GET /` - Web interface
- `GET /api` - Health check
- `POST /api/ask` - Ask questions
- `GET /api/stats` - System statistics

