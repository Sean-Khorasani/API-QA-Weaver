# 📚 API-QA-Weaver User Guide

Welcome to the comprehensive user guide for API-QA-Weaver! This guide will walk you through everything from initial setup to advanced usage.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Setting Up Mock Backend](#setting-up-mock-backend)
3. [Testing Mock APIs](#testing-mock-apis)
4. [Using ITOC](#using-itoc-intelligent-test-oracle-with-contract-learning)
5. [Using CTGE](#using-ctge-conversational-test-generation-engine)
6. [Using SETS](#using-sets-self-evolving-test-suite)
7. [Multiplayer Testing Tools](#multiplayer-testing-tools)
8. [Advanced Usage](#advanced-usage)
9. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (version 16 or higher)
  ```bash
  node --version  # Should output v16.x.x or higher
  ```

- **Python** (version 3.8 or higher) - for multiplayer testing tools
  ```bash
  python3 --version  # Should output Python 3.8.x or higher
  ```

- **Git**
  ```bash
  git --version
  ```

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/Sean-Khorasani/API-QA-Weaver.git

# Navigate to the project directory
cd API-QA-Weaver
```

### Step 2: Install Dependencies

#### Node.js Dependencies

```bash
# Install all Node.js dependencies
npm install

# This will install dependencies for:
# - ITOC (Intelligent Test Oracle)
# - CTGE (Conversational Test Generation)
# - SETS (Self-Evolving Test Suite)
```

#### Python Dependencies (Optional)

For the multiplayer testing tools:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

## Setting Up Mock Backend

API-QA-Weaver includes a complete mock backend setup using Mockoon for testing purposes.

### Step 1: Install Mockoon CLI

```bash
npm install -g @mockoon/cli
```

### Step 2: Navigate to Mock Backend Directory

```bash
cd mock-backend
```

### Step 3: Start Mock Services

```bash
# Make the script executable (Linux/Mac)
chmod +x start-mock-services.sh

# Start all mock services
./start-mock-services.sh
```

You should see output like:
```
Starting Mock Backend Services...
================================
Starting Main API Service on port 3001...
Starting Analytics Service on port 3002...
Starting Notification Service on port 3003...

All services started!
====================
Main API:          http://localhost:3001
Analytics Service: http://localhost:3002
Notification:      http://localhost:3003
```

### Step 4: Verify Services Are Running

```bash
# Test main API health endpoint
curl http://localhost:3001/health

# Expected response:
{
  "status": "healthy",
  "uptime": 12345,
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "cache": "connected",
    "queue": "connected"
  }
}
```

## Testing Mock APIs

### Quick Test Script

Run the provided test script to verify everything is working:

```bash
# From the project root
python3 test-with-mockoon.py
```

### Manual API Testing

#### Test Authentication

```bash
# Login request
curl -X POST http://localhost:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'
```

#### Test Product Listing

```bash
# Get products
curl http://localhost:3001/products?page=1&pageSize=5
```

#### Test Order Creation

```bash
# Create an order
curl -X POST http://localhost:3001/orders \
  -H "Content-Type: application/json" \
  -d '{"items": [{"productId": 1, "quantity": 2}]}'
```

## Using ITOC (Intelligent Test Oracle with Contract Learning)

ITOC learns from API specifications and traffic to generate intelligent tests.

### Basic Usage

```typescript
import { IntelligentTestOracle } from './itoc';

// Initialize ITOC
const oracle = new IntelligentTestOracle("http://localhost:3001");

// Load OpenAPI specification
oracle.loadOpenAPISpec({
  openapi: "3.0.0",
  info: { title: "My API", version: "1.0.0" },
  paths: {
    "/users": {
      get: {
        responses: {
          "200": {
            description: "User list",
            content: {
              "application/json": {
                schema: {
                  type: "array",
                  items: { $ref: "#/components/schemas/User" }
                }
              }
            }
          }
        }
      }
    }
  }
});

// Learn from actual traffic
oracle.learnFromTraffic(
  { method: "GET", path: "/users" },
  { status: 200, body: [{ id: 1, name: "John" }] }
);

// Generate tests
const tests = oracle.generateTestSuite();
```

### Advanced Features

- **Anomaly Detection**: Detect unusual API behavior
- **Contract Validation**: Ensure responses match specifications
- **Test Data Generation**: Create realistic test data

## Using CTGE (Conversational Test Generation Engine)

CTGE converts natural language descriptions into executable test code.

### Basic Conversation

```typescript
import { ConversationalEngine } from './ctge';

const engine = new ConversationalEngine();

// Have a conversation about testing needs
engine.processInput("I need to test the user registration endpoint");
engine.processInput("It's a POST request to /users/register");
engine.processInput("It should validate email format and password strength");
engine.processInput("Return 201 on success with the new user ID");

// Generate test code
const testCode = engine.generateTest({
  language: 'javascript',
  framework: 'jest'
});

console.log(testCode);
```

### Supported Test Frameworks

- **JavaScript**: Jest, Mocha, Jasmine
- **Python**: pytest, unittest
- **Java**: JUnit, TestNG
- **Go**: testing package

## Using SETS (Self-Evolving Test Suite)

SETS automatically updates your tests when your API changes.

### Initial Setup

```typescript
import { SelfEvolvingTestSuite } from './sets';

const sets = new SelfEvolvingTestSuite({
  projectPath: "./src",
  testOutputPath: "./tests",
  watchEnabled: true
});

// Start watching for changes
sets.watch();
```

### How It Works

1. **Code Analysis**: SETS analyzes your codebase for API endpoints
2. **Test Generation**: Creates tests for discovered endpoints
3. **Change Detection**: Monitors code changes
4. **Test Evolution**: Updates tests automatically

### Configuration

Create a `.sets.config.json` file:

```json
{
  "watchPaths": ["./src", "./api"],
  "testPath": "./tests",
  "excludePatterns": ["*.test.js", "node_modules"],
  "evolutionStrategy": "conservative",
  "aiEnabled": true
}
```

## Multiplayer Testing Tools

These tools apply game testing patterns to API testing.

### Network Simulation

```python
from network_simulator import NetworkConditionSimulator, NetworkCondition

# Create simulator
sim = NetworkConditionSimulator()

# Set network conditions
sim.set_condition(NetworkCondition(
    latency_ms=150,
    jitter_ms=20,
    packet_loss_rate=0.02,
    bandwidth_mbps=10
))

# Test API under these conditions
response = await test_api_with_conditions(sim)
```

### Load Testing

```python
from api_loadtest import LoadTestRunner, LoadProfile

runner = LoadTestRunner("http://localhost:3001")

# Run different load patterns
results = await runner.run_load_test(
    profile=LoadProfile.SPIKE,
    duration=300,
    max_users=1000
)
```

### Chaos Engineering

```python
from chaos_testing import ChaosOrchestrator, ChaosExperiment

chaos = ChaosOrchestrator()

# Define experiment
experiment = ChaosExperiment(
    name="Database failure",
    failure_type="service_down",
    duration=60,
    target="database"
)

# Run chaos test
results = await chaos.run_experiment(experiment)
```

## Advanced Usage

### Integrating with CI/CD

#### GitHub Actions Example

```yaml
name: API Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '16'
          
      - name: Install dependencies
        run: npm install
        
      - name: Start mock backend
        run: |
          npm install -g @mockoon/cli
          cd mock-backend
          ./start-mock-services.sh &
          
      - name: Run tests
        run: npm test
```

### Custom Test Generation

```typescript
// Create custom test generator
const customGenerator = {
  generateTest: (endpoint, method) => {
    return `
      test('${method} ${endpoint}', async () => {
        const response = await api.${method.toLowerCase()}('${endpoint}');
        expect(response.status).toBe(200);
      });
    `;
  }
};

// Use with CTGE
engine.setCustomGenerator(customGenerator);
```

### Performance Monitoring

```typescript
// Enable performance tracking
oracle.enablePerformanceTracking({
  thresholds: {
    p95: 500,  // 500ms
    p99: 1000  // 1000ms
  },
  alerting: true
});
```

## Troubleshooting

### Common Issues

#### Mock Services Not Starting

```bash
# Check if ports are already in use
lsof -i :3001
lsof -i :3002
lsof -i :3003

# Kill existing processes if needed
pkill -f mockoon-cli
```

#### TypeScript Compilation Errors

```bash
# Clean and rebuild
npm run clean
npm run build
```

#### Python Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Debug Mode

Enable debug logging:

```bash
# For Node.js tools
export DEBUG=api-qa-weaver:*
npm run demo

# For Python tools
export LOG_LEVEL=DEBUG
python3 test-multiplayer-tools.py
```

### Getting Help

1. Check the [FAQ](FAQ.md)
2. Search [existing issues](https://github.com/Sean-Khorasani/API-QA-Weaver/issues)
3. Join our [Discord community](https://discord.gg/api-qa-weaver)
4. Create a new issue with:
   - Your environment details
   - Steps to reproduce
   - Error messages
   - Expected vs actual behavior

## Next Steps

Now that you're set up, try:

1. **Run the demos**: `npm run demo`
2. **Explore examples**: Check the `examples/` directory
3. **Read the API docs**: See [API_REFERENCE.md](API_REFERENCE.md)
4. **Contribute**: See [CONTRIBUTING.md](../CONTRIBUTING.md)

Happy testing! 🚀