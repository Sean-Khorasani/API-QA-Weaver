# 🚀 API-QA-Weaver Complete Setup Guide

This guide will walk you through setting up API-QA-Weaver from scratch, including all tools and the mock backend.

## 📋 Prerequisites

Before starting, ensure you have:

- **Node.js** v16+ ([Download](https://nodejs.org/))
- **Python** 3.8+ ([Download](https://www.python.org/))
- **Git** ([Download](https://git-scm.com/))
- **Terminal/Command Prompt** access

## 🎯 Step-by-Step Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/Sean-Khorasani/API-QA-Weaver.git
cd API-QA-Weaver
```

### Step 2: Install Node.js Dependencies

```bash
# Install main dependencies
npm install

# Install tool-specific dependencies
cd itoc && npm install && cd ..
cd ctge && npm install && cd ..
cd sets && npm install && cd ..
```

### Step 3: Install Python Dependencies (Optional)

For the multiplayer testing tools:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt
```

### Step 4: Install Mockoon CLI

```bash
npm install -g @mockoon/cli
```

### Step 5: Start Mock Backend Services

```bash
cd mock-backend
chmod +x start-mock-services.sh  # Make executable (Linux/Mac)
./start-mock-services.sh
```

You should see:
```
Starting Mock Backend Services...
================================
All services started!
====================
Main API:          http://localhost:3001
Analytics Service: http://localhost:3002
Notification:      http://localhost:3003
```

### Step 6: Verify Installation

Run the quick start example:

```bash
cd ../examples
npm install axios  # Install example dependencies
node quick-start.js
```

Expected output:
```
🧬 API-QA-Weaver Quick Start Examples
=====================================

✅ Health Check: healthy
✅ Authentication successful, token: 35237e92-3e08-4b55-b...
✅ Products retrieved: 10 items
✅ Order created: 1d74b1c2-db7e-4e5c-a85d-b8d02576836c
```

## 🔧 Testing Each Tool

### ITOC (Intelligent Test Oracle)

```bash
cd itoc
npm run demo
```

### CTGE (Conversational Test Generation)

```bash
cd ctge
npm run demo
```

### SETS (Self-Evolving Test Suite)

```bash
cd sets
npm run demo
```

### Multiplayer Testing Tools

```bash
# With virtual environment activated
python multiplayer-qa-toolkit/network-simulator/network_simulator.py
```

## 🎭 Mock API Endpoints

The mock backend provides these endpoints:

### Main API (Port 3001)
- `POST /auth/login` - User authentication
- `GET /users/:id` - Get user details
- `GET /products` - List products (with pagination)
- `POST /orders` - Create order
- `GET /search` - Search functionality
- `POST /payments/process` - Process payment
- `GET /health` - Health check

### Analytics Service (Port 3002)
- `POST /events` - Track events
- `GET /metrics/:metric` - Get metrics
- `GET /realtime` - Real-time dashboard

### Notification Service (Port 3003)
- `POST /notifications/send` - Send notification
- `GET /notifications/:id/status` - Check status

## 📝 Example API Calls

### Authentication
```bash
curl -X POST http://localhost:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'
```

### Get Products
```bash
curl http://localhost:3001/products?page=1&pageSize=5
```

### Track Event
```bash
curl -X POST http://localhost:3002/events \
  -H "Content-Type: application/json" \
  -d '{"event": "page_view", "properties": {"page": "/home"}}'
```

## 🔍 Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

```bash
# Find process using port
lsof -i :3001  # Linux/Mac
netstat -ano | findstr :3001  # Windows

# Kill mockoon processes
pkill -f mockoon-cli  # Linux/Mac
taskkill /F /IM mockoon-cli.exe  # Windows
```

### Mock Services Not Starting

1. Ensure Mockoon CLI is installed globally:
   ```bash
   npm list -g @mockoon/cli
   ```

2. Check if configuration files exist:
   ```bash
   ls mock-backend/*.json
   ```

3. Try starting services individually:
   ```bash
   mockoon-cli start --data mock-backend/mockoon-config.json
   ```

### TypeScript Compilation Errors

Some TypeScript projects may have compilation issues. You can:

1. Try building with less strict settings:
   ```bash
   cd itoc
   npx tsc --noEmit false --skipLibCheck true
   ```

2. Or use the pre-built examples in the `examples/` directory

### Python Import Errors

Ensure your virtual environment is activated:
```bash
which python  # Should show venv path
pip list      # Should show installed packages
```

## 🚀 Next Steps

1. **Read the User Guide**: Check `docs/USER_GUIDE.md` for detailed usage
2. **Explore Examples**: Look in the `examples/` directory
3. **Run Tests**: Try `npm test` in each tool directory
4. **Customize Mock Data**: Edit the JSON files in `mock-backend/`
5. **Build Your Own Tests**: Use the tools to test your own APIs

## 📚 Additional Resources

- [User Guide](docs/USER_GUIDE.md) - Comprehensive usage guide
- [API Reference](docs/API_REFERENCE.md) - Detailed API documentation
- [Contributing](CONTRIBUTING.md) - How to contribute
- [GitHub Issues](https://github.com/Sean-Khorasani/API-QA-Weaver/issues) - Report bugs or request features

## 💡 Tips

1. **Keep mock services running**: The mock backend needs to stay running for tests
2. **Use virtual environment**: Always activate Python venv for multiplayer tools
3. **Check logs**: Mock services create logs in the `mock-backend/` directory
4. **Experiment freely**: The mock backend is safe to test against

## 🎉 Success!

If you've made it this far, you have a fully functional API-QA-Weaver setup! You can now:

- ✅ Test APIs with intelligent oracle (ITOC)
- ✅ Generate tests from natural language (CTGE)
- ✅ Create self-evolving test suites (SETS)
- ✅ Apply game testing patterns to APIs
- ✅ Test against realistic mock services

Happy testing! 🚀