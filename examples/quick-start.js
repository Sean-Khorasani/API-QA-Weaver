/**
 * API-QA-Weaver Quick Start Example
 * 
 * This example demonstrates how to use the testing tools with a mock backend
 */

const axios = require('axios');

// Mock API endpoints
const API_BASE_URL = 'http://localhost:3001';
const ANALYTICS_URL = 'http://localhost:3002';

/**
 * Example 1: Basic API Testing
 */
async function testBasicAPI() {
  console.log('🧪 Testing Basic API Endpoints...\n');

  try {
    // Test health endpoint
    const health = await axios.get(`${API_BASE_URL}/health`);
    console.log('✅ Health Check:', health.data.status);

    // Test authentication
    const login = await axios.post(`${API_BASE_URL}/auth/login`, {
      username: 'testuser',
      password: 'password123'
    });
    console.log('✅ Authentication successful, token:', login.data.token.substring(0, 20) + '...');

    // Test product listing
    const products = await axios.get(`${API_BASE_URL}/products?page=1&pageSize=5`);
    console.log('✅ Products retrieved:', products.data.products.length, 'items');

    // Test order creation
    const order = await axios.post(`${API_BASE_URL}/orders`, {
      items: [
        { productId: 1, quantity: 2 },
        { productId: 3, quantity: 1 }
      ]
    });
    console.log('✅ Order created:', order.data.orderId);

  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

/**
 * Example 2: Analytics Service Testing
 */
async function testAnalytics() {
  console.log('\n📊 Testing Analytics Service...\n');

  try {
    // Track an event
    const event = await axios.post(`${ANALYTICS_URL}/events`, {
      event: 'page_view',
      properties: {
        page: '/products',
        user: 'test-user-123'
      }
    });
    console.log('✅ Event tracked:', event.data.eventId);

    // Get metrics
    const metrics = await axios.get(`${ANALYTICS_URL}/metrics/page_views?period=24h`);
    console.log('✅ Metrics retrieved:');
    console.log('   Total views:', metrics.data.summary.total);
    console.log('   Average:', metrics.data.summary.average);
    console.log('   Peak:', metrics.data.summary.peak);

  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

/**
 * Example 3: Load Testing Pattern
 */
async function testLoadPattern() {
  console.log('\n🚀 Testing Load Patterns...\n');

  const requests = [];
  const startTime = Date.now();

  // Send 20 concurrent requests
  for (let i = 0; i < 20; i++) {
    requests.push(
      axios.get(`${API_BASE_URL}/products?page=${i + 1}`)
        .then(() => ({ success: true, time: Date.now() - startTime }))
        .catch(() => ({ success: false, time: Date.now() - startTime }))
    );
  }

  const results = await Promise.all(requests);
  const successful = results.filter(r => r.success).length;
  const avgTime = results.reduce((sum, r) => sum + r.time, 0) / results.length;

  console.log(`✅ Load test completed:`);
  console.log(`   Success rate: ${(successful / results.length * 100).toFixed(1)}%`);
  console.log(`   Average response time: ${avgTime.toFixed(0)}ms`);
}

/**
 * Example 4: Error Handling Test
 */
async function testErrorHandling() {
  console.log('\n⚠️  Testing Error Handling...\n');

  try {
    // Test invalid login
    try {
      await axios.post(`${API_BASE_URL}/auth/login`, {
        username: 'invalid',
        password: 'wrong'
      });
    } catch (error) {
      if (error.response && error.response.status === 401) {
        console.log('✅ Invalid login correctly rejected:', error.response.data.error);
      }
    }

    // Test rate limiting
    const rateLimitRequests = [];
    for (let i = 0; i < 5; i++) {
      rateLimitRequests.push(axios.get(`${API_BASE_URL}/limited`));
    }

    try {
      await Promise.all(rateLimitRequests);
    } catch (error) {
      if (error.response && error.response.status === 429) {
        console.log('✅ Rate limiting working correctly');
      }
    }

  } catch (error) {
    console.error('❌ Unexpected error:', error.message);
  }
}

/**
 * Main function to run all examples
 */
async function main() {
  console.log('🧬 API-QA-Weaver Quick Start Examples');
  console.log('=====================================\n');

  console.log('⚠️  Make sure mock services are running:');
  console.log('   cd mock-backend && ./start-mock-services.sh\n');

  // Wait a moment for user to see the message
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Run all examples
  await testBasicAPI();
  await testAnalytics();
  await testLoadPattern();
  await testErrorHandling();

  console.log('\n✅ All examples completed!');
  console.log('\n📚 Next steps:');
  console.log('   - Check out the User Guide: docs/USER_GUIDE.md');
  console.log('   - Explore ITOC for contract testing');
  console.log('   - Try CTGE for natural language test generation');
  console.log('   - Set up SETS for self-evolving tests');
}

// Run the examples
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { testBasicAPI, testAnalytics, testLoadPattern, testErrorHandling };