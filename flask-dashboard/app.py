from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import random
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'healthcare-dashboard-secret-key'

# Mock data generators
def generate_ward_data():
    return [
        {"name": "ICU East", "occupancy": random.randint(85, 95), "status": "critical", "trend": "up"},
        {"name": "ICU West", "occupancy": random.randint(75, 85), "status": "warning", "trend": "stable"},
        {"name": "Emergency", "occupancy": random.randint(85, 95), "status": "warning", "trend": "up"},
        {"name": "General A", "occupancy": random.randint(70, 85), "status": "normal", "trend": "stable"},
        {"name": "General B", "occupancy": random.randint(60, 75), "status": "normal", "trend": "down"},
        {"name": "Pediatrics", "occupancy": random.randint(60, 75), "status": "normal", "trend": "stable"},
        {"name": "Maternity", "occupancy": random.randint(65, 80), "status": "normal", "trend": "up"},
        {"name": "Surgery", "occupancy": random.randint(65, 75), "status": "normal", "trend": "stable"}
    ]

def generate_metrics():
    return {
        "total_beds": 350,
        "occupied_beds": random.randint(250, 280),
        "available_beds": random.randint(70, 100),
        "occupancy_rate": round(random.uniform(70, 85), 1),
        "active_patients": random.randint(140, 170),
        "critical_alerts": random.randint(0, 5),
        "system_load": random.randint(60, 85),
        "staff_on_duty": random.randint(130, 150),
        "avg_wait_time": random.randint(15, 25),
        "satisfaction_score": round(random.uniform(4.2, 4.7), 1)
    }

def generate_chart_data():
    return [
        {"time": "00:00", "occupancy": random.randint(60, 70)},
        {"time": "04:00", "occupancy": random.randint(55, 65)},
        {"time": "08:00", "occupancy": random.randint(70, 80)},
        {"time": "12:00", "occupancy": random.randint(80, 90)},
        {"time": "16:00", "occupancy": random.randint(85, 95)},
        {"time": "20:00", "occupancy": random.randint(75, 85)},
    ]

@app.route('/')
def index():
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    return render_template('overview.html', metrics=generate_metrics(), wards=generate_ward_data())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        if data and data.get('username') == 'admin' and data.get('password') == 'admin':
            session['authenticated'] = True
            session['username'] = data.get('username')
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Invalid credentials"})
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/executive')
def executive():
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    return render_template('executive.html')

@app.route('/operations')
def operations():
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    return render_template('operations.html')

@app.route('/predictive')
def predictive():
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    return render_template('predictive.html')

@app.route('/performance')
def performance():
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    return render_template('performance.html')

@app.route('/patientflow')
def patientflow():
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    return render_template('patientflow.html')

@app.route('/realtime')
def realtime():
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    return render_template('realtime.html')

# API endpoints for real-time data
@app.route('/api/metrics')
def api_metrics():
    return jsonify(generate_metrics())

@app.route('/api/wards')
def api_wards():
    return jsonify(generate_ward_data())

@app.route('/api/chart-data')
def api_chart_data():
    return jsonify(generate_chart_data())

@app.route('/api/realtime')
def api_realtime():
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "occupancy": round(random.uniform(70, 85), 1),
        "active_patients": random.randint(140, 170),
        "admissions": random.randint(5, 15),
        "discharges": random.randint(3, 12),
        "alerts": random.randint(0, 5)
    })

if __name__ == '__main__':
    app.run(debug=True, port=3000, host='0.0.0.0')
