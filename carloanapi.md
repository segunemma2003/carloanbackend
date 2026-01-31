# 🚗 MillionAvto (AVTO LAIF) - Complete API Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Getting Started](#getting-started)
4. [Authentication](#authentication)
5. [API Endpoints](#api-endpoints)
6. [Admin Panel](#admin-panel)
7. [WebSocket Real-Time Chat](#websocket-real-time-chat)
8. [Search & Filters](#search--filters)
9. [Database Models](#database-models)
10. [Deployment](#deployment)

---

## 📖 Project Overview

**MillionAvto** (AVTO LAIF) is a comprehensive car marketplace platform built with FastAPI. It supports:
- Car, truck, motorcycle, boat, and rental listings
- Advanced search with 20+ filters
- Real-time WebSocket chat
- User authentication with JWT
- Admin panel for content management
- Geolocation and radius search
- Moderation system

**Platform:** Web (desktop + mobile adaptive), future mobile apps

---

## 🛠️ Technology Stack

```
Backend Framework: FastAPI 0.115.6
Database: PostgreSQL (asyncpg)
ORM: SQLAlchemy 2.0.36 (async)
Caching: Redis 5.2.1
Authentication: JWT (Access + Refresh tokens)
Real-time: WebSocket 14.1
Validation: Pydantic 2.10.4
Admin Panel: SQLAdmin 0.20.0
Migrations: Alembic
Password Hashing: bcrypt 5.0.0
```

---

## 🚀 Getting Started

### Prerequisites
```bash
Python 3.11+
PostgreSQL 14+
Redis 7+ (optional)
```

### Installation
```bash
# Clone repository
git clone <repository-url>
cd carloanbackend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Seed initial data
python -m scripts.seed_data

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Points
- **API Documentation:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Admin Panel:** http://localhost:8000/admin
- **Health Check:** http://localhost:8000/health

---

## 🔐 Authentication

### Registration & Login
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "phone": "+79001234567"
}
```

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "USER"
  }
}
```

**Tokens stored as HttpOnly cookies:**
- `access_token` (15 minutes)
- `refresh_token` (7 days, rotating)

### Token Refresh
```http
POST /api/v1/auth/refresh
```

### Password Reset
```http
POST /api/v1/auth/request-password-reset
Content-Type: application/json

{
  "email": "user@example.com"
}
```

```http
POST /api/v1/auth/reset-password
Content-Type: application/json

{
  "token": "reset_token_from_email",
  "new_password": "NewSecurePass123!"
}
```

---

## 📡 API Endpoints

### **1. Authentication** (`/api/v1/auth`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/register` | Register new user | No |
| POST | `/login` | Login user | No |
| POST | `/logout` | Logout user | Yes |
| POST | `/refresh` | Refresh access token | Yes |
| POST | `/verify-email` | Verify email address | Yes |
| POST | `/request-password-reset` | Request password reset | No |
| POST | `/reset-password` | Reset password with token | No |

### **2. User Management** (`/api/v1/users`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/me` | Get current user profile | Yes |
| PUT | `/me` | Update user profile | Yes |
| DELETE | `/me` | Delete user account | Yes |
| PUT | `/me/password` | Change password | Yes |
| GET | `/me/sessions` | List active sessions | Yes |
| DELETE | `/me/sessions/{id}` | Revoke specific session | Yes |
| DELETE | `/me/sessions/all` | Revoke all sessions | Yes |

### **3. Categories** (`/api/v1/categories`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | List all categories | No |
| GET | `/{id}` | Get single category | No |
| POST | `/` | Create category (Admin) | Yes (Admin) |
| PUT | `/{id}` | Update category (Admin) | Yes (Admin) |
| DELETE | `/{id}` | Delete category (Admin) | Yes (Admin) |

**Categories Available:**
- Автомобили (Cars)
- Грузовики и спецтехника (Trucks & Special Equipment)
- Мотоциклы (Motorcycles)
- Лодки и катера (Boats & Watercraft)
- Аренда (Rental)
- Авто на заказ (Import Cars)
- Самоделки (DIY/Custom Vehicles)

### **4. Vehicle References** (`/api/v1/vehicles`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/types` | List vehicle types | No |
| GET | `/brands` | List brands (filter by type) | No |
| GET | `/models` | List models (filter by brand) | No |
| GET | `/generations` | List generations (filter by model) | No |
| GET | `/modifications` | List modifications (filter by generation) | No |
| GET | `/body-types` | List body types | No |
| GET | `/transmissions` | List transmission types | No |
| GET | `/fuel-types` | List fuel types | No |
| GET | `/drive-types` | List drive types | No |
| GET | `/colors` | List available colors | No |

**Example: Cascading Selection**
```http
GET /api/v1/vehicles/brands?vehicle_type_id=1
GET /api/v1/vehicles/models?brand_id=5
GET /api/v1/vehicles/generations?model_id=25
GET /api/v1/vehicles/modifications?generation_id=100
```

### **5. Locations** (`/api/v1/locations`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/countries` | List countries | No |
| GET | `/regions` | List regions (filter by country) | No |
| GET | `/cities` | List cities (filter by region) | No |
| GET | `/detect` | Detect location by IP | No |
| GET | `/nearby` | Find nearby cities (radius) | No |
| GET | `/major-cities` | List major cities | No |

**Example: Radius Search**
```http
GET /api/v1/locations/nearby?lat=56.13&lon=40.41&radius_km=100
```

### **6. Advertisements** (`/api/v1/ads`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | List ads (with filters & search) | No |
| GET | `/{id}` | Get single ad details | No |
| POST | `/` | Create new ad | Yes |
| PUT | `/{id}` | Update ad | Yes (Owner) |
| DELETE | `/{id}` | Delete ad | Yes (Owner) |
| GET | `/my/ads` | List my ads (with status filter) | Yes |
| POST | `/{id}/view` | Track ad view | No |
| POST | `/{id}/upload-image` | Upload ad image | Yes (Owner) |
| POST | `/{id}/upload-video` | Upload ad video | Yes (Owner) |

**Ad Status Options:**
- `draft` - Not published yet
- `pending` - Awaiting moderation
- `active` - Live and visible
- `rejected` - Rejected by moderator
- `archived` - Archived by owner
- `expired` - Expired listing

### **7. Chat** (`/api/v1/chat`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/dialogs` | List all dialogs | Yes |
| GET | `/dialogs/{id}` | Get dialog details | Yes |
| POST | `/dialogs` | Create new dialog | Yes |
| GET | `/dialogs/{id}/messages` | Get messages in dialog | Yes |
| POST | `/dialogs/{id}/messages` | Send message | Yes |
| PUT | `/dialogs/{id}/messages/{msg_id}/read` | Mark message as read | Yes |
| POST | `/dialogs/{id}/block` | Block user in dialog | Yes |
| POST | `/dialogs/{id}/unblock` | Unblock user | Yes |

**WebSocket Endpoints:**
```
WS /ws/chat - Real-time chat
WS /ws/status - Online/offline status
```

### **8. Favorites & Comparison** (`/api/v1/favorites`, `/api/v1/comparison`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/favorites/` | Add to favorites | Yes |
| GET | `/favorites/` | List favorites | Yes |
| DELETE | `/favorites/{ad_id}` | Remove from favorites | Yes |
| POST | `/comparison/` | Add to comparison | Yes |
| GET | `/comparison/` | List comparison items | Yes |
| DELETE | `/comparison/{ad_id}` | Remove from comparison | Yes |
| GET | `/history/` | View browsing history | Yes |

### **9. Moderation** (`/api/v1/moderation`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/reports` | List all reports | Yes (Moderator) |
| POST | `/reports` | Create report | Yes |
| PUT | `/reports/{id}` | Update report status | Yes (Moderator) |
| POST | `/ads/{id}/moderate` | Moderate ad (approve/reject) | Yes (Moderator) |
| GET | `/logs` | View moderation logs | Yes (Moderator) |
| GET | `/stats` | Moderation statistics | Yes (Moderator) |

**Report Types:**
- `ad` - Report advertisement
- `user` - Report user
- `message` - Report chat message

**Report Reasons:**
- `fraud` - Fraudulent listing
- `spam` - Spam content
- `inappropriate` - Inappropriate content
- `duplicate` - Duplicate listing
- `wrong_category` - Wrong category
- `other` - Other reason

### **10. Banners** (`/api/v1/banners`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | List active banners | No |
| GET | `/{id}` | Get banner details | No |
| POST | `/` | Create banner (Admin) | Yes (Admin) |
| PUT | `/{id}` | Update banner (Admin) | Yes (Admin) |
| DELETE | `/{id}` | Delete banner (Admin) | Yes (Admin) |

**Banner Locations:**
- `home_top` - Home page top
- `home_middle` - Home page middle
- `category_top` - Category page top
- `ad_detail_sidebar` - Ad detail sidebar

---

## 🔍 Search & Filters

### Complete Search API
```http
GET /api/v1/ads/?q=BMW&category_id=1&brand_ids=5,10&price_from=500000&price_to=1500000&year_from=2020&sort_by=price_asc&page=1&size=20
```

### Available Filters

#### **Basic Filters:**
- `q` - Text search (title, description)
- `category_id` - Category filter
- `city_id` - City filter
- `region_id` - Region filter
- `country_id` - Country filter

#### **Vehicle Specifications:**
- `brand_ids` - Brand IDs (comma-separated)
- `model_ids` - Model IDs (comma-separated)
- `generation_ids` - Generation IDs
- `modification_ids` - Modification IDs
- `body_type_ids` - Body type IDs
- `transmission_ids` - Transmission IDs
- `fuel_type_ids` - Fuel type IDs
- `drive_type_ids` - Drive type IDs
- `color_ids` - Color IDs

#### **Price & Year:**
- `price_from` - Minimum price
- `price_to` - Maximum price
- `year_from` - Minimum year
- `year_to` - Maximum year

#### **Mileage & Engine:**
- `mileage_from` - Minimum mileage (km)
- `mileage_to` - Maximum mileage (km)
- `engine_volume_from` - Min engine volume (L)
- `engine_volume_to` - Max engine volume (L)
- `engine_power_from` - Min power (hp)
- `engine_power_to` - Max power (hp)

#### **Condition & Features:**
- `condition` - `new` or `used`
- `has_images` - `true` (only with photos)
- `has_vin` - `true` (only with VIN)
- `from_dealers` - `true` (only from dealers)

#### **Location & Radius:**
- `latitude` - Center latitude
- `longitude` - Center longitude
- `radius_km` - Radius in kilometers (50, 100, 200, 500, 1000)

#### **Sorting:**
- `sort_by` - Sort option:
  - `created_desc` - Newest first (default)
  - `created_asc` - Oldest first
  - `price_asc` - Price: Low to High
  - `price_desc` - Price: High to Low
  - `mileage_asc` - Mileage: Low to High
  - `mileage_desc` - Mileage: High to Low
  - `year_asc` - Year: Oldest first
  - `year_desc` - Year: Newest first

#### **Pagination:**
- `page` - Page number (default: 1)
- `size` - Items per page (default: 20, max: 100)

---

## 🎛️ Admin Panel

### Access
**URL:** http://localhost:8000/admin  
**Credentials:**
- Email: `admin@avtolaif.ru`
- Password: `admin123`

### Features
✅ **User Management** - View, edit, activate/deactivate users  
✅ **User Sessions** - Monitor and revoke user sessions  
✅ **Categories** - Manage categories with SEO fields  
✅ **Vehicle References** - Manage brands, models, generations, etc.  
✅ **Locations** - Manage countries, regions, cities  
✅ **Advertisements** - Approve, reject, delete ads  
✅ **Ad Media** - Manage images and videos  
✅ **Chat Monitoring** - View dialogs and messages  
✅ **Reports** - Handle user reports  
✅ **Moderation Logs** - Track all moderation actions  
✅ **Banners** - Create and manage promotional banners  

### Admin Roles
- **Administrator** - Full access to all features
- **Moderator** - Can moderate ads and handle reports
- **Dealer** - Can create multiple ads and have company profile

---

## 💬 WebSocket Real-Time Chat

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onopen = () => {
  // Send authentication
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your_jwt_access_token'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### Message Types

**Send Message:**
```json
{
  "type": "message",
  "dialog_id": 123,
  "content": "Hello! Is this car still available?"
}
```

**Receive Message:**
```json
{
  "type": "message",
  "dialog_id": 123,
  "message_id": 456,
  "sender_id": 789,
  "content": "Yes, it's available!",
  "created_at": "2026-01-31T12:00:00Z",
  "is_read": false
}
```

**Typing Indicator:**
```json
{
  "type": "typing",
  "dialog_id": 123,
  "user_id": 789
}
```

**Read Receipt:**
```json
{
  "type": "read",
  "dialog_id": 123,
  "message_id": 456
}
```

**Online Status:**
```json
{
  "type": "status",
  "user_id": 789,
  "status": "online"
}
```

---

## 🗄️ Database Models

### Core Models
- **User** - User accounts with roles
- **UserSession** - Active user sessions
- **Category** - Ad categories with SEO
- **Ad** - Advertisement listings
- **AdImage** - Ad photos
- **AdVideo** - Ad videos

### Vehicle References
- **VehicleType** - Car, Truck, Motorcycle, etc.
- **Brand** - Vehicle brands (200+)
- **Model** - Vehicle models
- **Generation** - Model generations
- **Modification** - Engine/spec modifications
- **BodyType** - Sedan, SUV, etc.
- **Transmission** - Manual, Automatic, etc.
- **FuelType** - Gasoline, Diesel, Electric, etc.
- **DriveType** - FWD, RWD, AWD, 4WD
- **Color** - Available colors

### Location Models
- **Country** - Countries
- **Region** - States/Provinces
- **City** - Cities with coordinates

### Chat Models
- **Dialog** - Chat conversations
- **Message** - Chat messages
- **MessageAttachment** - File attachments

### User Interaction Models
- **Favorite** - Saved ads
- **Comparison** - Compare ads
- **ViewHistory** - Browsing history

### Moderation Models
- **Report** - User reports
- **ModerationLog** - Moderation actions

### Marketing Models
- **Banner** - Promotional banners

---

## 🚀 Deployment

### Environment Variables
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/avtolaif

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=*

# App
APP_NAME=MillionAvto
DEBUG=false
```

### Production Checklist
✅ Set `DEBUG=false`  
✅ Use strong `SECRET_KEY`  
✅ Configure proper `CORS_ORIGINS`  
✅ Enable HTTPS  
✅ Set up PostgreSQL backups  
✅ Configure Redis for caching  
✅ Set up logging  
✅ Configure file storage (S3/CDN)  
✅ Set up monitoring (Sentry, etc.)  

---

## 📊 API Statistics

- **Total Endpoints:** 80+
- **Admin Views:** 27
- **Search Filters:** 20+
- **Sorting Options:** 8
- **Vehicle Brands:** 200+
- **Categories:** 7 main + subcategories

---

## 🎨 Branding

**Logo:** `/static/logo.png` (MillionAvto)  
**Primary Color:** `#5B87F5` (Blue)  
**CTA Color:** `#DC2626` (Red)  
**Success Color:** `#10B981` (Green)

---

## 📞 Support

For questions or issues, please contact the development team.

**© 2025 MillionAvto (AVTO LAIF)**

