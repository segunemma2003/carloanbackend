#!/bin/bash
# Health Check and Endpoint Test Script for FastAPI Backend
# Tests all critical endpoints

BASE_URL="${1:-https://carloanbackend-production.up.railway.app}"
WAIT_TIME="${2:-60}"

echo "=== FastAPI Backend Health Check ==="
echo "Base URL: $BASE_URL"
echo "Waiting ${WAIT_TIME} seconds for services to start..."
sleep $WAIT_TIME

echo ""
echo "Testing /health endpoint..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
if [ "$HEALTH_STATUS" = "200" ]; then
    echo "✅ Health: $HEALTH_STATUS"
else
    echo "❌ Health: $HEALTH_STATUS (expected: 200)"
fi

echo ""
echo "Testing /diagnostic endpoint..."
DIAG_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/diagnostic")
if [ "$DIAG_STATUS" = "200" ]; then
    echo "✅ Diagnostic: $DIAG_STATUS"
    curl -s "$BASE_URL/diagnostic" | python3 -m json.tool 2>/dev/null || curl -s "$BASE_URL/diagnostic"
else
    echo "❌ Diagnostic: $DIAG_STATUS (expected: 200)"
fi

echo ""
echo "Testing /admin endpoint..."
ADMIN_STATUS=$(curl -s -L -o /dev/null -w "%{http_code}" "$BASE_URL/admin")
if [[ "$ADMIN_STATUS" =~ ^(200|301|302)$ ]]; then
    echo "✅ Admin: $ADMIN_STATUS"
else
    echo "❌ Admin: $ADMIN_STATUS (expected: 200 301 302)"
fi

echo ""
echo "Testing /api/docs endpoint (Swagger)..."
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/docs")
if [[ "$DOCS_STATUS" =~ ^(200|301|302)$ ]]; then
    echo "✅ Swagger: $DOCS_STATUS"
else
    echo "❌ Swagger: $DOCS_STATUS (expected: 200 301 302)"
fi

echo ""
echo "Testing /openapi.json endpoint..."
SCHEMA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/openapi.json")
if [[ "$SCHEMA_STATUS" =~ ^(200|301|302)$ ]]; then
    echo "✅ Schema: $SCHEMA_STATUS"
else
    echo "❌ Schema: $SCHEMA_STATUS (expected: 200 301 302)"
fi

echo ""
echo "Testing /api/v1/ads endpoint (public)..."
ADS_STATUS=$(curl -s -L -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/ads")
if [ "$ADS_STATUS" = "200" ]; then
    echo "✅ Ads API: $ADS_STATUS"
else
    echo "❌ Ads API: $ADS_STATUS (expected: 200)"
fi

echo ""
echo "Testing /api/v1/categories endpoint (public)..."
CAT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/categories")
if [ "$CAT_STATUS" = "200" ]; then
    echo "✅ Categories API: $CAT_STATUS"
else
    echo "❌ Categories API: $CAT_STATUS (expected: 200)"
fi

echo ""
echo "=== Route Test Summary ==="
FAILED=0
[ "$HEALTH_STATUS" != "200" ] && FAILED=$((FAILED + 1))
[ "$DIAG_STATUS" != "200" ] && FAILED=$((FAILED + 1))
[[ ! "$ADMIN_STATUS" =~ ^(200|301|302)$ ]] && FAILED=$((FAILED + 1))
[[ ! "$DOCS_STATUS" =~ ^(200|301|302)$ ]] && FAILED=$((FAILED + 1))
[[ ! "$SCHEMA_STATUS" =~ ^(200|301|302)$ ]] && FAILED=$((FAILED + 1))

if [ $FAILED -eq 0 ]; then
    echo "✅ All endpoints are working!"
    exit 0
else
    echo "❌ $FAILED route(s) failed"
    echo ""
    echo "=== TROUBLESHOOTING STEPS ==="
    echo ""
    echo "1. Check Railway deployment logs:"
    echo "   railway logs"
    echo ""
    echo "2. Test endpoints directly:"
    echo "   curl $BASE_URL/health"
    echo "   curl $BASE_URL/diagnostic"
    echo "   curl $BASE_URL/admin"
    echo "   curl $BASE_URL/docs"
    echo ""
    echo "3. Check if application is running:"
    echo "   railway status"
    echo ""
    echo "4. View recent logs:"
    echo "   railway logs --tail 100"
    echo ""
    echo "5. Restart the service:"
    echo "   railway restart"
    exit 1
fi

