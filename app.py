from flask import Flask, jsonify
import subprocess

app = Flask(__name__)

@app.route("/trigger")
def trigger():
    try:
        subprocess.run(["python", "fetch_data3.py"])
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/")
def home():
    return "Backend running 🚀"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)