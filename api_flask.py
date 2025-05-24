from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "energy_monitoring.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS energy_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            battery_status TEXT,
            battery_charge INTEGER,
            battery_run_time INTEGER,
            cpu_usage REAL,
            gpu_usage REAL,
            power_estimated_watts REAL,
            temperature_samples TEXT,
            network_connection TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/api/energy_data', methods=['POST'])
def receive_energy_data():
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "Se espera una lista de registros JSON"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for record in data:
        cursor.execute('''
            INSERT INTO energy_data (
                timestamp, battery_status, battery_charge, battery_run_time,
                cpu_usage, gpu_usage, power_estimated_watts, temperature_samples, network_connection
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.get('timestamp'),
            record.get('battery_status'),
            record.get('battery_charge'),
            record.get('battery_run_time'),
            record.get('cpu_usage'),
            record.get('gpu_usage'),
            record.get('power_estimated_watts'),
            str(record.get('temperature_samples')),
            record.get('network_connection')
        ))
    conn.commit()
    conn.close()
    return jsonify({"message": f"{len(data)} registros guardados correctamente."}), 200

@app.route('/api/energy_data', methods=['GET'])
def get_energy_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM energy_data ORDER BY id DESC LIMIT 100')  # Últimos 100 registros
    rows = cursor.fetchall()
    conn.close()

    keys = ["id", "timestamp", "battery_status", "battery_charge", "battery_run_time", "cpu_usage", "gpu_usage", "power_estimated_watts", "temperature_samples", "network_connection"]
    results = [dict(zip(keys, row)) for row in rows]

    return jsonify(results)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
