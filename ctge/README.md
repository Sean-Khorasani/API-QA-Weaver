# CTGE - Conversational Test Generation Engine

CTGE is an AI-powered test generation framework that converts natural language descriptions into comprehensive API test suites across multiple programming languages.

## Features

- **Natural Language Processing**: Understands test requirements written in plain English
- **Multi-Language Support**: Generates tests in JavaScript, TypeScript, Python, and Java
- **Intelligent Test Suggestions**: Automatically suggests edge cases and additional test scenarios
- **Framework Integration**: Outputs tests compatible with Jest, pytest, JUnit, and more
- **AI Enhancement**: Optional OpenAI integration for more sophisticated test generation
- **Conversation Memory**: Maintains context across multiple test requests

## Installation

```bash
npm install
npm run build
```

## Quick Start

```typescript
import { ConversationalEngine } from './src';

const engine = new ConversationalEngine();

// Natural language test request
const result = await engine.processUserInput(
  "Test creating a new user with email validation"
);

// Generated test scenario
console.log(result.scenario);

// Generated test code in multiple languages
result.generatedTests.forEach(test => {
  console.log(`${test.language}: ${test.code}`);
});

// Additional test suggestions
result.suggestions.forEach(suggestion => {
  console.log(`Suggestion: ${suggestion.scenario}`);
});
```

## Usage Examples

### Basic Test Generation

```typescript
const engine = new ConversationalEngine();

// Simple CRUD test
const result = await engine.processUserInput(
  "Create a test for updating a product's price"
);

// Access generated JavaScript test
const jsTest = result.generatedTests.find(t => t.language === 'javascript');
console.log(jsTest.code);
```

### With API Context

```typescript
const context = {
  baseUrl: 'https://api.example.com',
  authentication: {
    type: 'bearer' as const,
    credentials: { token: 'your-token' }
  }
};

const result = await engine.processUserInput(
  "Test authenticated endpoints for user profile",
  context
);
```

### AI-Enhanced Mode

```typescript
// With OpenAI for enhanced test generation
const engine = new ConversationalEngine(process.env.OPENAI_API_KEY);

const result = await engine.processUserInput(
  "Create comprehensive security tests for login endpoint including SQL injection and XSS attempts"
);
```

## How It Works

1. **NLP Processing**: Analyzes natural language input to extract:
   - Intent (create, read, update, delete, validate, etc.)
   - Resources (users, products, orders, etc.)
   - Conditions and expectations
   - Data values and constraints

2. **Scenario Generation**: Creates structured test scenarios including:
   - Test steps (setup, requests, assertions, teardown)
   - Expected outcomes
   - Edge cases

3. **Code Generation**: Produces executable test code:
   - Multiple language implementations
   - Framework-specific syntax
   - Proper assertion patterns
   - Authentication handling

4. **Suggestion Engine**: Recommends additional tests for:
   - Edge cases (boundary values, invalid inputs)
   - Security concerns (injection, authentication)
   - Performance testing
   - Data integrity

## Supported Test Types

### CRUD Operations
- Create: "Test creating a new user with all required fields"
- Read: "Verify fetching users with pagination"
- Update: "Test updating user email address"
- Delete: "Ensure users can be deleted successfully"

### Validation Testing
- "Test user registration with invalid email format"
- "Verify required fields validation"
- "Check maximum length constraints"

### Security Testing
- "Test API with invalid authentication tokens"
- "Verify SQL injection protection"
- "Check authorization boundaries"

### Performance Testing
- "Test API response time under load"
- "Verify concurrent request handling"

## Generated Test Structure

### JavaScript/Jest Example
```javascript
describe('Test user creation', () => {
  test('Create new user', async () => {
    const response = await axios.post(`${baseURL}/api/users`, {
      name: 'John Doe',
      email: 'john@example.com'
    });
    
    expect(response.status).toBe(201);
    expect(response.data).toHaveProperty('id');
  });
});
```

### Python/pytest Example
```python
class TestUserCreation:
    def test_create_new_user(self):
        response = requests.post(
            f"{self.BASE_URL}/api/users",
            json={"name": "John Doe", "email": "john@example.com"}
        )
        
        assert response.status_code == 201
        assert "id" in response.json()
```

## Running the Demo

```bash
npm run demo
```

The demo will:
1. Process various natural language test requests
2. Generate test files in `examples/generated-tests/`
3. Show interactive conversation mode
4. Demonstrate programmatic usage

## Testing

```bash
# Run tests
npm test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

## Architecture

```
ctge/
├── src/
│   ├── ConversationalEngine.ts  # Main engine orchestrating the process
│   ├── NLPProcessor.ts          # Natural language understanding
│   ├── TestGenerator.ts         # Code generation for multiple languages
│   └── types.ts                 # TypeScript interfaces
├── tests/                       # Unit tests
├── examples/                    # Demo and examples
└── docs/                       # Additional documentation
```

## Edge Case Detection

CTGE automatically suggests testing for:

- **Boundary Values**: Min/max limits, empty strings, zero values
- **Invalid Data**: Malformed inputs, wrong types, special characters
- **Missing Data**: Required fields, null values
- **Security Issues**: Injection attempts, authentication bypasses
- **Concurrency**: Race conditions, simultaneous updates
- **Performance**: Load testing, response time validation

## Future Enhancements

- Support for GraphQL APIs
- Integration with API documentation (Swagger/OpenAPI)
- Visual test flow designer
- Test execution and reporting
- Support for more programming languages (Go, Rust, Ruby)
- Database state management for tests
- Mock server generation