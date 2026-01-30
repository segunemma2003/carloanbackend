# AVTO LAIF - Frontend API Integration Guide

**For User Features (Non-Admin)**

---

## 📋 Table of Contents

1. [Authentication & User Management](#1-authentication--user-management)
2. [User Profile](#2-user-profile)
3. [Vehicle References (Cascading Selection)](#3-vehicle-references-cascading-selection)
4. [Categories & Locations](#4-categories--locations)
5. [Advertisements (Ads)](#5-advertisements-ads)
6. [Chat & Messaging](#6-chat--messaging)
7. [Favorites & Comparison](#7-favorites--comparison)
8. [Search & Filters](#8-search--filters)
9. [WebSocket Integration](#9-websocket-integration)

---

## 🔐 Base URL & Authentication

**Base API URL:** `http://localhost:8000/api/v1`

**Authentication:** 
- All authenticated endpoints require JWT access token
- Token is stored in HttpOnly cookie named `access_token`
- Token expires in 15 minutes, refresh automatically with refresh token

---

## 1. Authentication & User Management

### 📖 User Stories

**US-1.1:** As a guest, I want to register an account so I can post ads and chat with sellers.

**US-1.2:** As a user, I want to login to my account so I can access my ads and messages.

**US-1.3:** As a user, I want to reset my password if I forget it.

**US-1.4:** As a user, I want to verify my email to activate my account.

---

### 1.1 User Registration

**Endpoint:** `POST /api/v1/auth/register`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "name": "John Doe",
  "phone": "+79001234567",
  "account_type": "individual",
  "accept_terms": true
}
```

**Success Response (201):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "phone": "+79001234567",
    "role": "user",
    "account_type": "individual",
    "email_verified": false,
    "phone_verified": false,
    "created_at": "2026-01-30T10:00:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Frontend Implementation:**
```javascript
async function register(userData) {
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // Important for cookies
    body: JSON.stringify(userData)
  });
  
  if (response.ok) {
    const data = await response.json();
    // Tokens are automatically stored in cookies
    // Redirect to verification page or dashboard
    return data.user;
  }
  throw await response.json();
}
```

---

### 1.2 User Login

**Endpoint:** `POST /api/v1/auth/login`

**Request Body:**
```json
{
  "email_or_phone": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Success Response (200):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "account_type": "individual"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Frontend Implementation:**
```javascript
async function login(credentials) {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(credentials)
  });
  
  if (response.ok) {
    const data = await response.json();
    localStorage.setItem('user', JSON.stringify(data.user));
    return data.user;
  }
  throw await response.json();
}
```

---

### 1.3 Token Refresh

**Endpoint:** `POST /api/v1/auth/refresh`

**Request:** No body needed (uses refresh_token cookie)

**Success Response (200):**
```json
{
  "access_token": "new_access_token...",
  "refresh_token": "new_refresh_token...",
  "token_type": "bearer"
}
```

**Frontend Implementation:**
```javascript
async function refreshToken() {
  const response = await fetch('/api/v1/auth/refresh', {
    method: 'POST',
    credentials: 'include'
  });
  
  if (response.ok) {
    return true; // New tokens stored in cookies
  }
  
  // If refresh fails, redirect to login
  window.location.href = '/login';
  return false;
}

// Auto-refresh before token expires
setInterval(refreshToken, 14 * 60 * 1000); // Every 14 minutes
```

---

### 1.4 Logout

**Endpoint:** `POST /api/v1/auth/logout`

**Success Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

**Frontend Implementation:**
```javascript
async function logout() {
  await fetch('/api/v1/auth/logout', {
    method: 'POST',
    credentials: 'include'
  });
  
  localStorage.clear();
  window.location.href = '/';
}
```

---

### 1.5 Request Password Reset

**Endpoint:** `POST /api/v1/auth/request-password-reset`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200):**
```json
{
  "message": "Password reset email sent"
}
```

---

### 1.6 Reset Password

**Endpoint:** `POST /api/v1/auth/reset-password`

**Request Body:**
```json
{
  "token": "reset_token_from_email",
  "new_password": "NewSecurePassword123!"
}
```

---

## 2. User Profile

### 📖 User Stories

**US-2.1:** As a user, I want to view my profile to see my personal information.

**US-2.2:** As a user, I want to update my profile information.

**US-2.3:** As a user, I want to manage my active sessions across devices.

---

### 2.1 Get Current User Profile

**Endpoint:** `GET /api/v1/users/me`

**Success Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "phone": "+79001234567",
  "role": "user",
  "account_type": "individual",
  "avatar_url": null,
  "email_verified": true,
  "phone_verified": true,
  "company_name": null,
  "company_description": null,
  "company_logo_url": null,
  "website": null,
  "created_at": "2026-01-30T10:00:00Z"
}
```

**Frontend Implementation:**
```javascript
async function getProfile() {
  const response = await fetch('/api/v1/users/me', {
    credentials: 'include'
  });
  
  if (response.ok) {
    return await response.json();
  }
  throw await response.json();
}
```

---

### 2.2 Update Profile

**Endpoint:** `PATCH /api/v1/users/me`

**Request Body:**
```json
{
  "name": "John Smith",
  "phone": "+79009876543",
  "company_name": "Best Auto Shop",
  "company_description": "Professional car dealer",
  "website": "https://bestautoshop.ru"
}
```

**Success Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Smith",
  "phone": "+79009876543",
  "company_name": "Best Auto Shop"
}
```

---

### 2.3 Change Password

**Endpoint:** `POST /api/v1/users/me/change-password`

**Request Body:**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

**Success Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

---

### 2.4 Get Active Sessions

**Endpoint:** `GET /api/v1/users/me/sessions`

**Success Response (200):**
```json
{
  "sessions": [
    {
      "id": 1,
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
      "ip_address": "192.168.1.1",
      "created_at": "2026-01-30T10:00:00Z",
      "last_activity": "2026-01-30T15:30:00Z",
      "is_current": true
    },
    {
      "id": 2,
      "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)",
      "ip_address": "192.168.1.2",
      "created_at": "2026-01-29T08:00:00Z",
      "last_activity": "2026-01-30T12:00:00Z",
      "is_current": false
    }
  ],
  "total": 2
}
```

**Frontend Implementation:**
```javascript
async function getSessions() {
  const response = await fetch('/api/v1/users/me/sessions', {
    credentials: 'include'
  });
  return await response.json();
}
```

---

### 2.5 Revoke Session

**Endpoint:** `DELETE /api/v1/users/me/sessions/{session_id}`

**Success Response (200):**
```json
{
  "message": "Session revoked successfully"
}
```

---

## 3. Vehicle References (Cascading Selection)

### 📖 User Stories

**US-3.1:** As a user creating an ad, I want to select my vehicle type, then see only relevant brands.

**US-3.2:** As a user, after selecting a brand, I want to see only models from that brand.

**US-3.3:** As a user, I want the system to auto-fill engine specs when I select a modification.

---

### 3.1 Get Vehicle Types

**Endpoint:** `GET /api/v1/vehicles/types`

**Success Response (200):**
```json
[
  {
    "id": 1,
    "name": "Легковые",
    "slug": "passenger",
    "icon": "car",
    "is_active": true,
    "sort_order": 1
  },
  {
    "id": 2,
    "name": "Внедорожники",
    "slug": "suv",
    "icon": "suv",
    "is_active": true,
    "sort_order": 2
  }
]
```

**Frontend Implementation:**
```javascript
async function getVehicleTypes() {
  const response = await fetch('/api/v1/vehicles/types');
  return await response.json();
}

// Usage in React/Vue
useEffect(() => {
  getVehicleTypes().then(types => setVehicleTypes(types));
}, []);
```

---

### 3.2 Get Brands (Filtered by Vehicle Type)

**Endpoint:** `GET /api/v1/vehicles/brands?vehicle_type_id={id}`

**Query Parameters:**
- `vehicle_type_id` (optional) - Filter by vehicle type
- `popular_only` (optional, boolean) - Show only popular brands

**Success Response (200):**
```json
[
  {
    "id": 1,
    "vehicle_type_id": 1,
    "name": "Toyota",
    "slug": "toyota",
    "country": "Japan",
    "logo_url": null,
    "is_popular": true,
    "sort_order": 1
  },
  {
    "id": 2,
    "vehicle_type_id": 1,
    "name": "BMW",
    "slug": "bmw",
    "country": "Germany",
    "is_popular": true,
    "sort_order": 2
  }
]
```

**Frontend Implementation:**
```javascript
async function getBrands(vehicleTypeId = null) {
  const url = vehicleTypeId 
    ? `/api/v1/vehicles/brands?vehicle_type_id=${vehicleTypeId}`
    : '/api/v1/vehicles/brands';
  
  const response = await fetch(url);
  return await response.json();
}

// Cascading select example
const handleVehicleTypeChange = (typeId) => {
  setSelectedVehicleType(typeId);
  getBrands(typeId).then(brands => setBrands(brands));
  // Reset dependent fields
  setModels([]);
  setGenerations([]);
  setModifications([]);
};
```

---

### 3.3 Get Models (Filtered by Brand)

**Endpoint:** `GET /api/v1/vehicles/models?brand_id={id}`

**Query Parameters:**
- `brand_id` (required) - Brand ID
- `popular_only` (optional) - Show only popular models

**Success Response (200):**
```json
[
  {
    "id": 1,
    "brand_id": 1,
    "name": "Camry",
    "slug": "camry",
    "is_popular": true,
    "sort_order": 1
  },
  {
    "id": 2,
    "brand_id": 1,
    "name": "Corolla",
    "slug": "corolla",
    "is_popular": true,
    "sort_order": 2
  }
]
```

**Frontend Implementation:**
```javascript
async function getModels(brandId) {
  const response = await fetch(`/api/v1/vehicles/models?brand_id=${brandId}`);
  return await response.json();
}

const handleBrandChange = (brandId) => {
  setSelectedBrand(brandId);
  getModels(brandId).then(models => setModels(models));
  setGenerations([]);
  setModifications([]);
};
```

---

### 3.4 Get Generations (Filtered by Model)

**Endpoint:** `GET /api/v1/vehicles/generations?model_id={id}`

**Success Response (200):**
```json
[
  {
    "id": 1,
    "model_id": 1,
    "name": "XV70",
    "slug": "xv70",
    "year_start": 2018,
    "year_end": 2024,
    "sort_order": 1
  },
  {
    "id": 2,
    "model_id": 1,
    "name": "XV50",
    "slug": "xv50",
    "year_start": 2012,
    "year_end": 2017,
    "sort_order": 2
  }
]
```

---

### 3.5 Get Modifications (Filtered by Generation)

**Endpoint:** `GET /api/v1/vehicles/modifications?generation_id={id}`

**Success Response (200):**
```json
[
  {
    "id": 1,
    "generation_id": 1,
    "name": "2.5L 181hp AT",
    "slug": "25l-181hp-at",
    "engine_volume": 2.5,
    "engine_power": 181,
    "fuel_type_id": 1,
    "fuel_type_name": "Бензин",
    "transmission_id": 2,
    "transmission_name": "Автомат",
    "drive_type_id": 1,
    "drive_type_name": "Передний",
    "body_type_id": 1,
    "body_type_name": "Седан",
    "doors_count": 4
  }
]
```

**Frontend Implementation:**
```javascript
async function getModifications(generationId) {
  const response = await fetch(
    `/api/v1/vehicles/modifications?generation_id=${generationId}`
  );
  return await response.json();
}

const handleModificationChange = (modificationId) => {
  const modification = modifications.find(m => m.id === modificationId);
  
  // Auto-fill form fields
  setFormData(prev => ({
    ...prev,
    modification_id: modificationId,
    engine_volume: modification.engine_volume,
    engine_power: modification.engine_power,
    fuel_type_id: modification.fuel_type_id,
    transmission_id: modification.transmission_id,
    drive_type_id: modification.drive_type_id,
    body_type_id: modification.body_type_id
  }));
};
```

---

### 3.6 Get All References (One Request)

**Endpoint:** `GET /api/v1/vehicles/references`

**Use Case:** Load all reference data at once for caching

**Success Response (200):**
```json
{
  "vehicle_types": [...],
  "brands": [...],
  "body_types": [...],
  "transmissions": [...],
  "fuel_types": [...],
  "drive_types": [...],
  "colors": [...]
}
```

**Frontend Implementation:**
```javascript
// Cache all references on app initialization
async function initializeVehicleReferences() {
  const response = await fetch('/api/v1/vehicles/references');
  const references = await response.json();
  
  // Store in Redux/Zustand/Context
  localStorage.setItem('vehicle_refs', JSON.stringify(references));
  return references;
}
```

---

### 3.7 Get Body Types

**Endpoint:** `GET /api/v1/vehicles/body-types`

**Success Response (200):**
```json
[
  {
    "id": 1,
    "name": "Седан",
    "slug": "sedan",
    "icon": "sedan"
  },
  {
    "id": 2,
    "name": "Хэтчбек",
    "slug": "hatchback",
    "icon": "hatchback"
  }
]
```

---

### 3.8 Get Transmissions

**Endpoint:** `GET /api/v1/vehicles/transmissions`

**Success Response (200):**
```json
[
  {
    "id": 1,
    "name": "Механическая",
    "short_name": "МТ",
    "slug": "manual"
  },
  {
    "id": 2,
    "name": "Автоматическая",
    "short_name": "АТ",
    "slug": "automatic"
  }
]
```

---

### 3.9 Get Fuel Types

**Endpoint:** `GET /api/v1/vehicles/fuel-types`

**Success Response (200):**
```json
[
  {
    "id": 1,
    "name": "Бензин",
    "slug": "gasoline"
  },
  {
    "id": 2,
    "name": "Дизель",
    "slug": "diesel"
  },
  {
    "id": 3,
    "name": "Электро",
    "slug": "electric"
  }
]
```

---

### 3.10 Get Drive Types

**Endpoint:** `GET /api/v1/vehicles/drive-types`

**Success Response (200):**
```json
[
  {
    "id": 1,
    "name": "Передний",
    "slug": "fwd"
  },
  {
    "id": 2,
    "name": "Задний",
    "slug": "rwd"
  },
  {
    "id": 3,
    "name": "Полный",
    "slug": "awd"
  }
]
```

---

### 3.11 Get Colors

**Endpoint:** `GET /api/v1/vehicles/colors`

**Success Response (200):**
```json
[
  {
    "id": 1,
    "name": "Белый",
    "slug": "white",
    "hex_code": "#FFFFFF"
  },
  {
    "id": 2,
    "name": "Черный",
    "slug": "black",
    "hex_code": "#000000"
  }
]
```

---

## 4. Categories & Locations

### 📖 User Stories

**US-4.1:** As a user, I want to browse ads by category.

**US-4.2:** As a user, I want to filter ads by location.

---

### 4.1 Get Categories

**Endpoint:** `GET /api/v1/categories/`

**Success Response (200):**
```json
[
  {
    "id": 1,
    "name": "Автомобили",
    "slug": "auto",
    "icon": "car",
    "parent_id": null,
    "level": 0,
    "ads_count": 1250
  },
  {
    "id": 2,
    "name": "Грузовики и спецтехника",
    "slug": "trucks",
    "icon": "truck",
    "parent_id": null,
    "level": 0,
    "ads_count": 340
  }
]
```

---

### 4.2 Get Countries

**Endpoint:** `GET /api/v1/locations/countries`

**Success Response (200):**
```json
[
  {
    "id": 1,
    "name": "Россия",
    "code": "RU",
    "flag_emoji": "🇷🇺",
    "phone_code": "+7"
  }
]
```

---

### 4.3 Get Regions

**Endpoint:** `GET /api/v1/locations/regions?country_id={id}`

**Success Response (200):**
```json
[
  {
    "id": 1,
    "country_id": 1,
    "name": "Москва и Московская область",
    "slug": "moscow"
  },
  {
    "id": 2,
    "country_id": 1,
    "name": "Санкт-Петербург и Ленинградская область",
    "slug": "spb"
  }
]
```

---

### 4.4 Get Cities

**Endpoint:** `GET /api/v1/locations/cities?region_id={id}`

**Success Response (200):**
```json
[
  {
    "id": 1,
    "region_id": 1,
    "name": "Москва",
    "slug": "moscow",
    "is_major": true,
    "latitude": 55.7558,
    "longitude": 37.6173
  }
]
```

---

### 4.5 Get Major Cities

**Endpoint:** `GET /api/v1/locations/major-cities`

**Success Response (200):**
```json
[
  {
    "id": 1,
    "name": "Москва",
    "region_name": "Москва и Московская область",
    "latitude": 55.7558,
    "longitude": 37.6173
  }
]
```

---

### 4.6 Search Locations

**Endpoint:** `GET /api/v1/locations/search?q={query}`

**Success Response (200):**
```json
[
  {
    "id": 1,
    "type": "city",
    "name": "Москва",
    "region_name": "Москва и Московская область",
    "full_name": "Москва, Москва и Московская область"
  }
]
```

---

## 5. Advertisements (Ads)

### 📖 User Stories

**US-5.1:** As a user, I want to create an ad to sell my car.

**US-5.2:** As a user, I want to view all my posted ads.

**US-5.3:** As a user, I want to edit my ad before it's sold.

**US-5.4:** As a user, I want to mark my ad as sold.

**US-5.5:** As a user, I want to see how many people viewed my ad.

---

### 5.1 Create Ad

**Endpoint:** `POST /api/v1/ads/`

**Request Body:**
```json
{
  "category_id": 1,
  "vehicle_type_id": 1,
  "brand_id": 1,
  "model_id": 1,
  "generation_id": 1,
  "modification_id": 1,
  "year": 2023,
  "mileage": 15000,
  "body_type_id": 1,
  "transmission_id": 2,
  "fuel_type_id": 1,
  "drive_type_id": 1,
  "color_id": 1,
  "engine_volume": 2.5,
  "engine_power": 181,
  "condition": "used",
  "price": 2500000,
  "currency": "RUB",
  "title": "Toyota Camry 2023 в отличном состоянии",
  "description": "Автомобиль в идеальном состоянии, один владелец...",
  "city_id": 1,
  "contact_name": "Иван",
  "contact_phone": "+79001234567",
  "vin": "JT2BF18E3S0123456",
  "owners_count": 1,
  "pts_type": "original",
  "steering_wheel": "left",
  "features": {
    "leather_interior": true,
    "sunroof": true,
    "parking_sensors": true
  }
}
```

**Success Response (201):**
```json
{
  "id": 1,
  "user_id": 1,
  "status": "pending",
  "title": "Toyota Camry 2023 в отличном состоянии",
  "price": 2500000,
  "currency": "RUB",
  "year": 2023,
  "mileage": 15000,
  "brand_name": "Toyota",
  "model_name": "Camry",
  "city_name": "Москва",
  "created_at": "2026-01-30T10:00:00Z",
  "published_at": null,
  "expires_at": null
}
```

**Frontend Implementation:**
```javascript
async function createAd(adData) {
  const response = await fetch('/api/v1/ads/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(adData)
  });
  
  if (response.ok) {
    const ad = await response.json();
    // Redirect to ad page or my ads
    window.location.href = `/ads/${ad.id}`;
    return ad;
  }
  throw await response.json();
}
```

---

### 5.2 Get My Ads

**Endpoint:** `GET /api/v1/ads/my/ads`

**Query Parameters:**
- `status_filter` (optional) - Filter by status: active, pending, archived, rejected
- `page` (default: 1)
- `page_size` (default: 20)

**Success Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "status": "active",
      "title": "Toyota Camry 2023",
      "price": 2500000,
      "currency": "RUB",
      "year": 2023,
      "mileage": 15000,
      "brand_name": "Toyota",
      "model_name": "Camry",
      "city_name": "Москва",
      "main_image_url": "https://...",
      "views_count": 245,
      "is_featured": false,
      "is_top": false,
      "published_at": "2026-01-25T10:00:00Z",
      "expires_at": "2026-02-25T10:00:00Z",
      "created_at": "2026-01-25T09:30:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

**Frontend Implementation:**
```javascript
async function getMyAds(page = 1, statusFilter = null) {
  let url = `/api/v1/ads/my/ads?page=${page}`;
  if (statusFilter) {
    url += `&status_filter=${statusFilter}`;
  }
  
  const response = await fetch(url, { credentials: 'include' });
  return await response.json();
}

// Usage in component
useEffect(() => {
  getMyAds(currentPage, selectedStatus)
    .then(data => setMyAds(data));
}, [currentPage, selectedStatus]);
```

---

### 5.3 Get Ad Details

**Endpoint:** `GET /api/v1/ads/{ad_id}`

**Success Response (200):**
```json
{
  "id": 1,
  "user_id": 1,
  "status": "active",
  "category_id": 1,
  "vehicle_type_id": 1,
  "brand_id": 1,
  "brand_name": "Toyota",
  "model_id": 1,
  "model_name": "Camry",
  "generation_id": 1,
  "generation_name": "XV70",
  "modification_id": 1,
  "year": 2023,
  "mileage": 15000,
  "body_type_name": "Седан",
  "transmission_name": "Автомат",
  "fuel_type_name": "Бензин",
  "drive_type_name": "Передний",
  "color_name": "Белый",
  "engine_volume": 2.5,
  "engine_power": 181,
  "condition": "used",
  "price": 2500000,
  "currency": "RUB",
  "title": "Toyota Camry 2023 в отличном состоянии",
  "description": "Автомобиль в идеальном состоянии...",
  "city_name": "Москва",
  "region_name": "Москва и Московская область",
  "latitude": 55.7558,
  "longitude": 37.6173,
  "contact_name": "Иван",
  "contact_phone": "+79001234567",
  "vin": "JT2BF18E3S0123456",
  "owners_count": 1,
  "pts_type": "original",
  "features": {
    "leather_interior": true,
    "sunroof": true
  },
  "images": [
    {
      "id": 1,
      "url": "https://storage.example.com/ads/1/image1.jpg",
      "thumbnail_url": "https://storage.example.com/ads/1/thumb1.jpg",
      "sort_order": 0
    }
  ],
  "videos": [],
  "seller": {
    "id": 1,
    "name": "Иван",
    "account_type": "individual",
    "avatar_url": null,
    "ads_count": 5
  },
  "views_count": 245,
  "is_favorite": false,
  "is_in_comparison": false,
  "published_at": "2026-01-25T10:00:00Z",
  "created_at": "2026-01-25T09:30:00Z"
}
```

---

### 5.4 Update Ad

**Endpoint:** `PATCH /api/v1/ads/{ad_id}`

**Request Body:** (partial update, send only changed fields)
```json
{
  "price": 2400000,
  "mileage": 16000,
  "description": "Updated description..."
}
```

**Success Response (200):**
```json
{
  "id": 1,
  "price": 2400000,
  "mileage": 16000,
  "description": "Updated description..."
}
```

---

### 5.5 Delete Ad

**Endpoint:** `DELETE /api/v1/ads/{ad_id}`

**Success Response (200):**
```json
{
  "message": "Ad deleted successfully"
}
```

---

### 5.6 Archive Ad

**Endpoint:** `POST /api/v1/ads/{ad_id}/archive`

**Success Response (200):**
```json
{
  "message": "Ad archived successfully"
}
```

---

### 5.7 Mark Ad as Sold

**Endpoint:** `POST /api/v1/ads/{ad_id}/sold`

**Success Response (200):**
```json
{
  "message": "Ad marked as sold"
}
```

---

### 5.8 Republish Ad

**Endpoint:** `POST /api/v1/ads/{ad_id}/republish`

**Use Case:** Reactivate archived or expired ad

**Success Response (200):**
```json
{
  "message": "Ad republished successfully",
  "expires_at": "2026-03-01T10:00:00Z"
}
```

---

### 5.9 Get Ad Statistics

**Endpoint:** `GET /api/v1/ads/{ad_id}/stats`

**Success Response (200):**
```json
{
  "views_total": 245,
  "views_today": 12,
  "views_week": 87,
  "views_month": 245,
  "favorite_count": 15,
  "messages_count": 8,
  "views_by_date": [
    {
      "date": "2026-01-30",
      "views": 12
    }
  ]
}
```

---

### 5.10 Upload Ad Images

**Endpoint:** `POST /api/v1/ads/{ad_id}/images`

**Request:** `multipart/form-data`
- `file`: Image file (max 10MB)

**Success Response (201):**
```json
{
  "id": 1,
  "ad_id": 1,
  "url": "https://storage.example.com/ads/1/image1.jpg",
  "thumbnail_url": "https://storage.example.com/ads/1/thumb1.jpg",
  "sort_order": 0
}
```

**Frontend Implementation:**
```javascript
async function uploadImage(adId, file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`/api/v1/ads/${adId}/images`, {
    method: 'POST',
    credentials: 'include',
    body: formData
  });
  
  return await response.json();
}

// Multiple file upload
async function uploadMultipleImages(adId, files) {
  const promises = Array.from(files).map(file => 
    uploadImage(adId, file)
  );
  return await Promise.all(promises);
}
```

---

### 5.11 Delete Ad Image

**Endpoint:** `DELETE /api/v1/ads/{ad_id}/images/{image_id}`

**Success Response (200):**
```json
{
  "message": "Image deleted successfully"
}
```

---

## 6. Chat & Messaging

### 📖 User Stories

**US-6.1:** As a user, I want to message the seller about their ad.

**US-6.2:** As a user, I want to see all my conversations in one place.

**US-6.3:** As a user, I want to see unread message notifications.

**US-6.4:** As a user, I want to block a user if they're being inappropriate.

---

### 6.1 Get My Dialogs

**Endpoint:** `GET /api/v1/chat/dialogs`

**Query Parameters:**
- `page` (default: 1)
- `page_size` (default: 20)

**Success Response (200):**
```json
{
  "dialogs": [
    {
      "id": 1,
      "ad_id": 1,
      "ad_title": "Toyota Camry 2023",
      "ad_main_image": "https://...",
      "ad_price": "2500000 RUB",
      "seller_id": 2,
      "buyer_id": 1,
      "other_user": {
        "id": 2,
        "name": "Петр",
        "avatar_url": null,
        "account_type": "individual"
      },
      "last_message_text": "Машина еще актуальна?",
      "last_message_at": "2026-01-30T15:30:00Z",
      "unread_count": 2,
      "is_blocked": false,
      "created_at": "2026-01-30T10:00:00Z"
    }
  ],
  "total": 5,
  "unread_total": 3
}
```

**Frontend Implementation:**
```javascript
async function getDialogs(page = 1) {
  const response = await fetch(
    `/api/v1/chat/dialogs?page=${page}`,
    { credentials: 'include' }
  );
  return await response.json();
}

// Auto-refresh dialogs
useEffect(() => {
  const interval = setInterval(() => {
    getDialogs(currentPage).then(data => setDialogs(data));
  }, 5000); // Refresh every 5 seconds
  
  return () => clearInterval(interval);
}, [currentPage]);
```

---

### 6.2 Create Dialog (Start Conversation)

**Endpoint:** `POST /api/v1/chat/dialogs`

**Request Body:**
```json
{
  "ad_id": 1,
  "initial_message": "Здравствуйте! Машина еще актуальна?"
}
```

**Success Response (201):**
```json
{
  "id": 1,
  "ad_id": 1,
  "ad_title": "Toyota Camry 2023",
  "seller_id": 2,
  "buyer_id": 1,
  "other_user": {
    "id": 2,
    "name": "Петр"
  },
  "last_message_text": "Здравствуйте! Машина еще актуальна?",
  "unread_count": 0,
  "created_at": "2026-01-30T15:30:00Z"
}
```

**Frontend Implementation:**
```javascript
async function startConversation(adId, message) {
  const response = await fetch('/api/v1/chat/dialogs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      ad_id: adId,
      initial_message: message
    })
  });
  
  if (response.ok) {
    const dialog = await response.json();
    // Redirect to chat
    window.location.href = `/messages/${dialog.id}`;
    return dialog;
  }
  throw await response.json();
}
```

---

### 6.3 Get Dialog Messages

**Endpoint:** `GET /api/v1/chat/dialogs/{dialog_id}`

**Success Response (200):**
```json
{
  "id": 1,
  "ad_id": 1,
  "ad_title": "Toyota Camry 2023",
  "seller_id": 2,
  "buyer_id": 1,
  "other_user": {
    "id": 2,
    "name": "Петр",
    "avatar_url": null
  },
  "is_blocked": false,
  "messages": [
    {
      "id": 1,
      "dialog_id": 1,
      "sender_id": 1,
      "sender": {
        "id": 1,
        "name": "Иван"
      },
      "text": "Здравствуйте! Машина еще актуальна?",
      "is_read": true,
      "read_at": "2026-01-30T15:31:00Z",
      "is_delivered": true,
      "created_at": "2026-01-30T15:30:00Z"
    },
    {
      "id": 2,
      "dialog_id": 1,
      "sender_id": 2,
      "sender": {
        "id": 2,
        "name": "Петр"
      },
      "text": "Да, актуальна. Когда можете посмотреть?",
      "is_read": false,
      "is_delivered": true,
      "created_at": "2026-01-30T15:32:00Z"
    }
  ]
}
```

---

### 6.4 Send Message

**Endpoint:** `POST /api/v1/chat/dialogs/{dialog_id}/messages`

**Request Body:**
```json
{
  "text": "Отлично! Завтра в 14:00 подойдет?"
}
```

**Success Response (201):**
```json
{
  "id": 3,
  "dialog_id": 1,
  "sender_id": 1,
  "sender": {
    "id": 1,
    "name": "Иван"
  },
  "text": "Отлично! Завтра в 14:00 подойдет?",
  "is_read": false,
  "is_delivered": true,
  "created_at": "2026-01-30T15:35:00Z"
}
```

**Frontend Implementation:**
```javascript
async function sendMessage(dialogId, text) {
  const response = await fetch(
    `/api/v1/chat/dialogs/${dialogId}/messages`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ text })
    }
  );
  
  if (response.ok) {
    const message = await response.json();
    // Add to messages list
    setMessages(prev => [...prev, message]);
    return message;
  }
  throw await response.json();
}

// Usage in chat component
const handleSendMessage = (e) => {
  e.preventDefault();
  if (messageText.trim()) {
    sendMessage(dialogId, messageText)
      .then(() => setMessageText(''))
      .catch(error => console.error(error));
  }
};
```

---

### 6.5 Mark Dialog as Read

**Endpoint:** `POST /api/v1/chat/dialogs/{dialog_id}/read`

**Success Response (200):**
```json
{
  "message": "Marked 2 messages as read"
}
```

**Frontend Implementation:**
```javascript
// Mark as read when user opens dialog
useEffect(() => {
  if (dialogId) {
    markDialogAsRead(dialogId);
  }
}, [dialogId]);

async function markDialogAsRead(dialogId) {
  await fetch(`/api/v1/chat/dialogs/${dialogId}/read`, {
    method: 'POST',
    credentials: 'include'
  });
}
```

---

### 6.6 Get Unread Count

**Endpoint:** `GET /api/v1/chat/unread-count`

**Success Response (200):**
```json
{
  "unread_count": 5
}
```

**Frontend Implementation:**
```javascript
// Update unread count badge
async function getUnreadCount() {
  const response = await fetch('/api/v1/chat/unread-count', {
    credentials: 'include'
  });
  const data = await response.json();
  return data.unread_count;
}

// Polling for unread count
useEffect(() => {
  const interval = setInterval(() => {
    getUnreadCount().then(count => setUnreadCount(count));
  }, 10000); // Every 10 seconds
  
  return () => clearInterval(interval);
}, []);
```

---

### 6.7 Block User

**Endpoint:** `POST /api/v1/chat/dialogs/{dialog_id}/block`

**Success Response (200):**
```json
{
  "message": "User blocked successfully"
}
```

---

### 6.8 Unblock User

**Endpoint:** `POST /api/v1/chat/dialogs/{dialog_id}/unblock`

**Success Response (200):**
```json
{
  "message": "User unblocked successfully"
}
```

---

### 6.9 Delete Dialog

**Endpoint:** `DELETE /api/v1/chat/dialogs/{dialog_id}`

**Note:** Soft delete - only hides for current user

**Success Response (200):**
```json
{
  "message": "Dialog deleted successfully"
}
```

---

## 7. Favorites & Comparison

### 📖 User Stories

**US-7.1:** As a user, I want to save ads to favorites for later viewing.

**US-7.2:** As a user, I want to compare multiple ads side-by-side.

**US-7.3:** As a user, I want to see my browsing history.

---

### 7.1 Add to Favorites

**Endpoint:** `POST /api/v1/favorites/`

**Request Body:**
```json
{
  "ad_id": 1
}
```

**Success Response (201):**
```json
{
  "message": "Ad added to favorites"
}
```

**Frontend Implementation:**
```javascript
async function addToFavorites(adId) {
  const response = await fetch('/api/v1/favorites/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ ad_id: adId })
  });
  
  if (response.ok) {
    // Update UI
    setIsFavorite(true);
  }
}

// Toggle favorite
const handleFavoriteClick = () => {
  if (isFavorite) {
    removeFromFavorites(adId);
  } else {
    addToFavorites(adId);
  }
};
```

---

### 7.2 Remove from Favorites

**Endpoint:** `DELETE /api/v1/favorites/{ad_id}`

**Success Response (200):**
```json
{
  "message": "Ad removed from favorites"
}
```

---

### 7.3 Get My Favorites

**Endpoint:** `GET /api/v1/favorites/`

**Query Parameters:**
- `page` (default: 1)
- `page_size` (default: 20)

**Success Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Toyota Camry 2023",
      "price": 2500000,
      "currency": "RUB",
      "year": 2023,
      "brand_name": "Toyota",
      "model_name": "Camry",
      "city_name": "Москва",
      "main_image_url": "https://...",
      "added_at": "2026-01-29T10:00:00Z"
    }
  ],
  "total": 8,
  "page": 1,
  "page_size": 20
}
```

---

### 7.4 Add to Comparison

**Endpoint:** `POST /api/v1/favorites/comparison`

**Request Body:**
```json
{
  "ad_id": 1
}
```

**Success Response (201):**
```json
{
  "message": "Ad added to comparison"
}
```

---

### 7.5 Remove from Comparison

**Endpoint:** `DELETE /api/v1/favorites/comparison/{ad_id}`

**Success Response (200):**
```json
{
  "message": "Ad removed from comparison"
}
```

---

### 7.6 Compare Ads

**Endpoint:** `GET /api/v1/favorites/comparison`

**Success Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Toyota Camry 2023",
      "price": 2500000,
      "year": 2023,
      "mileage": 15000,
      "engine_volume": 2.5,
      "engine_power": 181,
      "fuel_type_name": "Бензин",
      "transmission_name": "Автомат",
      "drive_type_name": "Передний",
      "body_type_name": "Седан"
    },
    {
      "id": 2,
      "title": "Honda Accord 2022",
      "price": 2300000,
      "year": 2022,
      "mileage": 25000,
      "engine_volume": 2.0,
      "engine_power": 150,
      "fuel_type_name": "Бензин",
      "transmission_name": "Вариатор",
      "drive_type_name": "Передний",
      "body_type_name": "Седан"
    }
  ],
  "total": 2
}
```

**Frontend Implementation:**
```javascript
// Comparison table component
function ComparisonTable() {
  const [comparison, setComparison] = useState([]);
  
  useEffect(() => {
    fetch('/api/v1/favorites/comparison', { credentials: 'include' })
      .then(res => res.json())
      .then(data => setComparison(data.items));
  }, []);
  
  return (
    <table>
      <thead>
        <tr>
          <th>Характеристика</th>
          {comparison.map(ad => (
            <th key={ad.id}>{ad.title}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Цена</td>
          {comparison.map(ad => (
            <td key={ad.id}>{ad.price.toLocaleString()} ₽</td>
          ))}
        </tr>
        <tr>
          <td>Год</td>
          {comparison.map(ad => (
            <td key={ad.id}>{ad.year}</td>
          ))}
        </tr>
        {/* More rows... */}
      </tbody>
    </table>
  );
}
```

---

### 7.7 Get View History

**Endpoint:** `GET /api/v1/favorites/history`

**Query Parameters:**
- `page` (default: 1)
- `page_size` (default: 20)

**Success Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Toyota Camry 2023",
      "price": 2500000,
      "main_image_url": "https://...",
      "viewed_at": "2026-01-30T15:00:00Z"
    }
  ],
  "total": 25,
  "page": 1
}
```

---

## 8. Search & Filters

### 📖 User Stories

**US-8.1:** As a user, I want to search for cars by keyword.

**US-8.2:** As a user, I want to filter ads by price range, year, and mileage.

**US-8.3:** As a user, I want to see the newest ads first.

---

### 8.1 Search Ads

**Endpoint:** `GET /api/v1/ads/`

**Query Parameters:**
- `q` - Text search (title, description)
- `category_id` - Filter by category
- `vehicle_type_id` - Filter by vehicle type
- `brand_id` - Filter by brand
- `model_id` - Filter by model
- `generation_id` - Filter by generation
- `price_min` - Minimum price
- `price_max` - Maximum price
- `year_min` - Minimum year
- `year_max` - Maximum year
- `mileage_min` - Minimum mileage
- `mileage_max` - Maximum mileage
- `body_type_id` - Filter by body type
- `transmission_id` - Filter by transmission
- `fuel_type_id` - Filter by fuel type
- `drive_type_id` - Filter by drive type
- `color_id` - Filter by color
- `condition` - Filter by condition: new, used
- `city_id` - Filter by city
- `region_id` - Filter by region
- `photos_only` - Show only ads with photos (boolean)
- `dealer_only` - Show only dealer ads (boolean)
- `private_only` - Show only private ads (boolean)
- `vin_only` - Show only ads with VIN (boolean)
- `sort_by` - Sort order: date, price_asc, price_desc, mileage, year
- `page` (default: 1)
- `page_size` (default: 20, max: 100)

**Example Request:**
```
GET /api/v1/ads/?q=camry&brand_id=1&price_min=2000000&price_max=3000000&year_min=2020&sort_by=price_asc&page=1
```

**Success Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Toyota Camry 2023",
      "price": 2500000,
      "currency": "RUB",
      "year": 2023,
      "mileage": 15000,
      "brand_name": "Toyota",
      "model_name": "Camry",
      "generation_name": "XV70",
      "engine_volume": 2.5,
      "engine_power": 181,
      "transmission_name": "Автомат",
      "fuel_type_name": "Бензин",
      "city_name": "Москва",
      "region_name": "Москва и Московская область",
      "main_image_url": "https://...",
      "views_count": 245,
      "is_featured": false,
      "is_top": false,
      "is_urgent": false,
      "is_favorite": false,
      "published_at": "2026-01-25T10:00:00Z",
      "created_at": "2026-01-25T09:30:00Z"
    }
  ],
  "total": 47,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

**Frontend Implementation:**
```javascript
function buildSearchUrl(filters) {
  const params = new URLSearchParams();
  
  Object.keys(filters).forEach(key => {
    if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
      params.append(key, filters[key]);
    }
  });
  
  return `/api/v1/ads/?${params.toString()}`;
}

async function searchAds(filters) {
  const url = buildSearchUrl(filters);
  const response = await fetch(url);
  return await response.json();
}

// Usage in search component
const [filters, setFilters] = useState({
  q: '',
  brand_id: null,
  price_min: null,
  price_max: null,
  year_min: null,
  year_max: null,
  sort_by: 'date',
  page: 1
});

useEffect(() => {
  searchAds(filters).then(data => setSearchResults(data));
}, [filters]);

const handleFilterChange = (key, value) => {
  setFilters(prev => ({
    ...prev,
    [key]: value,
    page: 1 // Reset to first page on filter change
  }));
};
```

---

### 8.2 Advanced Search Example

**Complete Search Form:**
```javascript
function SearchForm() {
  const [filters, setFilters] = useState({
    q: '',
    category_id: null,
    vehicle_type_id: null,
    brand_id: null,
    model_id: null,
    generation_id: null,
    price_min: '',
    price_max: '',
    year_min: '',
    year_max: '',
    mileage_min: '',
    mileage_max: '',
    body_type_id: null,
    transmission_id: null,
    fuel_type_id: null,
    drive_type_id: null,
    city_id: null,
    photos_only: false,
    sort_by: 'date'
  });
  
  const handleSubmit = (e) => {
    e.preventDefault();
    searchAds(filters).then(results => {
      // Display results
    });
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Text search */}
      <input
        type="text"
        placeholder="Поиск по названию..."
        value={filters.q}
        onChange={(e) => setFilters({...filters, q: e.target.value})}
      />
      
      {/* Vehicle Type */}
      <select onChange={(e) => {
        setFilters({
          ...filters,
          vehicle_type_id: e.target.value,
          brand_id: null,
          model_id: null
        });
      }}>
        <option value="">Тип транспорта</option>
        {/* Options from API */}
      </select>
      
      {/* Brand (cascading) */}
      <select
        disabled={!filters.vehicle_type_id}
        onChange={(e) => {
          setFilters({
            ...filters,
            brand_id: e.target.value,
            model_id: null
          });
        }}
      >
        <option value="">Марка</option>
        {/* Options from API filtered by vehicle_type_id */}
      </select>
      
      {/* Price range */}
      <div>
        <input
          type="number"
          placeholder="Цена от"
          value={filters.price_min}
          onChange={(e) => setFilters({...filters, price_min: e.target.value})}
        />
        <input
          type="number"
          placeholder="Цена до"
          value={filters.price_max}
          onChange={(e) => setFilters({...filters, price_max: e.target.value})}
        />
      </div>
      
      {/* Year range */}
      <div>
        <input
          type="number"
          placeholder="Год от"
          value={filters.year_min}
          onChange={(e) => setFilters({...filters, year_min: e.target.value})}
        />
        <input
          type="number"
          placeholder="Год до"
          value={filters.year_max}
          onChange={(e) => setFilters({...filters, year_max: e.target.value})}
        />
      </div>
      
      {/* Checkboxes */}
      <label>
        <input
          type="checkbox"
          checked={filters.photos_only}
          onChange={(e) => setFilters({...filters, photos_only: e.target.checked})}
        />
        Только с фото
      </label>
      
      {/* Sort */}
      <select
        value={filters.sort_by}
        onChange={(e) => setFilters({...filters, sort_by: e.target.value})}
      >
        <option value="date">По дате</option>
        <option value="price_asc">По цене (возр.)</option>
        <option value="price_desc">По цене (убыв.)</option>
        <option value="year">По году</option>
        <option value="mileage">По пробегу</option>
      </select>
      
      <button type="submit">Найти</button>
    </form>
  );
}
```

---

## 9. WebSocket Integration

### 📖 User Stories

**US-9.1:** As a user, I want to receive messages in real-time without refreshing.

**US-9.2:** As a user, I want to see when the other person is typing.

---

### 9.1 WebSocket Connection

**Endpoint:** `ws://localhost:8000/ws/{user_id}`

**Authentication:** Send access token as query parameter or in first message

**Connection Example:**
```javascript
class ChatWebSocket {
  constructor(userId, accessToken) {
    this.userId = userId;
    this.accessToken = accessToken;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }
  
  connect() {
    const wsUrl = `ws://localhost:8000/ws/${this.userId}?token=${this.accessToken}`;
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      
      // Send ping every 30 seconds to keep connection alive
      this.pingInterval = setInterval(() => {
        this.send({ type: 'ping' });
      }, 30000);
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket closed');
      clearInterval(this.pingInterval);
      this.reconnect();
    };
  }
  
  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      
      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      setTimeout(() => this.connect(), delay);
    }
  }
  
  handleMessage(data) {
    switch (data.type) {
      case 'message':
        // New message received
        this.onNewMessage(data.message);
        break;
      
      case 'message_read':
        // Message was read
        this.onMessageRead(data.message_id);
        break;
      
      case 'user_online':
        // User came online
        this.onUserOnline(data.user_id);
        break;
      
      case 'user_offline':
        // User went offline
        this.onUserOffline(data.user_id);
        break;
      
      case 'typing':
        // User is typing
        this.onUserTyping(data.user_id, data.dialog_id);
        break;
      
      case 'pong':
        // Ping response
        break;
      
      default:
        console.log('Unknown message type:', data.type);
    }
  }
  
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
  
  sendMessage(dialogId, text) {
    this.send({
      type: 'message',
      dialog_id: dialogId,
      text: text
    });
  }
  
  sendTyping(dialogId) {
    this.send({
      type: 'typing',
      dialog_id: dialogId
    });
  }
  
  markAsRead(dialogId, messageId) {
    this.send({
      type: 'read',
      dialog_id: dialogId,
      message_id: messageId
    });
  }
  
  disconnect() {
    if (this.ws) {
      clearInterval(this.pingInterval);
      this.ws.close();
    }
  }
  
  // Callbacks (override in implementation)
  onNewMessage(message) {
    console.log('New message:', message);
  }
  
  onMessageRead(messageId) {
    console.log('Message read:', messageId);
  }
  
  onUserOnline(userId) {
    console.log('User online:', userId);
  }
  
  onUserOffline(userId) {
    console.log('User offline:', userId);
  }
  
  onUserTyping(userId, dialogId) {
    console.log('User typing:', userId, dialogId);
  }
}

// Usage in React
function ChatComponent({ currentUser, dialogId }) {
  const [ws, setWs] = useState(null);
  const [messages, setMessages] = useState([]);
  
  useEffect(() => {
    // Get access token from cookie or storage
    const accessToken = getAccessToken();
    
    const chatWs = new ChatWebSocket(currentUser.id, accessToken);
    
    chatWs.onNewMessage = (message) => {
      if (message.dialog_id === dialogId) {
        setMessages(prev => [...prev, message]);
        
        // Mark as read if dialog is open
        chatWs.markAsRead(dialogId, message.id);
      }
    };
    
    chatWs.connect();
    setWs(chatWs);
    
    return () => {
      chatWs.disconnect();
    };
  }, [currentUser.id, dialogId]);
  
  const handleSendMessage = (text) => {
    if (ws) {
      ws.sendMessage(dialogId, text);
    }
  };
  
  return (
    <div>
      {/* Chat UI */}
    </div>
  );
}
```

---

## 🔧 Error Handling

### Standard Error Response

All error responses follow this format:

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "details": {
    "field": "email",
    "error": "Invalid email format"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Invalid request data |
| `UNAUTHORIZED` | 401 | Not authenticated |
| `FORBIDDEN` | 403 | No permission |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists |
| `INTERNAL_ERROR` | 500 | Server error |

### Frontend Error Handling

```javascript
async function apiRequest(url, options = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      
      // Handle specific errors
      if (response.status === 401) {
        // Try to refresh token
        const refreshed = await refreshToken();
        if (refreshed) {
          // Retry original request
          return apiRequest(url, options);
        } else {
          // Redirect to login
          window.location.href = '/login';
        }
      }
      
      throw error;
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
```

---

## 📱 Mobile-Friendly Considerations

### Pagination

Always implement infinite scroll or "Load More" for mobile:

```javascript
function AdsList() {
  const [ads, setAds] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  
  const loadMore = async () => {
    if (loading || !hasMore) return;
    
    setLoading(true);
    const data = await searchAds({ ...filters, page });
    
    setAds(prev => [...prev, ...data.items]);
    setPage(prev => prev + 1);
    setHasMore(data.page < data.pages);
    setLoading(false);
  };
  
  // Infinite scroll
  useEffect(() => {
    const handleScroll = () => {
      if (
        window.innerHeight + window.scrollY >= document.body.offsetHeight - 500 &&
        !loading &&
        hasMore
      ) {
        loadMore();
      }
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [loading, hasMore]);
  
  return (
    <div>
      {ads.map(ad => <AdCard key={ad.id} ad={ad} />)}
      {loading && <Spinner />}
      {!hasMore && <p>No more ads</p>}
    </div>
  );
}
```

---

## 🎨 UI/UX Best Practices

### Loading States

Always show loading indicators:

```javascript
function AdDetails({ adId }) {
  const [ad, setAd] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    fetch(`/api/v1/ads/${adId}`)
      .then(res => res.json())
      .then(data => {
        setAd(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, [adId]);
  
  if (loading) return <Skeleton />;
  if (error) return <ErrorMessage error={error} />;
  if (!ad) return <NotFound />;
  
  return <AdView ad={ad} />;
}
```

### Optimistic Updates

Update UI immediately, rollback on error:

```javascript
async function toggleFavorite(adId) {
  // Optimistic update
  setIsFavorite(true);
  
  try {
    await addToFavorites(adId);
  } catch (error) {
    // Rollback on error
    setIsFavorite(false);
    showErrorToast('Failed to add to favorites');
  }
}
```

---

## 📝 Complete Flow Examples

### Example 1: Creating an Ad

```javascript
async function createAdFlow() {
  // Step 1: Load references
  const references = await fetch('/api/v1/vehicles/references')
    .then(r => r.json());
  
  // Step 2: User fills form with cascading selects
  const formData = {
    category_id: 1,
    vehicle_type_id: 1,  // Легковые
    brand_id: 1,          // User selects Toyota
    model_id: 5,          // User selects Camry (from filtered models)
    generation_id: 2,     // User selects XV70 (from filtered gens)
    modification_id: 10,  // User selects 2.5L 181hp (auto-fills specs)
    year: 2023,
    mileage: 15000,
    price: 2500000,
    currency: 'RUB',
    title: 'Toyota Camry 2023',
    description: '...',
    city_id: 1,
    contact_phone: '+79001234567'
  };
  
  // Step 3: Create ad
  const ad = await fetch('/api/v1/ads/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(formData)
  }).then(r => r.json());
  
  // Step 4: Upload images
  for (const file of selectedFiles) {
    await uploadImage(ad.id, file);
  }
  
  // Step 5: Redirect to ad page
  window.location.href = `/ads/${ad.id}`;
}
```

### Example 2: Messaging a Seller

```javascript
async function messageSellerFlow(adId) {
  // Step 1: Check if user is logged in
  const user = getCurrentUser();
  if (!user) {
    return redirectToLogin();
  }
  
  // Step 2: Create or get dialog
  const dialog = await fetch('/api/v1/chat/dialogs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      ad_id: adId,
      initial_message: 'Здравствуйте! Интересует это объявление.'
    })
  }).then(r => r.json());
  
  // Step 3: Open chat
  window.location.href = `/messages/${dialog.id}`;
  
  // Step 4: Connect WebSocket for real-time updates
  const ws = new ChatWebSocket(user.id, getAccessToken());
  ws.connect();
}
```

---

## 🚀 Performance Optimization Tips

### 1. Cache Reference Data

```javascript
// Cache vehicle references in localStorage
const CACHE_KEY = 'vehicle_references';
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

async function getVehicleReferences() {
  const cached = localStorage.getItem(CACHE_KEY);
  if (cached) {
    const { data, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp < CACHE_DURATION) {
      return data;
    }
  }
  
  const data = await fetch('/api/v1/vehicles/references').then(r => r.json());
  localStorage.setItem(CACHE_KEY, JSON.stringify({
    data,
    timestamp: Date.now()
  }));
  
  return data;
}
```

### 2. Debounce Search Input

```javascript
import { debounce } from 'lodash';

const debouncedSearch = debounce((query) => {
  searchAds({ q: query }).then(results => setResults(results));
}, 500);

<input
  onChange={(e) => debouncedSearch(e.target.value)}
  placeholder="Поиск..."
/>
```

### 3. Image Lazy Loading

```javascript
<img
  src={ad.main_image_url}
  loading="lazy"
  alt={ad.title}
/>
```

---

## 📄 Summary

This guide covers all user-facing features of AVTO LAIF API:

- ✅ Complete authentication flow
- ✅ User profile management
- ✅ Cascading vehicle selection system
- ✅ Ad creation, editing, and management
- ✅ Real-time chat with WebSocket
- ✅ Advanced search and filters
- ✅ Favorites and comparison
- ✅ Location-based filtering

All endpoints are tested and ready for frontend integration! 🚀

