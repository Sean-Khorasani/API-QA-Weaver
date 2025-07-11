# API Reference

## Table of Contents

- [ITOC (Intelligent Test Oracle)](#itoc-intelligent-test-oracle)
- [CTGE (Conversational Test Generation Engine)](#ctge-conversational-test-generation-engine)
- [SETS (Self-Evolving Test Suite)](#sets-self-evolving-test-suite)
- [Multiplayer Testing Tools](#multiplayer-testing-tools)

## ITOC (Intelligent Test Oracle)

### Class: `IntelligentTestOracle`

The main class for intelligent test generation based on API contracts and traffic learning.

#### Constructor

```typescript
new IntelligentTestOracle(baseUrl: string, options?: ITOCOptions)
```

**Parameters:**
- `baseUrl` (string): The base URL of the API to test
- `options` (ITOCOptions): Optional configuration

**Options:**
```typescript
interface ITOCOptions {
  aiEnabled?: boolean;          // Enable AI-powered features
  openAIKey?: string;           // OpenAI API key
  learningRate?: number;        // How quickly to adapt (0-1)
  anomalyThreshold?: number;    // Threshold for anomaly detection
}
```

#### Methods

##### `loadOpenAPISpec(spec: OpenAPISpec): void`

Load an OpenAPI specification for contract learning.

```typescript
oracle.loadOpenAPISpec({
  openapi: "3.0.0",
  info: { title: "My API", version: "1.0.0" },
  paths: { /* ... */ }
});
```

##### `learnFromTraffic(request: Request, response: Response): void`

Learn from actual API traffic to improve test generation.

```typescript
oracle.learnFromTraffic(
  { method: "GET", path: "/users", headers: {} },
  { status: 200, body: [/* users */], headers: {} }
);
```

##### `generateTestSuite(): TestSuite`

Generate a comprehensive test suite based on learned patterns.

```typescript
const suite = oracle.generateTestSuite();
suite.tests.forEach(test => test.run());
```

##### `detectAnomaly(request: Request): number`

Detect anomalous requests (0-1 score, higher = more anomalous).

```typescript
const anomalyScore = oracle.detectAnomaly({
  method: "GET",
  path: "/users/../../etc/passwd"
});
```

## CTGE (Conversational Test Generation Engine)

### Class: `ConversationalEngine`

Natural language interface for test generation.

#### Constructor

```typescript
new ConversationalEngine(config?: CTGEConfig)
```

**Configuration:**
```typescript
interface CTGEConfig {
  language?: 'javascript' | 'typescript' | 'python' | 'java' | 'go';
  framework?: 'jest' | 'mocha' | 'pytest' | 'junit';
  style?: 'bdd' | 'tdd';
  aiModel?: string;
}
```

#### Methods

##### `processInput(input: string): string`

Process natural language input and return a response.

```typescript
const response = engine.processInput("Test the login endpoint");
```

##### `generateTest(options?: GenerateOptions): string`

Generate test code based on the conversation context.

```typescript
const testCode = engine.generateTest({
  language: 'javascript',
  framework: 'jest',
  includeComments: true
});
```

##### `resetContext(): void`

Clear the conversation context to start fresh.

```typescript
engine.resetContext();
```

##### `getContext(): ConversationContext`

Get the current conversation context.

```typescript
const context = engine.getContext();
console.log(context.endpoints, context.testCases);
```

## SETS (Self-Evolving Test Suite)

### Class: `SelfEvolvingTestSuite`

Automatically evolving test suite that adapts to code changes.

#### Constructor

```typescript
new SelfEvolvingTestSuite(config: SETSConfig)
```

**Configuration:**
```typescript
interface SETSConfig {
  projectPath: string;        // Path to project source
  testOutputPath: string;     // Where to write tests
  watchEnabled?: boolean;     // Enable file watching
  evolutionStrategy?: 'conservative' | 'aggressive';
  excludePatterns?: string[]; // Files to ignore
}
```

#### Methods

##### `analyze(): Promise<Analysis[]>`

Analyze the codebase for API endpoints.

```typescript
const endpoints = await sets.analyze();
endpoints.forEach(ep => console.log(ep.path, ep.method));
```

##### `generateTests(analysis: Analysis): Promise<string>`

Generate tests for a specific endpoint.

```typescript
const testCode = await sets.generateTests(endpoints[0]);
```

##### `watch(): void`

Start watching for code changes.

```typescript
sets.watch();
sets.on('change', (change) => {
  console.log('Code changed:', change.file);
});
```

##### `evolve(change: Change): Promise<Evolution>`

Evolve tests based on a code change.

```typescript
const evolution = await sets.evolve({
  file: 'api/users.js',
  type: 'modify',
  endpoints: ['/users', '/users/:id']
});
```

## Multiplayer Testing Tools

### NetworkConditionSimulator

Simulate various network conditions for testing.

```python
class NetworkConditionSimulator:
    def __init__(self):
        """Initialize the network simulator"""
    
    def set_condition(self, condition: NetworkCondition):
        """Set the current network condition"""
    
    def apply_latency(self) -> float:
        """Get latency with jitter applied"""
    
    def should_drop_packet(self) -> bool:
        """Determine if packet should be dropped"""
```

### LoadTestRunner

Run load tests with various patterns.

```python
class LoadTestRunner:
    def __init__(self, base_url: str, endpoints: List[str]):
        """Initialize load test runner"""
    
    async def run_load_test(
        self,
        profile: LoadProfile,
        duration: float,
        max_users: int
    ) -> LoadTestMetrics:
        """Run a load test with specified profile"""
```

#### Load Profiles

- `SUSTAINED`: Constant load
- `SPIKE`: Sudden traffic spike
- `WAVE`: Gradual increase and decrease
- `GAME_LAUNCH`: Game launch pattern

### ChaosOrchestrator

Orchestrate chaos engineering experiments.

```python
class ChaosOrchestrator:
    def __init__(self, service_mesh: ServiceMesh):
        """Initialize chaos orchestrator"""
    
    async def run_experiment(
        self,
        experiment: ChaosExperiment
    ) -> ChaosResult:
        """Run a chaos experiment"""
```

#### Chaos Types

- `SERVICE_FAILURE`: Complete service outage
- `LATENCY_INJECTION`: Add artificial latency
- `NETWORK_PARTITION`: Split network
- `RESOURCE_EXHAUSTION`: Consume resources
- `CLOCK_SKEW`: Time manipulation

## Common Types

### Request

```typescript
interface Request {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  path: string;
  headers?: Record<string, string>;
  body?: any;
  query?: Record<string, string>;
}
```

### Response

```typescript
interface Response {
  status: number;
  headers?: Record<string, string>;
  body?: any;
  time?: number;
}
```

### TestCase

```typescript
interface TestCase {
  name: string;
  endpoint: string;
  method: string;
  input?: any;
  expectedOutput?: any;
  assertions: Assertion[];
}
```

### LoadTestMetrics

```python
class LoadTestMetrics:
    total_requests: int
    successful_requests: int
    failed_requests: int
    throughput: float  # requests per second
    error_rate: float
    percentiles: Dict[str, float]  # p50, p90, p95, p99
```

## Error Handling

All tools follow consistent error handling patterns:

```typescript
try {
  const result = await tool.operation();
} catch (error) {
  if (error instanceof ValidationError) {
    // Handle validation errors
  } else if (error instanceof NetworkError) {
    // Handle network errors
  } else {
    // Handle unexpected errors
  }
}
```

## Events

Many tools emit events for monitoring:

```typescript
oracle.on('test-generated', (test) => {
  console.log('New test:', test.name);
});

sets.on('evolution', (change) => {
  console.log('Tests evolved:', change.description);
});

engine.on('conversation', (message) => {
  console.log('User said:', message);
});
```

## Best Practices

1. **Initialize with appropriate configuration**
   ```typescript
   const oracle = new IntelligentTestOracle(baseUrl, {
     aiEnabled: true,
     learningRate: 0.1
   });
   ```

2. **Handle async operations properly**
   ```typescript
   await sets.analyze();
   await loadRunner.run_load_test();
   ```

3. **Use type-safe interfaces**
   ```typescript
   const request: Request = {
     method: 'GET',
     path: '/users'
   };
   ```

4. **Monitor events for insights**
   ```typescript
   oracle.on('anomaly-detected', (anomaly) => {
     logger.warn('Anomaly:', anomaly);
   });
   ```

5. **Clean up resources**
   ```typescript
   oracle.destroy();
   sets.stopWatching();
   ```