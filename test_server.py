#!/usr/bin/env python3

from flask import Flask, jsonify, request
import time
import random

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "service": "Test Server"
    })

@app.route('/api/v1/verify', methods=['POST'])
def verify():
    data = request.get_json()
    
    # Simulate some processing time
    time.sleep(random.uniform(0.01, 0.05))
    
    # Random verdict
    verdict = "YES" if random.random() > 0.3 else "NO"
    
    return jsonify({
        "verdict": verdict,
        "jwt_token": "test.jwt.token.here",
        "qr_code": "base64_encoded_qr_code",
        "secure_code": data.get("secure_code"),
        "jurisdiction": data.get("jurisdiction")
    })

@app.route('/api/v1/rules')
def rules():
    return jsonify({
        "rules": {
            "eligibility_score": 750,
            "risk_ratio": 0.35,
            "jurisdiction_verified": True
        }
    })

@app.route('/api/v1/endpoints')
def endpoints():
    return jsonify({
        "endpoints": {
            "verify": "/api/v1/verify",
            "health": "/health",
            "rules": "/api/v1/rules"
        }
    })

@app.route('/')
def root():
    return jsonify({
        "service": "Test Server for Stress Testing",
        "status": "operational",
        "endpoints": [
            "/health",
            "/api/v1/verify",
            "/api/v1/rules",
            "/api/v1/endpoints"
        ]
    })

if __name__ == '__main__':
    print("🚀 Starting Test Server for Stress Testing")
    print("📍 Server will be available at: http://localhost:8000")
    print("📊 Endpoints:")
    print("   • GET  /health")
    print("   • POST /api/v1/verify")
    print("   • GET  /api/v1/rules")
    print("   • GET  /api/v1/endpoints")
    print()
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
