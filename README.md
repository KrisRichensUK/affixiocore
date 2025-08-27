# Affixio Engine

A stateless, privacy-first, and post-quantum resilient eligibility verification engine.

## Overview

Affixio Engine is designed to provide deterministic YES/NO eligibility verdicts based on immutable rules and verifiable data trails, replacing ambiguity with mathematical proof. The system operates entirely in memory, ensuring no Personal Identifiable Information (PII) is persisted after transaction completion.

## Core Principles

- **Statelessness**: No PII persistence beyond request lifecycle
- **Zero-Trust**: Every verdict is cryptographically signed and verifiable
- **User Infrastructure Deployment**: Runs entirely within client infrastructure
- **Mathematical Certainty**: Deterministic verdicts with verifiable data trails

## Features

- **Stateless Verification**: Complete verification process without state persistence
- **JWT Token Generation**: Cryptographically signed verdicts with QR codes
- **Post-Quantum Cryptography**: Forward-compatible cryptographic primitives
- **Pluggable Data Connectors**: Dynamic external data source integration
- **Rule Engine**: JSON-based rule interpreter with jurisdiction support
- **Circuit Breaker Pattern**: Resilient external service integration
- **Pseudonymised Logging**: Audit trails without PII exposure

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd affixio-engine
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   export AFFIXIO_JWT_SECRET="your-super-secret-jwt-key-that-is-at-least-32-characters-long"
   export AFFIXIO_HOST="0.0.0.0"
   export AFFIXIO_PORT="8000"
   ```

4. **Start the mock server** (for testing)
   ```bash
   python mock_server.py
   ```

5. **Run the application**
   ```bash
   python -m src.main
   ```

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose -f docker/docker-compose.yml up --build
   ```

2. **Or build individual containers**
   ```bash
   docker build -f docker/Dockerfile -t affixio-engine .
   docker run -p 8000:8000 affixio-engine
   ```

## API Usage

### Verify Eligibility

```bash
curl -X POST "http://localhost:8000/api/v1/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "nino": "AB123456C",
    "jurisdiction": "UK",
    "client_id": "test_client"
  }'
```

**Response:**
```json
{
  "verdict": "YES",
  "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "qr_code": "iVBORw0KGgoAAAANSUhEUgAA...",
  "reasoning": "All eligibility criteria met"
}
```

### Verify QR Token

```bash
curl "http://localhost:8000/api/v1/verify-qr/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Get QR Code Image

```bash
curl "http://localhost:8000/api/v1/qr-image/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  --output verification.png
```

## Configuration

### Rules Configuration (`config/rules.json`)

Define eligibility rules in JSON format:

```json
{
  "rules": [
    {
      "name": "CreditScoreCheck",
      "conditions": {
        "AND": [
          {"fact": "credit_score", "operator": "GREATER_THAN_OR_EQUAL_TO", "value": 600}
        ]
      },
      "action": "GRANT_YES",
      "reason_pass": "Credit score meets requirement",
      "reason_fail": "Credit score too low",
      "jurisdiction": "UK"
    }
  ]
}
```

### Endpoints Configuration (`config/endpoints.json`)

Configure external data sources:

```json
{
  "mock_user_api": {
    "url": "http://localhost:8001",
    "method": "GET",
    "auth_type": "none",
    "timeout": 30,
    "retries": 3
  }
}
```

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=src tests/
```

### Test Categories

- **API Tests**: Endpoint functionality and validation
- **Engine Tests**: Core verification logic
- **Security Tests**: JWT token generation and verification

## Architecture

```
affixio-engine/
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   └── endpoints.py        # API endpoints
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   ├── security.py         # Cryptographic functions
│   │   └── stateless_engine.py # Core verification logic
│   ├── logic/
│   │   ├── connectors.py       # Data connectors
│   │   ├── rules.py            # Rule engine
│   │   └── models.py           # Data models
│   └── utils/
│       └── logging.py          # Logging utilities
├── config/
│   ├── rules.json             # Eligibility rules
│   ├── endpoints.json         # Data source config
│   └── settings.toml          # Application settings
├── tests/                     # Test suite
└── docker/                    # Containerization
```

## Security Features

- **JWT Token Signing**: HS256/RS256 signed verdicts
- **Post-Quantum Cryptography**: CRYSTALS-Kyber/Dilithium support
- **PII Hashing**: HMAC-based pseudonymisation
- **Circuit Breaker**: Resilient external service integration
- **Zero-Trust Architecture**: No implicit trust assumptions

## Performance

- **Response Time**: Sub-500ms average
- **Throughput**: 1000+ requests per second per instance
- **Scalability**: Horizontal scaling with no shared state
- **Reliability**: 99.9% uptime target

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Metrics

Prometheus metrics available at `/metrics` (when enabled)

### Logging

Structured logging with pseudonymised audit trails:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "message": "VERIFICATION_REQUEST",
  "nino_hash": "abc123...",
  "jurisdiction": "UK",
  "client_hash": "def456..."
}
```

## Deployment

### Production Deployment

1. **Environment Variables**
   ```bash
   AFFIXIO_JWT_SECRET=<secure-secret>
   AFFIXIO_HOST=0.0.0.0
   AFFIXIO_PORT=8000
   AFFIXIO_DEBUG=false
   ```

2. **Configuration Files**
   - Mount `config/` directory as volume
   - Ensure proper file permissions
   - Validate JSON configuration

3. **Load Balancer**
   - Multiple instances behind load balancer
   - No session affinity required
   - Health check endpoint: `/health`

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: affixio-engine
spec:
  replicas: 3
  selector:
    matchLabels:
      app: affixio-engine
  template:
    metadata:
      labels:
        app: affixio-engine
    spec:
      containers:
      - name: affixio-engine
        image: affixio-engine:latest
        ports:
        - containerPort: 8000
        env:
        - name: AFFIXIO_JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: affixio-secrets
              key: jwt-secret
        volumeMounts:
        - name: config
          mountPath: /app/config
      volumes:
      - name: config
        configMap:
          name: affixio-config
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

[License information]

## Support

For support and questions, please contact [support email/contact information].

