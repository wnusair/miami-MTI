"""
Standalone WebSocket Client - DELETE WHEN DONE TESTING
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
    <title>WS Client</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, sans-serif; background: #F5F7FA; padding: 1.5rem; }
        .container { max-width: 700px; margin: 0 auto; }
        .card { background: white; border: 1px solid #E5E7EB; border-radius: 4px; margin-bottom: 1rem; padding: 1rem; }
        .form-input { width: 100%; padding: 0.5rem; font-size: 0.875rem; border: 1px solid #D1D5DB; border-radius: 2px; margin-bottom: 0.5rem; }
        .form-input:focus { outline: none; border-color: #C3142D; }
        .btn { padding: 0.5rem 1rem; font-size: 0.875rem; border: none; border-radius: 2px; cursor: pointer; background: #C3142D; color: white; }
        .btn:hover { background: #A01025; }
        .btn-sm { padding: 0.25rem 0.5rem; font-size: 0.75rem; background: #E5E7EB; color: #000; }
        .btn-sm:hover { background: #D1D5DB; }
        .row { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem; }
        .row .form-input { margin-bottom: 0; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .status { width: 10px; height: 10px; border-radius: 50%; background: #C3142D; display: inline-block; }
        .status.on { background: #059669; }
        .display { background: #F5F7FA; padding: 1.5rem; text-align: center; border-radius: 4px; }
        .display .val { font-size: 2rem; font-weight: 700; color: #C3142D; }
        .display .meta { font-size: 0.7rem; color: #757575; margin-top: 0.25rem; }
        .log { background: #000; color: #0f0; font-family: monospace; font-size: 0.7rem; padding: 0.75rem; border-radius: 4px; max-height: 150px; overflow-y: auto; }
        @media (max-width: 500px) { .grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="row">
                <input type="text" id="server-url" class="form-input" value="http://localhost:5000">
                <button class="btn" id="connect-btn" onclick="toggleConnection()">Connect</button>
            </div>
            <div class="row">
                <button class="btn-sm" onclick="setServer('http://localhost:5000')">Local</button>
                <button class="btn-sm" onclick="setServer('https://mti.wnusair.org')">Production</button>
                <span style="margin-left:auto;font-size:0.75rem;"><span class="status" id="status-dot"></span> <span id="client-count">0</span> clients</span>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <input type="number" id="number-input" class="form-input" placeholder="Number">
                <button class="btn" style="width:100%" onclick="sendNumber()">Send</button>
            </div>
            <div class="card">
                <input type="text" id="message-input" class="form-input" placeholder="Message">
                <button class="btn" style="width:100%" onclick="sendMessage()">Send</button>
            </div>
        </div>
        
        <div class="grid">
            <div class="display">
                <div class="val" id="received-number">--</div>
                <div class="meta" id="number-meta"></div>
            </div>
            <div class="display">
                <div class="val" id="received-message" style="font-size:1.25rem">--</div>
                <div class="meta" id="message-meta"></div>
            </div>
        </div>
        
        <div class="card" style="margin-top:1rem;padding:0">
            <div class="log" id="event-log"></div>
        </div>
    </div>
    
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <script>
        let socket = null, isConnected = false;
        
        function setServer(url) { document.getElementById('server-url').value = url; }
        
        function toggleConnection() {
            if (isConnected) { socket.disconnect(); socket = null; }
            else { connect(); }
        }
        
        function connect() {
            const url = document.getElementById('server-url').value;
            socket = io(url, { transports: ['websocket', 'polling'], withCredentials: false });
            
            socket.on('connect', () => {
                isConnected = true;
                document.getElementById('status-dot').classList.add('on');
                document.getElementById('connect-btn').textContent = 'Disconnect';
                log('Connected');
            });
            
            socket.on('disconnect', () => {
                isConnected = false;
                document.getElementById('status-dot').classList.remove('on');
                document.getElementById('connect-btn').textContent = 'Connect';
                log('Disconnected');
            });
            
            socket.on('connect_error', (e) => log('Error: ' + e.message));
            socket.on('client_count', (d) => document.getElementById('client-count').textContent = d.count);
            
            socket.on('number_received', (d) => {
                document.getElementById('received-number').textContent = d.value;
                document.getElementById('number-meta').textContent = new Date(d.timestamp).toLocaleTimeString();
            });
            
            socket.on('message_received', (d) => {
                document.getElementById('received-message').textContent = d.message;
                document.getElementById('message-meta').textContent = new Date(d.timestamp).toLocaleTimeString();
            });
        }
        
        function sendNumber() {
            const v = document.getElementById('number-input').value;
            if (v && isConnected) { socket.emit('send_number', { value: parseFloat(v) }); document.getElementById('number-input').value = ''; }
        }
        
        function sendMessage() {
            const m = document.getElementById('message-input').value;
            if (m.trim() && isConnected) { socket.emit('broadcast_message', { message: m }); document.getElementById('message-input').value = ''; }
        }
        
        function log(msg) {
            const el = document.getElementById('event-log');
            el.innerHTML += '[' + new Date().toLocaleTimeString() + '] ' + msg + '\\n';
            el.scrollTop = el.scrollHeight;
        }
        
        document.getElementById('number-input').onkeypress = (e) => { if (e.key === 'Enter') sendNumber(); };
        document.getElementById('message-input').onkeypress = (e) => { if (e.key === 'Enter') sendMessage(); };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(CLIENT_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
