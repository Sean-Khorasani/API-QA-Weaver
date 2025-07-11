# 🧬 API-QA-Weaver

> AI-powered API testing toolkit featuring intelligent test generation, contract learning, and self-evolving test suites

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js](https://img.shields.io/badge/Node.js-16%2B-green)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)

## 🚀 Overview

API-QA-Weaver revolutionizes API testing by combining artificial intelligence with traditional testing approaches. This comprehensive toolkit includes:

- **ITOC** (Intelligent Test Oracle with Contract Learning) - Learn API behavior from specs and traffic
- **CTGE** (Conversational Test Generation Engine) - Generate tests from natural language descriptions
- **SETS** (Self-Evolving Test Suite) - Tests that automatically adapt to code changes
- **Multiplayer Game Testing Tools** - Enterprise-grade testing patterns adapted from Epic Games

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Tools Overview](#-tools-overview)
- [Usage Examples](#-usage-examples)
- [Mock Backend Setup](#-mock-backend-setup)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🤖 AI-Powered Testing
- Natural language to test code conversion
- Automatic test generation from API specs
- Self-evolving tests that adapt to changes
- Intelligent anomaly detection

### 🎮 Enterprise Testing Patterns
- Network condition simulation
- Load testing with realistic patterns
- Chaos engineering for resilience
- Performance optimization tools

### 🔧 Developer Friendly
- Simple CLI interface
- Comprehensive documentation
- Mock backend included
- Multiple language support

## 🏃 Quick Start

```bash
# Clone the repository
git clone https://github.com/Sean-Khorasani/API-QA-Weaver.git
cd API-QA-Weaver

# Install dependencies
npm install

# Set up mock backend
cd mock-backend
npm install -g @mockoon/cli
./start-mock-services.sh

# Run example tests
npm run demo
```

## 📦 Installation

### Prerequisites

- Node.js 16+ and npm
- Python 3.8+ (for multiplayer testing tools)
- Git

### Detailed Setup

1. **Clone the repository:**
```bash
git clone https://github.com/Sean-Khorasani/API-QA-Weaver.git
cd API-QA-Weaver
```

2. **Install Node.js dependencies:**
```bash
npm install
```

3. **Install Python dependencies (optional):**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. **Set up Mockoon (mock backend):**
```bash
npm install -g @mockoon/cli
```

## 🛠️ Tools Overview

### ITOC (Intelligent Test Oracle with Contract Learning)

Learn API contracts from OpenAPI specs and real traffic to generate comprehensive test suites.

```typescript
const oracle = new IntelligentTestOracle("http://api.example.com");
oracle.loadOpenAPISpec(spec);
oracle.learnFromTraffic(request, response);
const tests = oracle.generateTestSuite();
```

### CTGE (Conversational Test Generation Engine)

Convert natural language descriptions into executable test code.

```typescript
const engine = new ConversationalEngine();
engine.processInput("Test the login endpoint with invalid credentials");
const testCode = engine.generateTest();
```

### SETS (Self-Evolving Test Suite)

Automatically update tests when your API changes.

```typescript
const sets = new SelfEvolvingTestSuite("./src");
sets.watch(); // Tests evolve automatically
```

### Multiplayer Game Testing Tools

Enterprise-grade testing patterns from Epic Games, applicable to any high-traffic API.

- Network simulation
- Load testing
- Chaos engineering
- Performance analysis

## 📚 Usage Examples

### Basic API Testing

```javascript
// Test with ITOC
const oracle = new IntelligentTestOracle("http://localhost:3001");
oracle.loadOpenAPISpec(apiSpec);

// Generate tests
const tests = oracle.generateTestSuite();
tests.forEach(test => test.run());
```

### Natural Language Test Generation

```javascript
// Using CTGE
const engine = new ConversationalEngine();

engine.processInput("I need to test user registration");
engine.processInput("The endpoint is POST /users");
engine.processInput("It should validate email format");

const testCode = engine.generateTest();
```

### Self-Evolving Tests

```javascript
// Using SETS
const sets = new SelfEvolvingTestSuite({
  projectPath: "./api",
  testPath: "./tests",
  watch: true
});

// Tests automatically update when API changes
sets.on('test-evolved', (change) => {
  console.log(`Test evolved: ${change.description}`);
});
```

## 🎭 Mock Backend Setup

We include a complete mock backend using Mockoon for testing:

1. **Start mock services:**
```bash
cd mock-backend
./start-mock-services.sh
```

2. **Services available:**
- Main API: `http://localhost:3001`
- Analytics: `http://localhost:3002`
- Notifications: `http://localhost:3003`

3. **Test the services:**
```bash
curl http://localhost:3001/health
```

## 📖 Documentation

- [User Guide](docs/USER_GUIDE.md) - Complete walkthrough
- [API Reference](docs/API_REFERENCE.md) - Detailed API documentation
- [Examples](examples/) - Sample code and use cases
- [Architecture](docs/ARCHITECTURE.md) - System design details

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by testing practices at Epic Games
- Built with TypeScript and Python
- Mock backend powered by Mockoon
- AI capabilities via OpenAI (optional)

## 📞 Support

- 📧 Email: support@api-qa-weaver.dev
- 💬 Discord: [Join our community](https://discord.gg/api-qa-weaver)
- 🐛 Issues: [GitHub Issues](https://github.com/Sean-Khorasani/API-QA-Weaver/issues)

---

<p align="center">Made with ❤️ by the API-QA-Weaver Team</p>