"""
Middleware to inject custom CSS and JS into SQLAdmin pages.
This ensures logo and brand colors appear on all admin pages including login.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.types import Message


class AdminCustomMiddleware(BaseHTTPMiddleware):
    """Inject custom CSS and JS into admin panel pages."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add CORS headers for static files (SQLAdmin's /admin/statics/*)
        if request.url.path.startswith("/admin/statics") or request.url.path.startswith("/static"):
            # Ensure static files have proper CORS headers
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Cache-Control"] = "public, max-age=31536000"
        
        # Only modify admin panel pages (including login)
        if request.url.path.startswith("/admin"):
            # Check if response is HTML
            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type or not content_type:
                try:
                    # Read response body
                    body = b""
                    async for chunk in response.body_iterator:
                        body += chunk
                    
                    html = body.decode("utf-8")
                    
                    # Don't inject dashboard here - it has its own route at /dashboard-admin
                    # Only inject CSS and JS to customize the appearance
                    
                    # Inject CSS before </head>
                    css_injection = """
                    <link rel="stylesheet" href="/static/admin-custom.css">
                    <style>
                        /* Sidebar - Better colors for logo visibility */
                        .sidebar {
                            background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%) !important;
                            border-right: 1px solid #E5E7EB !important;
                        }
                        .sidebar-header {
                            background: white !important;
                            padding: 20px 15px !important;
                            border-bottom: 2px solid #5B87F5 !important;
                            margin-bottom: 10px;
                        }
                        /* Force logo display with better contrast - no duplicate */
                        .navbar-brand {
                            display: flex !important;
                            align-items: center !important;
                            gap: 12px;
                            padding: 10px 15px !important;
                            background: white !important;
                            border-radius: 8px;
                            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                            margin: 10px !important;
                        }
                        .navbar-brand::before {
                            display: none !important;
                        }
                        .navbar-brand img {
                            display: inline-block !important;
                            visibility: visible !important;
                            opacity: 1 !important;
                            max-height: 45px;
                            width: auto;
                            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
                        }
                        /* Brand colors - Primary Blue #5B87F5 */
                        :root {
                            --primary-blue: #5B87F5;
                            --primary-blue-hover: #4472E4;
                            --red-cta: #DC2626;
                            --success-green: #10B981;
                        }
                        .btn-primary, button[type="submit"].btn-primary, input[type="submit"] {
                            background-color: var(--primary-blue) !important;
                            border-color: var(--primary-blue) !important;
                        }
                        .btn-primary:hover, button[type="submit"].btn-primary:hover {
                            background-color: var(--primary-blue-hover) !important;
                        }
                        .navbar-brand, .navbar-brand a {
                            color: var(--primary-blue) !important;
                        }
                        a {
                            color: var(--primary-blue) !important;
                        }
                        a:hover {
                            color: var(--primary-blue-hover) !important;
                        }
                        /* Login page styling */
                        .login-container, .card {
                            border-top: 3px solid var(--primary-blue) !important;
                        }
                        /* Sidebar navigation links - better styling */
                        .sidebar .nav-link {
                            color: #374151 !important;
                            padding: 12px 20px !important;
                            border-radius: 6px;
                            margin: 4px 10px;
                            transition: all 0.2s ease;
                        }
                        .sidebar .nav-link:hover {
                            background-color: #f3f4f6 !important;
                            color: var(--primary-blue) !important;
                            transform: translateX(2px);
                        }
                        .sidebar .nav-link.active {
                            background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-hover) 100%) !important;
                            color: white !important;
                            box-shadow: 0 2px 8px rgba(91, 135, 245, 0.3);
                            font-weight: 600;
                        }
                    </style>
                    """
                    
                    # Inject JS before </body>
                    js_injection = """
                    <script src="/static/admin-upload.js" defer></script>
                    <script>
                        // Add Dashboard link to admin navigation (don't auto-redirect)
                        document.addEventListener('DOMContentLoaded', function() {
                            // Add Dashboard link to admin navigation
                            const sidebar = document.querySelector('.sidebar');
                            if (sidebar) {
                                // Check if dashboard link already exists
                                const existingLink = sidebar.querySelector('a[href="/dashboard-admin"]');
                                if (!existingLink) {
                                    const dashboardLink = document.createElement('a');
                                    dashboardLink.href = '/dashboard-admin';
                                    dashboardLink.className = 'nav-link';
                                    dashboardLink.innerHTML = '<i class="fa-solid fa-chart-line"></i> Dashboard';
                                    const firstNavItem = sidebar.querySelector('.nav-link');
                                    if (firstNavItem && firstNavItem.parentElement) {
                                        firstNavItem.parentElement.insertBefore(dashboardLink, firstNavItem);
                                    }
                                }
                            }
                        });
                    </script>
                    """
                    
                    # Inject into HTML
                    if "</head>" in html:
                        html = html.replace("</head>", css_injection + "</head>")
                    elif "<head>" in html:
                        html = html.replace("<head>", "<head>" + css_injection)
                    else:
                        # If no head tag, add before </html>
                        html = html.replace("</html>", css_injection + "</html>")
                    
                    if "</body>" in html:
                        html = html.replace("</body>", js_injection + "</body>")
                    elif "</html>" in html:
                        html = html.replace("</html>", js_injection + "</html>")
                    else:
                        html = html + js_injection
                    
                    # Create new headers without Content-Length (let FastAPI calculate it)
                    new_headers = dict(response.headers)
                    new_headers.pop("content-length", None)
                    new_headers.pop("Content-Length", None)
                    
                    return HTMLResponse(
                        content=html,
                        status_code=response.status_code,
                        headers=new_headers
                    )
                except Exception as e:
                    # If injection fails, return original response
                    import traceback
                    print(f"Admin middleware error: {e}")
                    traceback.print_exc()
                    return response
        
        return response
