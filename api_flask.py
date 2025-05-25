from flask import Flask, request, jsonify
from flask_cors import CORS   #
import sqlite3
import os
import json

app = Flask(__name__)
CORS(app)   # << habilita CORS para todos los orígenes
DB_PATH = os.path.join(os.path.dirname(__file__), "energy_monitoring.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Crea la base de datos y la tabla energy_data si no existen.
    """
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
        conn.commit()


@app.route('/api/energy_data', methods=['POST'])
def receive_energy_data():
    """
    Recibe una lista de registros JSON y los inserta en la base de datos.
    """
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "Se espera una lista de registros JSON"}), 400

    inserted = 0
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for record in data:
            # Validar campos mínimos
            ts = record.get('timestamp')
            pw = record.get('power_estimated_watts')
            if ts is None or pw is None:
                continue
            # Serializar temperatura a JSON string
            temps = record.get('temperature_samples')
            temps_json = json.dumps(temps)

            cursor.execute('''
                INSERT INTO energy_data (
                    timestamp, battery_status, battery_charge, battery_run_time,
                    cpu_usage, gpu_usage, gpu_power_watts, power_estimated_watts,
                    temperature_samples, network_connection, device_name, serial_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ts,
                record.get('battery_status'),
                record.get('battery_charge'),
                record.get('battery_run_time'),
                record.get('cpu_usage'),
                record.get('gpu_usage'),
                record.get('gpu_power_watts'),
                pw,
                temps_json,
                record.get('network_connection'),
                record.get('device_name'),
                record.get('serial_number')
            ))
            inserted += 1
        conn.commit()

    return jsonify({"message": f"{inserted} registros guardados correctamente."}), 200


@app.route('/api/energy_data', methods=['GET'])
def get_energy_data():
    """
    Devuelve todos los registros de energy_data.
    """
    with get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM energy_data ORDER BY id').fetchall()
    results = []
    for row in rows:
        rec = dict(row)
        # Convertir temperatura de JSON string a lista
        rec['temperature_samples'] = json.loads(rec['temperature_samples'])
        results.append(rec)
    return jsonify(results), 200


@app.route('/api/energy_data/by_name/<device_name>', methods=['GET'])
def get_energy_data_by_name(device_name):
    """
    Devuelve todos los registros de energy_data para un device_name específico.
    """
    with get_db_connection() as conn:
        rows = conn.execute(
            'SELECT * FROM energy_data WHERE device_name = ? ORDER BY id',
            (device_name,)
        ).fetchall()
    results = []
    for row in rows:
        rec = dict(row)
        rec['temperature_samples'] = json.loads(rec['temperature_samples'])
        results.append(rec)
    return jsonify(results), 200


@app.route('/api/energy_stats', methods=['GET'])
def get_energy_stats():
    """
    Devuelve estadísticas globales: promedio y máximo de power_estimated_watts,
    promedio de cpu_usage y gpu_usage.
    """
    with get_db_connection() as conn:
        row = conn.execute('''
            SELECT
                AVG(power_estimated_watts) AS avg_power,
                MAX(power_estimated_watts) AS max_power,
                AVG(cpu_usage) AS avg_cpu,
                AVG(gpu_usage) AS avg_gpu
            FROM energy_data
        ''').fetchone()
    stats = dict(row)
    return jsonify(stats), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
