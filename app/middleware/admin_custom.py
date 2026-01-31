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
                    
                    # Inject CSS before </head>
                    css_injection = """
                    <link rel="stylesheet" href="/static/admin-custom.css">
                    <style>
                        /* Force logo display */
                        .navbar-brand::before {
                            content: "";
                            display: inline-block;
                            width: 50px;
                            height: 50px;
                            background-image: url('/static/logo.png');
                            background-size: contain;
                            background-repeat: no-repeat;
                            background-position: center;
                            margin-right: 10px;
                            vertical-align: middle;
                        }
                        .navbar-brand img {
                            display: inline-block !important;
                            visibility: visible !important;
                            opacity: 1 !important;
                            max-height: 50px;
                            width: auto;
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
                        /* Active nav links */
                        .sidebar .nav-link.active {
                            background-color: var(--primary-blue) !important;
                            color: white !important;
                        }
                    </style>
                    """
                    
                    # Inject JS before </body>
                    js_injection = """
                    <script src="/static/admin-upload.js" defer></script>
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
