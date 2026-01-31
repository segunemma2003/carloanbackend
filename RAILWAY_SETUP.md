# Railway Setup Guide - Quick Fix for Database Connection

## The Error You're Seeing

```
ConnectionRefusedError: [Errno 111] Connection refused
```

This means the app can't connect to the PostgreSQL database.

## Quick Fix Steps

### 1. Add PostgreSQL Service in Railway

1. Go to your Railway project dashboard
2. Click **"+ New"** button
3. Select **"Database"** → **"Add PostgreSQL"**
4. Railway will automatically create a PostgreSQL database

### 2. Link Database to Your App

1. In your Railway project, you should see:
   - Your app service
   - A PostgreSQL service
2. Click on your **app service**
3. Go to **"Variables"** tab
4. Railway should automatically add `DATABASE_URL` - if not, add it manually:
   - Variable name: `DATABASE_URL`
   - Value: Click **"Add Reference"** → Select your PostgreSQL service → Select `DATABASE_URL`

### 3. Verify Environment Variables

Make sure these are set in your app service:

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

**Important:** Railway provides `DATABASE_URL` in format `postgresql://...` but our app automatically converts it to `postgresql+asyncpg://...` format.

### 4. Redeploy

1. Railway should auto-redeploy when you add the database
2. Or manually trigger a redeploy from the dashboard
3. Check the logs - you should see "Database initialized"

## If Database Still Doesn't Connect

### Check Database URL Format

Railway's `DATABASE_URL` should look like:
```
postgresql://postgres:password@hostname:5432/railway
```

Our app automatically converts it to:
```
postgresql+asyncpg://postgres:password@hostname:5432/railway
```

### Manual Database URL Setup

If automatic linking doesn't work:

1. Go to your PostgreSQL service in Railway
2. Click **"Variables"** tab
3. Copy the connection details:
   - `PGHOST`
   - `PGPORT`
   - `PGDATABASE`
   - `PGUSER`
   - `PGPASSWORD`
4. In your app service, set `DATABASE_URL` manually:
   ```
   postgresql+asyncpg://PGUSER:PGPASSWORD@PGHOST:PGPORT/PGDATABASE
   ```

### Run Migrations

After database is connected, run migrations:

1. In Railway, go to your app service
2. Click **"Deploy"** tab
3. Add a one-time command:
   ```
   alembic upgrade head
   ```
4. Or use Railway CLI:
   ```bash
   railway run alembic upgrade head
   ```

## Verify Connection

Once deployed, check logs for:
- ✅ "Database initialized" - Success!
- ❌ "Connection refused" - Database not linked or URL wrong

## Common Issues

### Issue: DATABASE_URL not set
**Fix:** Add PostgreSQL service and link it to your app

### Issue: Wrong URL format
**Fix:** Our app auto-converts `postgresql://` to `postgresql+asyncpg://`, so just use Railway's `DATABASE_URL` as-is

### Issue: Database not ready yet
**Fix:** Wait a few seconds after creating the database service, then redeploy

### Issue: SSL connection errors
**Fix:** Railway's PostgreSQL uses SSL. Our connection should handle this automatically.

## Need Help?

- Check Railway logs: Dashboard → Your Service → Logs
- Verify database is running: Dashboard → PostgreSQL Service → Status should be "Active"
- Test connection manually using Railway CLI:
  ```bash
  railway connect postgres
  ```

