import { ContractLearner, TestOracle } from '../src';
import axios from 'axios';

async function runDemo() {
  console.log('=== ITOC (Intelligent Test Oracle with Contract Learning) Demo ===\n');

  // Initialize the contract learner
  const learner = new ContractLearner(process.env.OPENAI_API_KEY);
  const oracle = new TestOracle();

  // Step 1: Learn from OpenAPI specification
  console.log('1. Learning from OpenAPI specification...');
  const contracts = await learner.learnFromOpenAPI('./examples/openapi-spec.yaml');
  console.log(`   Learned ${contracts.length} API contracts\n`);

  // Step 2: Simulate traffic and learn patterns
  console.log('2. Simulating API traffic to learn patterns...');
  const baseURL = 'http://localhost:3000/api';
  
  // Simulate various API calls
  for (let i = 0; i < 20; i++) {
    try {
      // GET /users
      const start1 = Date.now();
      const res1 = await axios.get(`${baseURL}/users`, {
        params: { limit: 10, offset: 0 }
      });
      await learner.learnFromTraffic(
        '/users',
        'GET',
        { params: { limit: 10, offset: 0 } },
        { status: res1.status, data: res1.data },
        Date.now() - start1
      );

      // POST /users
      if (i % 3 === 0) {
        const start2 = Date.now();
        const newUser = {
          name: `Test User ${i}`,
          email: `test${i}@example.com`,
          age: 20 + i
        };
        try {
          const res2 = await axios.post(`${baseURL}/users`, newUser);
          await learner.learnFromTraffic(
            '/users',
            'POST',
            { body: newUser },
            { status: res2.status, data: res2.data },
            Date.now() - start2
          );
        } catch (error: any) {
          if (error.response) {
            await learner.learnFromTraffic(
              '/users',
              'POST',
              { body: newUser },
              { status: error.response.status, data: error.response.data },
              Date.now() - start2
            );
          }
        }
      }

      // GET /users/:id
      const userId = Math.floor(Math.random() * 10) + 1;
      const start3 = Date.now();
      try {
        const res3 = await axios.get(`${baseURL}/users/${userId}`);
        await learner.learnFromTraffic(
          '/users/{id}',
          'GET',
          { params: { id: userId } },
          { status: res3.status, data: res3.data },
          Date.now() - start3
        );
      } catch (error: any) {
        if (error.response?.status === 404) {
          await learner.learnFromTraffic(
            '/users/{id}',
            'GET',
            { params: { id: userId } },
            { status: 404, data: error.response.data },
            Date.now() - start3
          );
        }
      }

      await new Promise(resolve => setTimeout(resolve, 100));
    } catch (error) {
      // Continue learning even with errors
    }
  }
  console.log('   Traffic simulation complete\n');

  // Step 3: Display learned patterns
  console.log('3. Learned Patterns:\n');
  const allContracts = learner.getAllContracts();
  
  allContracts.forEach(contract => {
    console.log(`   ${contract.method} ${contract.endpoint}:`);
    console.log(`     - Traffic observed: ${contract.patterns.frequency} requests`);
    console.log(`     - Common status codes:`);
    contract.patterns.commonResponses.forEach(resp => {
      console.log(`       * ${resp.statusCode}: ${(resp.frequency * 100).toFixed(1)}% (avg ${resp.responseTime.avg.toFixed(0)}ms)`);
    });
    if (contract.anomalies.length > 0) {
      console.log(`     - Anomalies detected: ${contract.anomalies.length}`);
      contract.anomalies.forEach(anomaly => {
        console.log(`       * ${anomaly.type}: ${anomaly.description} (${anomaly.severity})`);
      });
    }
    console.log();
  });

  // Step 4: Generate test data and assertions
  console.log('4. Generating Tests with Learned Oracle:\n');
  
  const getUsersContract = learner.getLearnedContract('/users', 'GET');
  if (getUsersContract) {
    console.log('   Testing GET /users:');
    const testData = oracle.generateTestData(getUsersContract);
    console.log(`     - Generated test data: ${JSON.stringify(testData)}`);
    
    // Make actual request
    try {
      const start = Date.now();
      const response = await axios.get(`${baseURL}/users`, { params: testData.query });
      const responseTime = Date.now() - start;
      
      // Generate assertions
      const assertions = oracle.generateAssertions(getUsersContract, {
        status: response.status,
        data: response.data,
        responseTime
      });
      
      // Evaluate assertions
      const results = oracle.evaluateAssertions(assertions);
      console.log(`     - Assertions: ${results.passed} passed, ${results.failed} failed`);
      
      if (results.failed > 0) {
        console.log('     - Failures:');
        results.failures.forEach(failure => {
          console.log(`       * ${failure.message}`);
        });
      }
    } catch (error) {
      console.log(`     - Test failed: ${error}`);
    }
  }

  // Step 5: Test anomaly detection
  console.log('\n5. Testing Anomaly Detection:\n');
  
  // Simulate an anomaly - very slow response
  console.log('   Simulating slow response...');
  const slowStart = Date.now();
  setTimeout(async () => {
    await learner.learnFromTraffic(
      '/users/{id}',
      'GET',
      { params: { id: 1 } },
      { status: 200, data: { id: '1', name: 'Test' } },
      2000 // Very slow response
    );
    
    const contract = learner.getLearnedContract('/users/{id}', 'GET');
    if (contract && contract.anomalies.length > 0) {
      console.log('   Anomaly detected:');
      const latestAnomaly = contract.anomalies[contract.anomalies.length - 1];
      console.log(`     - ${latestAnomaly.type}: ${latestAnomaly.description}`);
    }
  }, 100);
}

// Check if server is running
async function checkServer() {
  try {
    await axios.get('http://localhost:3000/api/users');
    return true;
  } catch (error) {
    return false;
  }
}

// Main execution
(async () => {
  const serverRunning = await checkServer();
  if (!serverRunning) {
    console.log('⚠️  Sample server is not running!');
    console.log('Please run the sample server first:');
    console.log('  npx ts-node examples/sample-server.ts\n');
    process.exit(1);
  }

  try {
    await runDemo();
  } catch (error) {
    console.error('Demo error:', error);
  }
})();