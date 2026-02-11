"""
Game routes for itch.io embed proxy.
Fetches itch.io content server-side and rewrites URLs to bypass embedding restrictions.
"""
import re
import requests
from urllib.parse import urljoin, urlparse, quote
from flask import Response, abort, current_app, request
from flask_login import login_required
from . import game_bp


# Configure your itch.io game URL here
ITCHIO_GAME_URL = "https://ae-alexander-elert.itch.io/miami-university-ohio"
ITCHIO_BASE_URL = "https://itch.io"
ITCHIO_ASSET_BASE_URL = "https://v6p9d9t4.ssl.hwcdn.net"  # Common itch.io CDN

# Request timeout in seconds
REQUEST_TIMEOUT = 20


def get_request_headers():
    """Get browser-like headers for requests."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }


def rewrite_relative_urls(html_content, base_url):
    """
    Rewrite relative URLs in HTML to absolute URLs pointing to itch.io.
    
    Args:
        html_content: The HTML string to process
        base_url: The base URL to resolve relative paths against
        
    Returns:
        HTML string with rewritten URLs
    """
    # Rewrite src attributes (images, scripts, iframes)
    html_content = re.sub(
        r'(src=["\'])(?!https?://|data:|//)(.*?)(["\'])',
        lambda m: m.group(1) + urljoin(base_url, m.group(2)) + m.group(3),
        html_content
    )
    
    # Rewrite href attributes (stylesheets, links)
    html_content = re.sub(
        r'(href=["\'])(?!https?://|data:|//|#)(.*?)(["\'])',
        lambda m: m.group(1) + urljoin(base_url, m.group(2)) + m.group(3),
        html_content
    )
    
    # Rewrite url() in inline styles
    html_content = re.sub(
        r'(url\(["\']?)(?!https?://|data:)(.*?)(["\']?\))',
        lambda m: m.group(1) + urljoin(base_url, m.group(2)) + m.group(3),
        html_content
    )
    
    # Rewrite srcset attributes (responsive images)
    def rewrite_srcset(match):
        srcset_value = match.group(2)
        # Split by comma, rewrite each URL, rejoin
        entries = srcset_value.split(',')
        rewritten = []
        for entry in entries:
            parts = entry.strip().split()
            if parts:
                url = parts[0]
                if not url.startswith(('http://', 'https://', 'data:')):
                    parts[0] = urljoin(base_url, url)
                rewritten.append(' '.join(parts))
        return match.group(1) + ', '.join(rewritten) + match.group(3)
    
    html_content = re.sub(
        r'(srcset=["\'])(.*?)(["\'])',
        rewrite_srcset,
        html_content
    )
    
    return html_content


def add_permissive_headers(response):
    """Add headers to allow embedding and cross-origin requests."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    # Remove restrictive headers that block embedding
    response.headers.pop('X-Frame-Options', None)
    return response


@game_bp.route('/embed')
@login_required
def proxy_game_embed():
    """
    Proxy the configured itch.io game page with URL rewriting.
    This fetches the game page and rewrites all URLs to be absolute.
        
    Returns:
        The proxied HTML content with rewritten URLs
    """
    target_url = ITCHIO_GAME_URL
    
    try:
        resp = requests.get(target_url, headers=get_request_headers(), timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        
    except requests.exceptions.Timeout:
        current_app.logger.error(f"Timeout fetching itch.io game: {target_url}")
        abort(504, description="Game server timeout")
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error fetching itch.io game: {e}")
        abort(502, description="Unable to fetch game content")
    
    # Get the content and rewrite URLs
    html_content = resp.text
    html_content = rewrite_relative_urls(html_content, target_url)
    
    # Create response with permissive headers
    response = Response(html_content, mimetype='text/html')
    response = add_permissive_headers(response)
    
    return response


@game_bp.route('/frame')
@login_required
def game_frame():
    """
    Serve a minimal HTML page that embeds the itch.io game in a full-page iframe.
    This acts as a wrapper that your dashboard can safely embed.
    """
    # This HTML page will be served from your domain, so it can be embedded
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VR Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        html, body {{
            width: 100%;
            height: 100%;
            overflow: hidden;
            background: #000;
        }}
        .game-container {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #fff;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 1.2rem;
            text-align: center;
        }}
        .loading-spinner {{
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255,255,255,0.3);
            border-top-color: #fff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        .error {{
            display: none;
            color: #ff6b6b;
        }}
        .fallback-btn {{
            display: inline-block;
            margin-top: 1rem;
            padding: 0.75rem 1.5rem;
            background: #fa5c5c;
            color: #fff;
            text-decoration: none;
            border-radius: 4px;
            font-weight: 500;
            transition: background 0.2s;
        }}
        .fallback-btn:hover {{
            background: #ff7676;
        }}
    </style>
</head>
<body>
    <div class="game-container">
        <div class="loading" id="loading">
            <div class="loading-spinner"></div>
            <p>Loading VR Dashboard...</p>
            <div class="error" id="error">
                <p style="margin-top:1rem;">Unable to load embedded game.</p>
                <a href="{ITCHIO_GAME_URL}" target="_blank" rel="noopener noreferrer" class="fallback-btn">
                    Open in New Tab
                </a>
            </div>
        </div>
        <iframe 
            id="game-iframe"
            src="{ITCHIO_GAME_URL}"
            allowfullscreen
            allow="autoplay; fullscreen; gamepad"
            style="opacity: 0; transition: opacity 0.3s;"
        ></iframe>
    </div>
    <script>
        (function() {{
            const iframe = document.getElementById('game-iframe');
            const loading = document.getElementById('loading');
            const error = document.getElementById('error');
            let loadTimeout;
            
            function showGame() {{
                loading.style.display = 'none';
                iframe.style.opacity = '1';
                clearTimeout(loadTimeout);
            }}
            
            function showError() {{
                error.style.display = 'block';
                document.querySelector('.loading-spinner').style.display = 'none';
                document.querySelector('.loading p').style.display = 'none';
            }}
            
            iframe.addEventListener('load', function() {{
                // Give it a moment to actually render
                setTimeout(showGame, 500);
            }});
            
            iframe.addEventListener('error', showError);
            
            // Fallback timeout - if nothing loads in 10 seconds, show error
            loadTimeout = setTimeout(function() {{
                if (iframe.style.opacity === '0') {{
                    showError();
                }}
            }}, 10000);
        }})();
    </script>
</body>
</html>'''
    
    response = Response(html, mimetype='text/html')
    response = add_permissive_headers(response)
    return response


@game_bp.route('/asset-proxy')
@login_required
def proxy_asset():
    """
    Proxy individual assets from itch.io CDN.
    Use this if the game requests assets that need proxying.
    
    Query params:
        url: The full URL of the asset to proxy
    """
    asset_url = request.args.get('url')
    if not asset_url:
        abort(400, description="Missing 'url' parameter")
    
    # Security: Only allow proxying from known itch.io domains
    allowed_domains = ['itch.io', 'hwcdn.net', 'itch.zone']
    if not any(domain in asset_url for domain in allowed_domains):
        abort(403, description="Asset URL not from allowed domain")
    
    try:
        resp = requests.get(asset_url, headers=get_request_headers(), timeout=30, stream=True)
        resp.raise_for_status()
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error proxying asset: {e}")
        abort(502, description="Unable to fetch asset")
    
    # Determine content type from response
    content_type = resp.headers.get('Content-Type', 'application/octet-stream')
    
    response = Response(resp.content, mimetype=content_type)
    response = add_permissive_headers(response)
    
    # Cache static assets
    if any(ext in asset_url for ext in ['.js', '.css', '.png', '.jpg', '.wasm', '.data']):
        response.headers['Cache-Control'] = 'public, max-age=86400'
    
    return response
