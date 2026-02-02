# Public API Endpoints (No Authentication Required)

All endpoints listed below are **publicly accessible** and do **NOT require authentication**.

## ✅ Public Endpoints

### Ads (Listings)
- `GET /api/v1/ads` - List/search ads (public)
- `GET /api/v1/ads/{ad_id}` - Get ad details (public)

### Categories
- `GET /api/v1/categories` - List categories (public)
- `GET /api/v1/categories/tree` - Get category tree (public)
- `GET /api/v1/categories/{category_id}` - Get category by ID (public)
- `GET /api/v1/categories/slug/{slug}` - Get category by slug (public)

### Vehicles (Reference Data)
- `GET /api/v1/vehicles/types` - List vehicle types (public)
- `GET /api/v1/vehicles/brands` - List brands (public)
- `GET /api/v1/vehicles/brands/{brand_id}` - Get brand by ID (public)
- `GET /api/v1/vehicles/models` - List models (public)
- `GET /api/v1/vehicles/models/{model_id}` - Get model by ID (public)
- `GET /api/v1/vehicles/generations` - List generations (public)
- `GET /api/v1/vehicles/generations/{generation_id}` - Get generation by ID (public)
- `GET /api/v1/vehicles/modifications` - List modifications (public)
- `GET /api/v1/vehicles/modifications/{modification_id}` - Get modification by ID (public)
- `GET /api/v1/vehicles/body-types` - List body types (public)
- `GET /api/v1/vehicles/transmissions` - List transmission types (public)
- `GET /api/v1/vehicles/fuel-types` - List fuel types (public)
- `GET /api/v1/vehicles/drive-types` - List drive types (public)
- `GET /api/v1/vehicles/colors` - List colors (public)
- `GET /api/v1/vehicles/references` - Get all reference data (public)

### Locations
- `GET /api/v1/locations/countries` - List countries (public)
- `GET /api/v1/locations/countries/{country_id}` - Get country with regions (public)
- `GET /api/v1/locations/regions` - List regions (public)
- `GET /api/v1/locations/regions/{region_id}` - Get region with cities (public)
- `GET /api/v1/locations/cities` - List cities (public)
- `GET /api/v1/locations/cities/{city_id}` - Get city details (public)
- `GET /api/v1/locations/search` - Search locations (public)
- `GET /api/v1/locations/nearby` - Get nearby cities (public)
- `GET /api/v1/locations/major-cities` - Get major cities (public)

### Banners
- `GET /api/v1/banners` - Get active banners (public)
- `GET /api/v1/banners/{banner_id}` - Get banner by ID (public)
- `POST /api/v1/banners/{banner_id}/impression` - Track impression (public)
- `POST /api/v1/banners/{banner_id}/click` - Track click (public)

## 🔒 Protected Endpoints (Require Authentication)

### User-Specific
- `GET /api/v1/users/me` - Get current user profile
- `GET /api/v1/users/{user_id}` - Get user profile
- `PATCH /api/v1/users/me` - Update profile
- `GET /api/v1/ads/my/ads` - Get my ads
- `POST /api/v1/ads` - Create ad
- `PATCH /api/v1/ads/{ad_id}` - Update ad
- `DELETE /api/v1/ads/{ad_id}` - Delete ad
- `GET /api/v1/favorites` - Get favorites
- `POST /api/v1/favorites` - Add to favorites
- `GET /api/v1/chat/dialogs` - Get chat dialogs
- `GET /api/v1/notifications` - Get notifications

### Admin Only
- All `POST`, `PATCH`, `DELETE` endpoints for categories, vehicles, locations
- `GET /api/v1/admin/stats` - Admin dashboard stats
- `GET /api/v1/moderation/pending` - Pending moderation items
- `POST /api/v1/moderation/report` - Create report (requires auth)
- All `/admin/*` endpoints in banners

## Test Public Endpoints

```bash
# Test ads (no auth required)
curl https://carloanbackend-production.up.railway.app/api/v1/ads

# Test categories (no auth required)
curl https://carloanbackend-production.up.railway.app/api/v1/categories

# Test vehicle types (no auth required)
curl https://carloanbackend-production.up.railway.app/api/v1/vehicles/types

# Test locations (no auth required)
curl https://carloanbackend-production.up.railway.app/api/v1/locations/countries

# Test banners (no auth required)
curl https://carloanbackend-production.up.railway.app/api/v1/banners
```

All these endpoints work **without any authentication tokens or cookies**.

