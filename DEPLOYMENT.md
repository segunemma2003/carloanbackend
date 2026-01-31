# Deployment Guide - Railway

This guide will help you deploy the AVTO LAIF Backend to Railway.

## Prerequisites

1. A GitHub account
2. A Railway account (sign up at https://railway.app)
3. Your code pushed to a GitHub repository

## Step 1: Prepare Your Repository

1. Make sure your code is committed and pushed to GitHub:
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push origin main
   ```

## Step 2: Create Railway Project

1. Go to https://railway.app and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will automatically detect the Dockerfile

## Step 3: Add Services

### PostgreSQL Database

1. In your Railway project, click "+ New"
2. Select "Database" → "Add PostgreSQL"
3. Railway will create a PostgreSQL database
4. Note the connection details (you'll need them for environment variables)

### Redis (Optional but Recommended)

1. Click "+ New" again
2. Select "Database" → "Add Redis"
3. Railway will create a Redis instance

## Step 4: Configure Environment Variables

In your Railway service settings, add these environment variables:

### Required Variables

```
# Application
APP_NAME=AVTO_LAIF
APP_ENV=production
DEBUG=False
SECRET_KEY=<generate-a-strong-secret-key>
API_V1_PREFIX=/api/v1

# Database (Railway will provide DATABASE_URL automatically)
# Just set this to use Railway's PostgreSQL:
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (if you added Redis service)
REDIS_URL=${{Redis.REDIS_URL}}

# JWT
JWT_SECRET_KEY=<generate-a-strong-jwt-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS (update with your frontend URL)
CORS_ORIGINS=["https://your-frontend-domain.com","https://www.your-frontend-domain.com"]

# Email (if using email service)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@avtolaif.ru

# SMS (if using SMS service)
SMS_PROVIDER=twilio
SMS_API_KEY=your-sms-api-key
SMS_API_SECRET=your-sms-secret

# Frontend URL (for email links)
FRONTEND_URL=https://your-frontend-domain.com
```

### Generate Secret Keys

You can generate secure keys using:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Run this twice to generate:
- `SECRET_KEY`
- `JWT_SECRET_KEY`

## Step 5: Run Database Migrations

1. In Railway, go to your service
2. Click on "Settings" → "Deploy"
3. Add a one-time command in "Deploy Command":
   ```
   alembic upgrade head
   ```
4. Or use Railway CLI:
   ```bash
   railway run alembic upgrade head
   ```

## Step 6: Deploy

1. Railway will automatically deploy when you push to your main branch
2. Or manually trigger a deployment from the Railway dashboard
3. Wait for the build to complete
4. Your app will be available at: `https://your-app-name.up.railway.app`

## Step 7: Verify Deployment

1. Check health endpoint: `https://your-app-name.up.railway.app/health`
2. Check API docs: `https://your-app-name.up.railway.app/docs`
3. Test admin panel: `https://your-app-name.up.railway.app/admin`

## Step 8: Create Admin User

You'll need to create an admin user. You can do this by:

1. Using Railway CLI to run a script:
   ```bash
   railway run python scripts/create_admin.py
   ```

2. Or connect to the database and insert manually:
   ```sql
   INSERT INTO users (email, password_hash, role, is_active, email_verified)
   VALUES ('admin@avtolaif.ru', '<hashed-password>', 'admin', true, true);
   ```

## Step 9: Custom Domain (Optional)

1. In Railway, go to your service
2. Click "Settings" → "Networking"
3. Click "Generate Domain" or "Add Custom Domain"
4. Follow the instructions to configure DNS

## Monitoring

- View logs in Railway dashboard
- Set up alerts in Railway settings
- Monitor database usage in Railway dashboard

## Troubleshooting

### Build Fails
- Check build logs in Railway dashboard
- Ensure all dependencies are in `requirements.txt`
- Verify Dockerfile is correct

### Database Connection Issues
- Verify `DATABASE_URL` environment variable is set
- Check PostgreSQL service is running
- Ensure database migrations have run

### App Crashes
- Check application logs
- Verify all required environment variables are set
- Check database connection string format

### Static Files Not Loading
- Ensure `app/static` directory exists
- Check file permissions
- Verify static file paths in code

## Railway CLI (Optional)

Install Railway CLI for easier management:
```bash
npm i -g @railway/cli
railway login
railway link  # Link to your project
railway up    # Deploy
railway logs  # View logs
```

## Cost Estimation

- **Free Tier**: $5/month credit
- **Hobby Plan**: $20/month (includes PostgreSQL and Redis)
- **Pro Plan**: $100/month (for production use)

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Status: https://status.railway.app

