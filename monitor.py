#!/usr/bin/env python3
"""
Real VPS Monitor – Python Web Dashboard
Shows CPU cores, RAM, storage, uptime.
Run: python3 vps_monitor.py
Access: http://your-server-ip:5050
"""

from flask import Flask, jsonify, render_template_string
import subprocess
import re
import os

app = Flask(__name__)

# ---------- System info functions ----------
def get_cpu_cores():
    with open('/proc/cpuinfo', 'r') as f:
        return f.read().count('processor\t:')

def get_ram():
    with open('/proc/meminfo', 'r') as f:
        mem = f.read()
    total = re.search(r'MemTotal:\s+(\d+)', mem)
    avail = re.search(r'MemAvailable:\s+(\d+)', mem)
    if total and avail:
        total_kb = int(total.group(1))
        avail_kb = int(avail.group(1))
        used_kb = total_kb - avail_kb
        return {
            'total_gb': round(total_kb / (1024**2), 1),
            'used_gb': round(used_kb / (1024**2), 1),
            'free_gb': round(avail_kb / (1024**2), 1)
        }
    return {'total_gb': 0, 'used_gb': 0, 'free_gb': 0}

def get_storage():
    try:
        output = subprocess.check_output(['df', '-B1', '/'], universal_newlines=True)
        lines = output.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            total_b = int(parts[1])
            used_b = int(parts[2])
            total_gb = round(total_b / (1024**3), 1)
            used_gb = round(used_b / (1024**3), 1)
            percent = round((used_b / total_b) * 100)
            return {
                'total_gb': total_gb,
                'used_gb': used_gb,
                'percent': percent
            }
    except:
        pass
    return {'total_gb': 0, 'used_gb': 0, 'percent': 0}

def get_uptime():
    with open('/proc/uptime', 'r') as f:
        seconds = float(f.readline().split()[0])
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    mins = rem // 60
    return f"{int(days)}d {int(hours)}h {int(mins)}m"

# ---------- API endpoint ----------
@app.route('/api/stats')
def stats():
    return jsonify({
        'cpu_cores': get_cpu_cores(),
        'ram': get_ram(),
        'storage': get_storage(),
        'uptime': get_uptime()
    })

# ---------- Dashboard HTML (inline template) ----------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VPS Monitor</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; font-family:Segoe UI,sans-serif; }
body { background:#0f172a; color:white; padding:20px; }
.header { text-align:center; margin-bottom:25px; }
.header h1 { font-size:32px; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:15px; }
.card { background:#1e293b; border-radius:16px; padding:20px; box-shadow:0 0 15px rgba(0,0,0,.3); transition:.3s; }
.card:hover { transform:translateY(-5px); }
.title { font-size:14px; color:#94a3b8; margin-bottom:10px; }
.value { font-size:28px; font-weight:bold; }
.online { color:#22c55e; }
.progress { height:10px; background:#334155; border-radius:20px; overflow:hidden; margin-top:10px; }
.bar { height:100%; width:0%; background:#22c55e; transition: width 1s; }
.footer { margin-top:30px; text-align:center; color:#94a3b8; }
</style>
</head>
<body>

<div class="header">
<h1>🚀 VPS Dashboard</h1>
<p>Real Server Information – Auto-refreshed</p>
</div>

<div class="grid">
<div class="card">
    <div class="title">CPU Cores</div>
    <div class="value" id="cpu">--</div>
</div>
<div class="card">
    <div class="title">RAM</div>
    <div class="value" id="ram">--</div>
    <div class="progress"><div class="bar" id="ramBar"></div></div>
</div>
<div class="card">
    <div class="title">Storage (/)</div>
    <div class="value" id="storage">--</div>
    <div class="progress"><div class="bar" id="storageBar"></div></div>
</div>
<div class="card">
    <div class="title">Uptime</div>
    <div class="value" id="uptime">--</div>
</div>
<div class="card">
    <div class="title">Server Status</div>
    <div class="value online" id="status">ONLINE</div>
</div>
<div class="card">
    <div class="title">OS / Kernel</div>
    <div class="value" id="os">--</div>
</div>
</div>

<div class="footer">VPS Monitor – live system data</div>

<script>
async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();

        // CPU cores
        document.getElementById('cpu').innerText = data.cpu_cores + ' cores';

        // RAM
        const ram = data.ram;
        document.getElementById('ram').innerText = ram.used_gb + ' / ' + ram.total_gb + ' GB';
        const ramPercent = (ram.used_gb / ram.total_gb) * 100;
        document.getElementById('ramBar').style.width = ramPercent + '%';

        // Storage
        const sto = data.storage;
        document.getElementById('storage').innerText = sto.used_gb + ' / ' + sto.total_gb + ' GB (' + sto.percent + '%)';
        document.getElementById('storageBar').style.width = sto.percent + '%';

        // Uptime
        document.getElementById('uptime').innerText = data.uptime;

        // Server status (page loaded = online)
        document.getElementById('status').innerText = 'ONLINE';
        document.getElementById('status').className = 'value online';

        // OS info (gathered once, but we can fetch it from the server if we add to API)
        // For simplicity we add a one-time OS reading – here we just leave placeholder,
        // you can extend the API to return os info.
    } catch(e) {
        document.getElementById('status').innerText = 'OFFLINE';
        document.getElementById('status').className = 'value off';
    }
}

// Fetch immediately and then every 10 seconds
fetchStats();
setInterval(fetchStats, 10000);
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=False)
