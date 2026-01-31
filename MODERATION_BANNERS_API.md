# Moderation & Banners API Documentation

Complete API documentation for user-facing Moderation and Banners endpoints.

**Base URL:** `/api/v1`

**Authentication:** Most endpoints require authentication via JWT token in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

---

## 📋 Table of Contents

1. [Moderation API](#moderation-api)
   - [Submit Reports](#submit-reports)
   - [View My Reports](#view-my-reports)
2. [Banners API](#banners-api)
   - [Get Banners](#get-banners)
   - [Track Banner Events](#track-banner-events)

---

## 🛡️ Moderation API

Base path: `/api/v1/moderation`

### Submit Reports

Users can report inappropriate content including ads, users, and messages.

#### Report an Advertisement

**Endpoint:** `POST /moderation/reports/ad/{ad_id}`

**Authentication:** Required

**Path Parameters:**
- `ad_id` (integer, required) - ID of the advertisement to report

**Query Parameters:**
- `reason` (enum, required) - Reason for reporting
  - Values: `fraud`, `spam`, `inappropriate`, `wrong_category`, `wrong_price`, `duplicate`, `sold`, `other`
- `description` (string, optional) - Additional details about the report

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/moderation/reports/ad/123?reason=fraud&description=Suspicious%20pricing" \
  -H "Authorization: Bearer <access_token>"
```

**Response:**
```json
{
  "message": "Report submitted successfully"
}
```

**Status Codes:**
- `201 Created` - Report submitted successfully
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Ad not found
- `422 Unprocessable Entity` - Invalid reason or missing parameters

---

#### Report a User

**Endpoint:** `POST /moderation/reports/user/{user_id}`

**Authentication:** Required

**Path Parameters:**
- `user_id` (integer, required) - ID of the user to report

**Query Parameters:**
- `reason` (enum, required) - Reason for reporting
  - Values: `fraud`, `spam`, `inappropriate`, `wrong_category`, `wrong_price`, `duplicate`, `sold`, `other`
- `description` (string, optional) - Additional details about the report

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/moderation/reports/user/456?reason=spam&description=Posting%20fake%20ads" \
  -H "Authorization: Bearer <access_token>"
```

**Response:**
```json
{
  "message": "Report submitted successfully"
}
```

**Status Codes:**
- `201 Created` - Report submitted successfully
- `401 Unauthorized` - Authentication required
- `404 Not Found` - User not found
- `422 Unprocessable Entity` - Invalid reason, cannot report yourself, or missing parameters

**Error Example:**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Cannot report yourself",
  "details": {}
}
```

---

#### Report a Chat Message

**Endpoint:** `POST /moderation/reports/message/{message_id}`

**Authentication:** Required

**Path Parameters:**
- `message_id` (integer, required) - ID of the message to report

**Query Parameters:**
- `reason` (enum, required) - Reason for reporting
  - Values: `fraud`, `spam`, `inappropriate`, `wrong_category`, `wrong_price`, `duplicate`, `sold`, `other`
- `description` (string, optional) - Additional details about the report

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/moderation/reports/message/789?reason=inappropriate&description=Offensive%20language" \
  -H "Authorization: Bearer <access_token>"
```

**Response:**
```json
{
  "message": "Report submitted successfully"
}
```

**Status Codes:**
- `201 Created` - Report submitted successfully
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Message not found or user is not a participant in the dialog
- `422 Unprocessable Entity` - Invalid reason or missing parameters

---

### View My Reports

Users can view their own submitted reports and check their status.

#### Get My Reports (List)

**Endpoint:** `GET /moderation/reports/my`

**Authentication:** Required

**Query Parameters:**
- `page` (integer, optional, default: 1) - Page number (minimum: 1)
- `page_size` (integer, optional, default: 20) - Items per page (minimum: 1, maximum: 100)

**Request Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/moderation/reports/my?page=1&page_size=20" \
  -H "Authorization: Bearer <access_token>"
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "report_type": "ad",
      "target_id": 123,
      "reason": "fraud",
      "description": "Suspicious pricing",
      "status": "pending",
      "resolved_at": null,
      "resolution_note": null,
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "report_type": "user",
      "target_id": 456,
      "reason": "spam",
      "description": "Posting fake ads",
      "status": "resolved",
      "resolved_at": "2024-01-16T14:20:00Z",
      "resolution_note": "User warned",
      "created_at": "2024-01-15T11:00:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20
}
```

**Response Fields:**
- `items` (array) - List of reports
  - `id` (integer) - Report ID
  - `report_type` (string) - Type of report: `ad`, `user`, or `message`
  - `target_id` (integer) - ID of the reported item
  - `reason` (string) - Reason for the report
  - `description` (string, nullable) - Additional details
  - `status` (string) - Report status: `pending`, `reviewing`, `resolved`, `dismissed`
  - `resolved_at` (string, nullable) - ISO 8601 timestamp when report was resolved
  - `resolution_note` (string, nullable) - Moderator's note about resolution
  - `created_at` (string) - ISO 8601 timestamp when report was created
- `total` (integer) - Total number of reports
- `page` (integer) - Current page number
- `page_size` (integer) - Items per page

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Authentication required

---

#### Get My Report Details

**Endpoint:** `GET /moderation/reports/my/{report_id}`

**Authentication:** Required

**Path Parameters:**
- `report_id` (integer, required) - ID of the report

**Request Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/moderation/reports/my/1" \
  -H "Authorization: Bearer <access_token>"
```

**Response:**
```json
{
  "id": 1,
  "report_type": "ad",
  "target_id": 123,
  "reason": "fraud",
  "description": "Suspicious pricing",
  "status": "pending",
  "resolved_by": null,
  "resolved_at": null,
  "resolution_note": null,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Response Fields:**
- `id` (integer) - Report ID
- `report_type` (string) - Type of report: `ad`, `user`, or `message`
- `target_id` (integer) - ID of the reported item
- `reason` (string) - Reason for the report
- `description` (string, nullable) - Additional details
- `status` (string) - Report status: `pending`, `reviewing`, `resolved`, `dismissed`
- `resolved_by` (integer, nullable) - ID of moderator who resolved the report
- `resolved_at` (string, nullable) - ISO 8601 timestamp when report was resolved
- `resolution_note` (string, nullable) - Moderator's note about resolution
- `created_at` (string) - ISO 8601 timestamp when report was created

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Report not found or doesn't belong to current user

---

### Report Types

- `ad` - Report an advertisement
- `user` - Report a user
- `message` - Report a chat message

### Report Reasons

- `fraud` - Fraudulent listing or activity
- `spam` - Spam content
- `inappropriate` - Inappropriate content
- `wrong_category` - Wrong category
- `wrong_price` - Incorrect pricing
- `duplicate` - Duplicate listing
- `sold` - Item already sold
- `other` - Other reason

### Report Status

- `pending` - Report is pending review
- `reviewing` - Report is being reviewed by moderator
- `resolved` - Report has been resolved
- `dismissed` - Report was dismissed

---

## 🎯 Banners API

Base path: `/api/v1/banners`

### Get Banners

#### List Active Banners

**Endpoint:** `GET /banners/`

**Authentication:** Not required (public endpoint)

**Query Parameters:**
- `banner_type` (enum, optional) - Filter by banner type
  - Values: `sidebar`, `top`, `middle`, `bottom`
- `page` (string, optional) - Target page for filtering (future use)

**Request Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/banners/?banner_type=sidebar"
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Special Offer",
      "description": "Get 20% off on premium listings",
      "banner_type": "sidebar",
      "image_url": "https://example.com/banner1.jpg",
      "link_url": "https://example.com/offer",
      "status": "active",
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2024-12-31T23:59:59Z",
      "sort_order": 10,
      "target_pages": null,
      "impressions": 1250,
      "clicks": 45,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-15T14:30:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": null
}
```

**Response Fields:**
- `items` (array) - List of active banners
  - `id` (integer) - Banner ID
  - `title` (string) - Banner title
  - `description` (string, nullable) - Banner description
  - `banner_type` (string) - Banner type: `sidebar`, `top`, `middle`, `bottom`
  - `image_url` (string) - URL to banner image
  - `link_url` (string, nullable) - URL to navigate when banner is clicked
  - `status` (string) - Banner status: `active`, `paused`, `expired`, `draft`
  - `start_date` (string, nullable) - ISO 8601 timestamp when banner becomes active
  - `end_date` (string, nullable) - ISO 8601 timestamp when banner expires
  - `sort_order` (integer) - Display priority (higher = shown first)
  - `target_pages` (string, nullable) - JSON array of target pages (future use)
  - `impressions` (integer) - Number of times banner was viewed
  - `clicks` (integer) - Number of times banner was clicked
  - `created_at` (string) - ISO 8601 timestamp when banner was created
  - `updated_at` (string) - ISO 8601 timestamp when banner was last updated
- `total` (integer) - Total number of active banners
- `skip` (integer) - Number of items skipped (for pagination)
- `limit` (integer, nullable) - Maximum items returned

**Notes:**
- Only returns banners with `status = active`
- Only returns banners within their date range (if `start_date` and `end_date` are set)
- Banners are sorted by `sort_order` (descending), then by `created_at` (descending)

**Status Codes:**
- `200 OK` - Success

---

#### Get Banner by ID

**Endpoint:** `GET /banners/{banner_id}`

**Authentication:** Not required (public endpoint)

**Path Parameters:**
- `banner_id` (integer, required) - ID of the banner

**Request Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/banners/1"
```

**Response:**
```json
{
  "id": 1,
  "title": "Special Offer",
  "description": "Get 20% off on premium listings",
  "banner_type": "sidebar",
  "image_url": "https://example.com/banner1.jpg",
  "link_url": "https://example.com/offer",
  "status": "active",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-12-31T23:59:59Z",
  "sort_order": 10,
  "target_pages": null,
  "impressions": 1250,
  "clicks": 45,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Banner not found or not active

**Error Response:**
```json
{
  "detail": "Banner not found or not active"
}
```

---

### Track Banner Events

#### Track Banner Impression

**Endpoint:** `POST /banners/{banner_id}/impression`

**Authentication:** Not required (public endpoint)

**Path Parameters:**
- `banner_id` (integer, required) - ID of the banner

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/banners/1/impression"
```

**Response:**
- Status: `204 No Content`
- Body: Empty

**Notes:**
- Increments the `impressions` counter for the banner
- Should be called when the banner is displayed to the user

**Status Codes:**
- `204 No Content` - Impression tracked successfully

---

#### Track Banner Click

**Endpoint:** `POST /banners/{banner_id}/click`

**Authentication:** Not required (public endpoint)

**Path Parameters:**
- `banner_id` (integer, required) - ID of the banner

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/banners/1/click"
```

**Response:**
- Status: `204 No Content`
- Body: Empty

**Notes:**
- Increments the `clicks` counter for the banner
- Should be called when the user clicks on the banner

**Status Codes:**
- `204 No Content` - Click tracked successfully

---

### Banner Types

- `sidebar` - Sidebar banner
- `top` - Top banner
- `middle` - Middle banner
- `bottom` - Bottom banner

### Banner Status

- `active` - Banner is active and visible
- `paused` - Banner is paused (not visible)
- `expired` - Banner has expired (not visible)
- `draft` - Banner is in draft state (not visible)

---

## 🔐 Authentication

Most endpoints require authentication. Include the JWT access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

To get an access token, use the authentication endpoints:
- `POST /api/v1/auth/login` - Login with email/phone and password
- `POST /api/v1/auth/refresh` - Refresh access token

---

## ❌ Error Responses

All endpoints may return the following error responses:

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["query", "reason"],
      "msg": "value is not a valid enumeration member",
      "type": "type_error.enum"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## 📝 Notes

1. **Report Privacy:** Users can only view their own reports. They cannot see reports submitted by other users.

2. **Banner Visibility:** Only active banners within their date range are returned to users. Draft, paused, and expired banners are not accessible via public endpoints.

3. **Banner Tracking:** It's recommended to track impressions when displaying banners and track clicks when users interact with them. This helps measure banner performance.

4. **Rate Limiting:** Consider implementing rate limiting for report submission to prevent abuse.

5. **Moderation Process:** Reports are reviewed by moderators. Users can check the status of their reports using the "View My Reports" endpoints.

---

## 🔗 Related Documentation

- [Main API Documentation](./carloanapi.md) - Complete API reference
- [Authentication API](./carloanapi.md#authentication) - How to authenticate
- [Admin Panel Guide](./carloanapi.md#admin-panel) - Admin endpoints (not covered in this document)

---

**Last Updated:** January 2024  
**API Version:** 1.0.0

