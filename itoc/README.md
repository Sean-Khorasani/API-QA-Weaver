# ITOC - Intelligent Test Oracle with Contract Learning

ITOC is an AI-powered API testing framework that learns from OpenAPI specifications, production traffic patterns, and historical data to automatically generate comprehensive test assertions and detect anomalies.

## Features

- **Contract Learning**: Automatically learns API contracts from OpenAPI/Swagger specifications
- **Traffic Pattern Analysis**: Monitors and learns from actual API traffic to understand normal behavior
- **Intelligent Test Generation**: Generates test data based on learned patterns and specifications
- **Anomaly Detection**: Identifies performance degradation, unexpected status codes, and schema violations
- **AI-Enhanced Analysis**: Optional integration with OpenAI for semantic anomaly detection
- **Self-Updating**: Continuously updates its understanding as APIs evolve

## Installation

```bash
npm install
npm run build
```

## Quick Start

1. **Start the sample server**:
```bash
npm run server
```

2. **Run the demo** (in another terminal):
```bash
npm run demo
```

## Usage

### Basic Example

```typescript
import { ContractLearner, TestOracle } from './src';

// Initialize the learner
const learner = new ContractLearner();
const oracle = new TestOracle();

// Learn from OpenAPI spec
const contracts = await learner.learnFromOpenAPI('./api-spec.yaml');

// Learn from actual traffic
await learner.learnFromTraffic(
  '/users',
  'GET',
  { params: { limit: 10 } },
  { status: 200, data: { users: [...] } },
  45 // response time in ms
);

// Generate test assertions
const contract = learner.getLearnedContract('/users', 'GET');
const assertions = oracle.generateAssertions(contract, response);

// Evaluate results
const results = oracle.evaluateAssertions(assertions);
console.log(`Passed: ${results.passed}, Failed: ${results.failed}`);
```

### AI-Enhanced Mode

To enable AI-powered semantic analysis:

```typescript
const learner = new ContractLearner(process.env.OPENAI_API_KEY);
```

## How It Works

1. **Contract Learning Phase**:
   - Parses OpenAPI specifications to understand API structure
   - Extracts endpoints, parameters, request/response schemas

2. **Pattern Learning Phase**:
   - Monitors actual API traffic
   - Learns common parameter values
   - Tracks response time patterns (avg, p95, p99)
   - Identifies common status codes and their frequencies

3. **Test Generation**:
   - Uses learned patterns to generate realistic test data
   - Prefers actual values seen in production
   - Falls back to schema-based generation

4. **Assertion Generation**:
   - Creates assertions for status codes, response times, and schemas
   - Checks for contract compliance
   - Identifies anomalies based on historical patterns

5. **Anomaly Detection**:
   - Unexpected status codes
   - Performance degradation (2x slower than average)
   - Schema mismatches
   - AI-powered semantic analysis (optional)

## Test Cases

Run the test suite:

```bash
npm test
```

With coverage:

```bash
npm run test:coverage
```

## Architecture

```
itoc/
├── src/
│   ├── types.ts          # TypeScript interfaces
│   ├── ContractLearner.ts # Main learning engine
│   ├── TestOracle.ts     # Assertion generation and evaluation
│   └── index.ts          # Main exports
├── tests/                # Test files
├── examples/            
│   ├── openapi-spec.yaml # Sample OpenAPI spec
│   ├── sample-server.ts  # Demo API server
│   └── demo.ts          # Interactive demonstration
└── docs/                # Additional documentation
```

## Key Concepts

### Learned Contracts
A learned contract combines:
- Static API specification (OpenAPI)
- Dynamic traffic patterns
- Historical anomalies
- Performance baselines

### Traffic Patterns
ITOC tracks:
- Request frequency
- Common parameter values
- Response status distributions
- Response time percentiles

### Anomaly Types
- `unexpected_status`: Status codes not seen before
- `performance_degradation`: Responses significantly slower than baseline
- `schema_mismatch`: Response doesn't match expected schema
- `new_error_pattern`: New error messages or patterns

## Benefits

1. **Reduced Manual Effort**: No need to manually write test assertions
2. **Adaptive Testing**: Tests evolve with your API
3. **Early Problem Detection**: Identifies issues before they impact users
4. **Comprehensive Coverage**: Learns from actual usage patterns
5. **Performance Monitoring**: Built-in performance regression detection

## Future Enhancements

- Support for more API specification formats (RAML, API Blueprint)
- Integration with popular testing frameworks (Jest, Mocha, Pytest)
- Dashboard for visualizing learned patterns
- Distributed learning across multiple services
- Enhanced AI capabilities for business logic validation