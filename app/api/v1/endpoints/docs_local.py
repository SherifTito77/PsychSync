"""
Local API Documentation Endpoint
Serves Swagger UI from local static files instead of CDN
Compatible with strict CSP policies
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/docs-local", response_class=HTMLResponse, include_in_schema=False)
async def swagger_ui_html():
    """
    Serve Swagger UI using local static files.
    This bypasses CSP restrictions on external CDNs.
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" type="text/css" href="/static/swagger-ui/swagger-ui.css">
        <style>
            html {
                box-sizing: border-box;
                overflow: -moz-scrollbars-vertical;
                overflow-y: scroll;
            }
            *,
            *:before,
            *:after {
                box-sizing: inherit;
            }
            body {
                margin: 0;
                padding: 0;
            }
            .topbar {
                background-color: #1d1d1d;
                padding: 15px 0;
            }
            .link {
                display: inline-block;
                padding: 10px 20px;
                color: #ffffff;
                text-decoration: none;
                font-weight: bold;
                margin: 0 10px;
                border-radius: 4px;
                transition: background-color 0.3s;
            }
            .link:hover {
                background-color: #4a4a4a;
            }
        </style>
    </head>

    <body>
        <div class="topbar">
            <a href="/docs-local" class="link">📚 Swagger UI (Local)</a>
            <a href="/redoc-local" class="link">📖 ReDoc (Local)</a>
            <a href="/openapi.json" class="link">🔧 OpenAPI JSON</a>
            <a href="/" class="link">🏠 Home</a>
        </div>

        <div id="swagger-ui"></div>

        <script src="/static/swagger-ui/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {
                const ui = SwaggerUIBundle({
                    url: '/openapi.json',
                    dom_id: '#swagger-ui',
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout",
                    deepLinking: true,
                    showExtensions: true,
                    showCommonExtensions: true,
                    tryItOutEnabled: true,
                    filter: true,
                    syntaxHighlight: {
                        activate: true,
                        theme: "monokai"
                    },
                    docExpansion: "list",
                    defaultModelsExpandDepth: 1,
                    defaultModelExpandDepth: 1,
                    persistAuthorization: true
                });

                window.ui = ui;
            }
        </script>
    </body>
    </html>
    """


@router.get("/redoc-local", response_class=HTMLResponse, include_in_schema=False)
async def redoc_html():
    """
    Serve ReDoc using local static files.
    Note: ReDoc still needs to be downloaded if you want it fully local.
    For now, this provides a simple alternative view.
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PsychSync AI - ReDoc</title>
        <style>
            body {
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            }
            .topbar {
                background-color: #1d1d1d;
                padding: 15px 0;
            }
            .link {
                display: inline-block;
                padding: 10px 20px;
                color: #ffffff;
                text-decoration: none;
                font-weight: bold;
                margin: 0 10px;
                border-radius: 4px;
            }
            .link:hover {
                background-color: #4a4a4a;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
            }
            .info {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 8px;
                margin-bottom: 30px;
            }
            .endpoints {
                display: grid;
                gap: 15px;
            }
            .endpoint {
                background: #f9fafb;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #059669;
            }
            .method {
                display: inline-block;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
                margin-right: 12px;
                color: white;
                font-size: 14px;
            }
            .get { background: #10b981; }
            .post { background: #3b82f6; }
            .put { background: #f59e0b; }
            .delete { background: #ef4444; }
            .patch { background: #8b5cf6; }
            .path {
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 15px;
                color: #1f2937;
            }
            .description {
                margin-top: 12px;
                color: #6b7280;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: white;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                text-align: center;
            }
            .stat-number {
                font-size: 36px;
                font-weight: bold;
                color: #059669;
            }
            .stat-label {
                margin-top: 8px;
                color: #6b7280;
            }
        </style>
    </head>

    <body>
        <div class="topbar">
            <a href="/docs-local" class="link">📚 Swagger UI (Local)</a>
            <a href="/redoc-local" class="link">📖 ReDoc (Local)</a>
            <a href="/openapi.json" class="link">🔧 OpenAPI JSON</a>
            <a href="/" class="link">🏠 Home</a>
        </div>

        <div class="container">
            <div class="info">
                <h1 style="margin: 0 0 10px 0;">🚀 PsychSync AI - API Documentation</h1>
                <p style="margin: 0;">Fast, local documentation viewer with no external dependencies</p>
            </div>

            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="stat-number" id="totalEndpoints">-</div>
                    <div class="stat-label">Total Endpoints</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="endpointsWithExamples">-</div>
                    <div class="stat-label">With Examples</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="coverage">-</div>
                    <div class="stat-label">Coverage</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="getEndpoints">-</div>
                    <div class="stat-label">GET Endpoints</div>
                </div>
            </div>

            <h2 style="color: #1f2937;">📋 API Endpoints</h2>
            <div class="endpoints" id="endpoints"></div>
        </div>

        <script>
            fetch('/openapi.json')
                .then(response => response.json())
                .then(spec => {
                    const paths = spec.paths || {};
                    const endpoints = [];
                    let totalEndpoints = 0;
                    let endpointsWithExamples = 0;
                    let getCount = 0;

                    for (const [path, methods] of Object.entries(paths)) {
                        for (const [method, details] of Object.entries(methods)) {
                            totalEndpoints++;
                            if (method === 'get') getCount++;

                            // Check for examples
                            let hasExample = false;
                            if (details.responses) {
                                for (const [status, response] of Object.entries(details.responses)) {
                                    if (response.content && response.content['application/json'] && response.content['application/json'].example) {
                                        hasExample = true;
                                        break;
                                    }
                                }
                            }
                            if (hasExample) endpointsWithExamples++;

                            endpoints.push({
                                path: path,
                                method: method.toUpperCase(),
                                summary: details.summary || details.description || 'No description',
                                hasExample: hasExample
                            });
                        }
                    }

                    // Update stats
                    document.getElementById('totalEndpoints').textContent = totalEndpoints;
                    document.getElementById('endpointsWithExamples').textContent = endpointsWithExamples;
                    document.getElementById('coverage').textContent = ((endpointsWithExamples / totalEndpoints) * 100).toFixed(1) + '%';
                    document.getElementById('getEndpoints').textContent = getCount;

                    // Display endpoints (first 50)
                    const container = document.getElementById('endpoints');
                    container.innerHTML = endpoints.slice(0, 50).map(ep => `
                        <div class="endpoint">
                            <div>
                                <span class="method ${ep.method.toLowerCase()}">${ep.method}</span>
                                <span class="path">${ep.path}</span>
                                ${ep.hasExample ? '<span style="color: #10b981; font-weight: bold;">✅ Has Example</span>' : ''}
                            </div>
                            <div class="description">${ep.summary}</div>
                        </div>
                    `).join('');
                })
                .catch(error => {
                    document.getElementById('stats').innerHTML = `
                        <div style="background: #fee2e2; padding: 20px; border-radius: 8px; color: #991b1b; grid-column: 1/-1;">
                            <h3>❌ Error Loading Documentation</h3>
                            <p>Could not fetch OpenAPI spec. Make sure the server is running.</p>
                            <p><strong>Error:</strong> ${error.message}</p>
                        </div>
                    `;
                });
        </script>
    </body>
    </html>
    """
