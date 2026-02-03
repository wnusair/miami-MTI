"""
Standalone WebSocket Client - DELETE WHEN DONE TESTING

Run from a separate device to test WebSocket connectivity to the main MTI app.
Usage: python websocket_client_app.py
Then open http://localhost:5001 in your browser.
"""
import os
from flask import Flask, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key')

CLIENT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MTI WebSocket Test Client</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, sans-serif; background: #F5F7FA; padding: 1rem; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #C3142D; font-size: 1.25rem; margin-bottom: 1rem; }
        .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
        .grid-wide { grid-column: span 3; }
        .grid-2 { grid-column: span 2; }
        @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } .grid-wide, .grid-2 { grid-column: span 1; } }
        .card { background: white; border: 1px solid #E5E7EB; border-radius: 4px; }
        .card-header { padding: 0.75rem 1rem; border-bottom: 1px solid #E5E7EB; font-weight: 600; font-size: 0.875rem; display: flex; justify-content: space-between; align-items: center; }
        .card-body { padding: 1rem; }
        .form-input { width: 100%; padding: 0.5rem; font-size: 0.875rem; border: 1px solid #D1D5DB; border-radius: 2px; margin-bottom: 0.5rem; font-family: inherit; }
        .form-input:focus { outline: none; border-color: #C3142D; }
        textarea.form-input { min-height: 60px; resize: vertical; font-family: monospace; }
        .btn { padding: 0.5rem 1rem; font-size: 0.875rem; border: none; border-radius: 2px; cursor: pointer; background: #C3142D; color: white; }
        .btn:hover { background: #A01025; }
        .btn:disabled { background: #D1D5DB; cursor: not-allowed; }
        .btn-block { width: 100%; }
        .btn-sm { padding: 0.25rem 0.5rem; font-size: 0.75rem; }
        .btn-outline { background: white; color: #000; border: 1px solid #D1D5DB; }
        .btn-outline:hover { background: #F5F7FA; }
        .row { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem; flex-wrap: wrap; }
        .row .form-input { margin-bottom: 0; flex: 1; min-width: 150px; }
        .status { width: 10px; height: 10px; border-radius: 50%; background: #C3142D; display: inline-block; }
        .status.on { background: #059669; }
        .display { background: #F5F7FA; padding: 1rem; text-align: center; border-radius: 4px; }
        .display .val { font-size: 2rem; font-weight: 700; color: #C3142D; }
        .display .val-sm { font-size: 1rem; word-break: break-word; }
        .display .meta { font-size: 0.7rem; color: #757575; margin-top: 0.25rem; }
        .stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin-bottom: 0.75rem; font-size: 0.75rem; text-align: center; }
        .stats-row span { color: #757575; }
        .log { background: #000; color: #0f0; font-family: monospace; font-size: 0.7rem; padding: 0.75rem; border-radius: 4px; max-height: 200px; overflow-y: auto; }
        .received-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .json-display { background: #F5F7FA; padding: 0.75rem; border-radius: 4px; font-family: monospace; font-size: 0.7rem; max-height: 150px; overflow: auto; white-space: pre-wrap; word-break: break-word; }
        .image-preview { max-width: 100%; max-height: 150px; border: 1px solid #E5E7EB; border-radius: 4px; display: block; margin-top: 0.5rem; }
        .image-container { text-align: center; min-height: 50px; }
        .image-placeholder { color: #757575; padding: 1rem; background: #F5F7FA; border-radius: 4px; font-size: 0.75rem; }
        .env-badge { display: inline-block; padding: 0.25rem 0.5rem; font-size: 0.7rem; border-radius: 2px; font-weight: 600; }
        .env-dev { background: #DBEAFE; color: #1D4ED8; }
        .env-prod { background: #FEE2E2; color: #991B1B; }
        .slider-container { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
        .slider-container input[type="range"] { flex: 1; }
        .slider-container span { font-size: 0.75rem; min-width: 40px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>MTI WebSocket Test Client</h1>
        
        <div class="grid">
            <div class="card grid-wide">
                <div class="card-header">
                    Connection
                    <span id="env-badge" class="env-badge env-dev">DEV</span>
                </div>
                <div class="card-body">
                    <div class="row">
                        <input type="text" id="server-url" class="form-input" value="http://localhost:5000">
                        <button class="btn" id="connect-btn" onclick="toggleConnection()">Connect</button>
                    </div>
                    <div class="row">
                        <button class="btn btn-sm btn-outline" onclick="setServer('http://localhost:5000')">Local (Dev)</button>
                        <button class="btn btn-sm btn-outline" onclick="setServer('https://mti.wnusair.org')">Production</button>
                        <span style="margin-left:auto;font-size:0.75rem;">
                            <span class="status" id="status-dot"></span>
                            <span id="status-text">Disconnected</span>
                            &nbsp;|&nbsp;
                            <span id="client-count">0</span> clients
                        </span>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">Latency Test</div>
                <div class="card-body">
                    <div class="display" style="margin-bottom:0.75rem">
                        <div class="val"><span id="latency-value">--</span><span style="font-size:1rem;color:#757575">ms</span></div>
                    </div>
                    <div class="stats-row">
                        <div><span>Min:</span> <span id="latency-min">--</span></div>
                        <div><span>Avg:</span> <span id="latency-avg">--</span></div>
                        <div><span>Max:</span> <span id="latency-max">--</span></div>
                        <div><span>N:</span> <span id="latency-samples">0</span></div>
                    </div>
                    <div class="row">
                        <button class="btn btn-sm" onclick="measureLatency()">Ping</button>
                        <button class="btn btn-sm btn-outline" onclick="startAutoPing()">Auto</button>
                        <button class="btn btn-sm btn-outline" onclick="stopAutoPing()">Stop</button>
                        <button class="btn btn-sm btn-outline" onclick="clearLatency()">Reset</button>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">Stress Test</div>
                <div class="card-body">
                    <div class="stats-row" style="grid-template-columns: repeat(3, 1fr);">
                        <div><span>Sent:</span> <span id="stress-sent">0</span></div>
                        <div><span>Recv:</span> <span id="stress-received">0</span></div>
                        <div><span>Lost:</span> <span id="stress-lost">0</span></div>
                    </div>
                    <div class="row">
                        <input type="number" id="stress-count" class="form-input" value="100" min="1" max="1000" style="flex:0 0 80px">
                        <button class="btn btn-block" onclick="runStressTest()">Run Stress Test</button>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">Send Number</div>
                <div class="card-body">
                    <input type="number" id="number-input" class="form-input" placeholder="Enter number">
                    <button class="btn btn-block" onclick="sendNumber()">Send</button>
                </div>
            </div>

            <div class="card">
                <div class="card-header">Send Message</div>
                <div class="card-body">
                    <input type="text" id="message-input" class="form-input" placeholder="Enter message">
                    <button class="btn btn-block" onclick="sendMessage()">Send</button>
                </div>
            </div>

            <div class="card">
                <div class="card-header">Send JSON</div>
                <div class="card-body">
                    <textarea id="json-input" class="form-input" placeholder='{"key": "value"}'></textarea>
                    <button class="btn btn-block" onclick="sendJson()">Send</button>
                </div>
            </div>

            <div class="card grid-wide">
                <div class="card-header">Send Image</div>
                <div class="card-body">
                    <div class="row">
                        <input type="file" id="image-input" accept="image/*" onchange="previewImage(event)" style="flex:1">
                        <button class="btn" onclick="sendImage()">Send Image</button>
                    </div>
                    <div class="slider-container">
                        <span>Quality:</span>
                        <input type="range" id="image-quality" min="10" max="100" value="50">
                        <span id="quality-value">50%</span>
                    </div>
                    <div class="slider-container">
                        <span>Max Size:</span>
                        <input type="range" id="image-maxsize" min="100" max="1000" value="400" step="50">
                        <span id="maxsize-value">400px</span>
                    </div>
                    <div class="image-container">
                        <img id="image-preview" class="image-preview" style="display:none">
                        <div id="image-info" style="font-size:0.7rem;color:#757575;margin-top:0.25rem"></div>
                    </div>
                </div>
            </div>

            <div class="card grid-wide">
                <div class="card-header">Received Data</div>
                <div class="card-body">
                    <div class="received-grid">
                        <div class="display">
                            <div class="val" id="received-number">--</div>
                            <div class="meta">Number</div>
                            <div class="meta" id="number-meta"></div>
                        </div>
                        <div class="display">
                            <div class="val val-sm" id="received-message">--</div>
                            <div class="meta">Message</div>
                            <div class="meta" id="message-meta"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card grid-2">
                <div class="card-header">Received JSON</div>
                <div class="card-body">
                    <pre class="json-display" id="received-json">No JSON received</pre>
                    <div style="font-size:0.7rem;color:#757575;margin-top:0.25rem" id="json-meta"></div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">Received Image</div>
                <div class="card-body">
                    <div class="image-container">
                        <img id="received-image" class="image-preview" style="display:none;max-height:120px">
                        <div id="received-image-placeholder" class="image-placeholder">No image received</div>
                    </div>
                    <div style="font-size:0.7rem;color:#757575;margin-top:0.25rem" id="image-meta"></div>
                </div>
            </div>

            <div class="card grid-wide">
                <div class="card-header">
                    Event Log
                    <button class="btn btn-sm btn-outline" onclick="clearLog()">Clear</button>
                </div>
                <div class="card-body" style="padding:0">
                    <div class="log" id="event-log"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <script>
let socket = null;
let isConnected = false;
let pingInterval = null;
let latencyData = { samples: [], min: null, max: null };
let stressTestSent = 0;
let stressTestReceived = 0;

document.getElementById('image-quality').oninput = function() {
    document.getElementById('quality-value').textContent = this.value + '%';
};
document.getElementById('image-maxsize').oninput = function() {
    document.getElementById('maxsize-value').textContent = this.value + 'px';
};

function setServer(url) {
    document.getElementById('server-url').value = url;
    updateEnvBadge(url);
}

function updateEnvBadge(url) {
    const badge = document.getElementById('env-badge');
    if (url.includes('localhost') || url.includes('127.0.0.1')) {
        badge.textContent = 'DEV';
        badge.className = 'env-badge env-dev';
    } else {
        badge.textContent = 'PROD';
        badge.className = 'env-badge env-prod';
    }
}

function toggleConnection() {
    if (isConnected) {
        socket.disconnect();
        socket = null;
    } else {
        connect();
    }
}

function connect() {
    const url = document.getElementById('server-url').value;
    updateEnvBadge(url);
    log('Connecting to ' + url + '...');
    
    socket = io(url, {
        transports: ['websocket', 'polling'],
        withCredentials: false
    });
    
    socket.on('connect', function() {
        isConnected = true;
        document.getElementById('status-dot').classList.add('on');
        document.getElementById('status-text').textContent = 'Connected';
        document.getElementById('connect-btn').textContent = 'Disconnect';
        log('Connected to server');
        loadLatencyFromStorage();
    });
    
    socket.on('disconnect', function() {
        isConnected = false;
        document.getElementById('status-dot').classList.remove('on');
        document.getElementById('status-text').textContent = 'Disconnected';
        document.getElementById('connect-btn').textContent = 'Connect';
        log('Disconnected from server');
        stopAutoPing();
    });
    
    socket.on('connect_error', function(e) {
        log('Connection error: ' + e.message);
    });
    
    socket.on('connection_response', function(data) {
        log('Server: ' + data.message);
    });
    
    socket.on('client_count', function(data) {
        document.getElementById('client-count').textContent = data.count;
    });
    
    socket.on('pong_latency', function(data) {
        const latency = Date.now() - data.client_time;
        recordLatency(latency);
        log('Latency: ' + latency + 'ms');
    });
    
    socket.on('number_received', function(data) {
        document.getElementById('received-number').textContent = data.value;
        document.getElementById('number-meta').textContent = 'From: ' + data.sender + ' @ ' + new Date(data.timestamp).toLocaleTimeString();
        log('Number: ' + data.value + ' from ' + data.sender);
    });
    
    socket.on('message_received', function(data) {
        document.getElementById('received-message').textContent = data.message;
        document.getElementById('message-meta').textContent = 'From: ' + data.sender + ' @ ' + new Date(data.timestamp).toLocaleTimeString();
        log('Message: "' + data.message + '" from ' + data.sender);
    });
    
    socket.on('json_received', function(data) {
        document.getElementById('received-json').textContent = JSON.stringify(data.payload, null, 2);
        document.getElementById('json-meta').textContent = 'From: ' + data.sender + ' @ ' + new Date(data.timestamp).toLocaleTimeString();
        log('JSON received from ' + data.sender);
    });
    
    socket.on('image_received', function(data) {
        const img = document.getElementById('received-image');
        const placeholder = document.getElementById('received-image-placeholder');
        img.src = data.image;
        img.style.display = 'block';
        placeholder.style.display = 'none';
        document.getElementById('image-meta').textContent = data.filename + ' from ' + data.sender;
        log('Image: ' + data.filename + ' from ' + data.sender);
    });
    
    socket.on('stress_test_response', function(data) {
        stressTestReceived++;
        document.getElementById('stress-received').textContent = stressTestReceived;
        document.getElementById('stress-lost').textContent = stressTestSent - stressTestReceived;
    });
}

function loadLatencyFromStorage() {
    try {
        const stored = localStorage.getItem('latency_stats');
        if (stored) {
            latencyData = JSON.parse(stored);
            updateLatencyDisplay();
        }
    } catch (e) {}
}

function saveLatencyToStorage() {
    try {
        localStorage.setItem('latency_stats', JSON.stringify(latencyData));
    } catch (e) {}
}

function recordLatency(latency) {
    latencyData.samples.push(latency);
    if (latencyData.samples.length > 100) latencyData.samples.shift();
    if (latencyData.min === null || latency < latencyData.min) latencyData.min = latency;
    if (latencyData.max === null || latency > latencyData.max) latencyData.max = latency;
    saveLatencyToStorage();
    updateLatencyDisplay();
}

function updateLatencyDisplay() {
    if (latencyData.samples.length > 0) {
        const latest = latencyData.samples[latencyData.samples.length - 1];
        const avg = Math.round(latencyData.samples.reduce((a, b) => a + b, 0) / latencyData.samples.length);
        document.getElementById('latency-value').textContent = latest;
        document.getElementById('latency-min').textContent = latencyData.min + 'ms';
        document.getElementById('latency-avg').textContent = avg + 'ms';
        document.getElementById('latency-max').textContent = latencyData.max + 'ms';
        document.getElementById('latency-samples').textContent = latencyData.samples.length;
    }
}

function measureLatency() {
    if (isConnected) socket.emit('ping_latency', { client_time: Date.now() });
}

function startAutoPing() {
    if (pingInterval) return;
    pingInterval = setInterval(measureLatency, 1000);
    log('Auto ping started');
}

function stopAutoPing() {
    if (pingInterval) {
        clearInterval(pingInterval);
        pingInterval = null;
        log('Auto ping stopped');
    }
}

function clearLatency() {
    latencyData = { samples: [], min: null, max: null };
    saveLatencyToStorage();
    document.getElementById('latency-value').textContent = '--';
    document.getElementById('latency-min').textContent = '--';
    document.getElementById('latency-avg').textContent = '--';
    document.getElementById('latency-max').textContent = '--';
    document.getElementById('latency-samples').textContent = '0';
    log('Latency stats cleared');
}

function runStressTest() {
    if (!isConnected) { log('Not connected'); return; }
    const count = parseInt(document.getElementById('stress-count').value) || 100;
    stressTestSent = 0;
    stressTestReceived = 0;
    document.getElementById('stress-sent').textContent = '0';
    document.getElementById('stress-received').textContent = '0';
    document.getElementById('stress-lost').textContent = '0';
    log('Stress test: ' + count + ' messages');
    
    for (let i = 0; i < count; i++) {
        setTimeout(function() {
            socket.emit('stress_test', { sequence: i });
            stressTestSent++;
            document.getElementById('stress-sent').textContent = stressTestSent;
        }, i * 10);
    }
}

function sendNumber() {
    const v = document.getElementById('number-input').value;
    if (v && isConnected) {
        socket.emit('send_number', { value: parseFloat(v) });
        log('Sent number: ' + v);
        document.getElementById('number-input').value = '';
    }
}

function sendMessage() {
    const m = document.getElementById('message-input').value;
    if (m.trim() && isConnected) {
        socket.emit('broadcast_message', { message: m });
        log('Sent message: "' + m + '"');
        document.getElementById('message-input').value = '';
    }
}

function sendJson() {
    const str = document.getElementById('json-input').value;
    try {
        const payload = JSON.parse(str);
        socket.emit('send_json', { payload: payload });
        log('Sent JSON');
        document.getElementById('json-input').value = '';
    } catch (e) {
        log('Invalid JSON: ' + e.message);
    }
}

function previewImage(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const img = document.getElementById('image-preview');
        img.src = e.target.result;
        img.style.display = 'block';
        
        const originalSize = Math.round(e.target.result.length / 1024);
        document.getElementById('image-info').textContent = 'Original: ' + originalSize + 'KB';
    };
    reader.readAsDataURL(file);
}

function sendImage() {
    const input = document.getElementById('image-input');
    const file = input.files[0];
    if (!file) { log('No image selected'); return; }
    if (!isConnected) { log('Not connected'); return; }
    
    const quality = parseInt(document.getElementById('image-quality').value) / 100;
    const maxSize = parseInt(document.getElementById('image-maxsize').value);
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            const canvas = document.createElement('canvas');
            let width = img.width;
            let height = img.height;
            
            if (width > maxSize || height > maxSize) {
                if (width > height) {
                    height = Math.round(height * maxSize / width);
                    width = maxSize;
                } else {
                    width = Math.round(width * maxSize / height);
                    height = maxSize;
                }
            }
            
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);
            
            const compressedData = canvas.toDataURL('image/jpeg', quality);
            const compressedSize = Math.round(compressedData.length / 1024);
            
            log('Sending image: ' + file.name + ' (' + compressedSize + 'KB, ' + width + 'x' + height + ')');
            
            socket.emit('send_image', {
                image: compressedData,
                filename: file.name
            });
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function clearLog() {
    document.getElementById('event-log').innerHTML = '';
}

function log(msg) {
    const el = document.getElementById('event-log');
    const time = new Date().toLocaleTimeString();
    el.innerHTML += '<span style="color:#757575">[' + time + ']</span> ' + msg + '\\n';
    el.scrollTop = el.scrollHeight;
}

document.getElementById('number-input').onkeypress = function(e) { if (e.key === 'Enter') sendNumber(); };
document.getElementById('message-input').onkeypress = function(e) { if (e.key === 'Enter') sendMessage(); };
document.getElementById('server-url').oninput = function() { updateEnvBadge(this.value); };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Serve the WebSocket test client page."""
    return render_template_string(CLIENT_TEMPLATE)

if __name__ == '__main__':
    print('MTI WebSocket Test Client')
    print('Open http://localhost:5001 in your browser')
    print('Connect to your MTI server (local or production)')
    app.run(host='0.0.0.0', port=5001, debug=True)
