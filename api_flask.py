from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "energy_monitoring.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS energy_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                battery_status TEXT,
                battery_charge INTEGER,
                battery_run_time INTEGER,
                cpu_usage REAL,
                gpu_usage REAL,
                gpu_power_watts REAL,
                power_estimated_watts REAL,
                temperature_samples TEXT,
                network_connection TEXT,
                device_name TEXT,
                serial_number TEXT
            )
        ''')

@app.route('/api/energy_data', methods=['POST'])
def receive_energy_data():
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "Se espera una lista de registros JSON"}), 400

    with get_db_connection() as conn:
        for record in data:
            # Validar campos mínimos (podrías ampliar)
            if not record.get("timestamp") or not record.get("power_estimated_watts"):
                continue
            conn.execute('''
                INSERT INTO energy_data (
                    timestamp, battery_status, battery_charge, battery_run_time,
                    cpu_usage, gpu_usage, gpu_power_watts, power_estimated_watts,
                    temperature_samples, network_connection, device_name, serial_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.get('timestamp'),
                record.get('battery_status'),
                record.get('battery_charge'),
                record.get('battery_run_time'),
                record.get('cpu_usage'),
                record.get('gpu_usage'),
                record.get('gpu_power_watts'),
                record.get('power_estimated_watts'),
                record.get('temperature_samples'),
                record.get('network_connection'),
                record.get('device_name'),
                record.get('serial_number')
            ))
        conn.commit()
    return jsonify({"message": f"{len(data)} registros guardados correctamente."}), 200

@app.route('/api/energy_data', methods=['GET'])
def get_energy_data():
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))

    with get_db_connection() as conn:
        rows = conn.execute(
            'SELECT * FROM energy_data ORDER BY id DESC LIMIT ? OFFSET ?', 
            (limit, offset)
        ).fetchall()
    
    results = [dict(row) for row in rows]
    return jsonify(results)

@app.route('/api/energy_stats', methods=['GET'])
def get_energy_stats():
    with get_db_connection() as conn:
        row = conn.execute('''
            SELECT 
                AVG(power_estimated_watts) as avg_power,
                MAX(power_estimated_watts) as max_power,
                AVG(cpu_usage) as avg_cpu,
                AVG(gpu_usage) as avg_gpu
            FROM energy_data
        ''').fetchone()
    return jsonify(dict(row))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
