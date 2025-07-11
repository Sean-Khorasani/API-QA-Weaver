import { ContractLearner } from '../src/ContractLearner';
import path from 'path';

describe('ContractLearner', () => {
  let learner: ContractLearner;

  beforeEach(() => {
    learner = new ContractLearner();
  });

  describe('learnFromOpenAPI', () => {
    it('should learn contracts from OpenAPI spec', async () => {
      const specPath = path.join(__dirname, '../examples/openapi-spec.yaml');
      const contracts = await learner.learnFromOpenAPI(specPath);

      expect(contracts).toHaveLength(5); // GET, POST /users + GET, PUT, DELETE /users/{id}
      
      const getUsersContract = contracts.find(c => c.endpoint === '/users' && c.method === 'GET');
      expect(getUsersContract).toBeDefined();
      expect(getUsersContract?.parameters).toHaveLength(2); // limit and offset
      expect(getUsersContract?.responses['200']).toBeDefined();
    });

    it('should extract request body schema', async () => {
      const specPath = path.join(__dirname, '../examples/openapi-spec.yaml');
      const contracts = await learner.learnFromOpenAPI(specPath);

      const postUsersContract = contracts.find(c => c.endpoint === '/users' && c.method === 'POST');
      expect(postUsersContract?.requestBody).toBeDefined();
      expect(postUsersContract?.requestBody?.properties).toHaveProperty('name');
      expect(postUsersContract?.requestBody?.properties).toHaveProperty('email');
    });
  });

  describe('learnFromTraffic', () => {
    it('should learn patterns from traffic', async () => {
      // Simulate multiple requests
      for (let i = 0; i < 10; i++) {
        await learner.learnFromTraffic(
          '/users',
          'GET',
          { params: { limit: 10, offset: 0 } },
          { status: 200, data: { users: [], total: 0 } },
          50 + Math.random() * 50
        );
      }

      const contract = learner.getLearnedContract('/users', 'GET');
      expect(contract).toBeDefined();
      expect(contract?.patterns.frequency).toBe(10);
      expect(contract?.patterns.commonResponses).toHaveLength(1);
      expect(contract?.patterns.commonResponses[0].statusCode).toBe(200);
    });

    it('should detect anomalies in response time', async () => {
      // Establish baseline
      for (let i = 0; i < 5; i++) {
        await learner.learnFromTraffic(
          '/api/test',
          'GET',
          {},
          { status: 200, data: {} },
          50
        );
      }

      // Simulate slow response
      await learner.learnFromTraffic(
        '/api/test',
        'GET',
        {},
        { status: 200, data: {} },
        500 // 10x slower
      );

      const contract = learner.getLearnedContract('/api/test', 'GET');
      expect(contract?.anomalies).toHaveLength(1);
      expect(contract?.anomalies[0].type).toBe('performance_degradation');
    });

    it('should detect unexpected status codes', async () => {
      // Establish pattern with 200 responses
      for (let i = 0; i < 5; i++) {
        await learner.learnFromTraffic(
          '/api/users',
          'POST',
          { body: { name: 'test', email: 'test@example.com' } },
          { status: 201, data: { id: i } },
          100
        );
      }

      // Unexpected error
      await learner.learnFromTraffic(
        '/api/users',
        'POST',
        { body: { name: 'test', email: 'test@example.com' } },
        { status: 500, data: { error: 'Server error' } },
        100
      );

      const contract = learner.getLearnedContract('/api/users', 'POST');
      expect(contract?.anomalies.length).toBeGreaterThan(0);
      const anomaly = contract?.anomalies.find(a => a.type === 'unexpected_status');
      expect(anomaly).toBeDefined();
      expect(anomaly?.severity).toBe('high');
    });
  });

  describe('pattern learning', () => {
    it('should track common parameter values', async () => {
      const params = [
        { limit: 10, offset: 0 },
        { limit: 20, offset: 0 },
        { limit: 10, offset: 10 },
        { limit: 10, offset: 0 },
      ];

      for (const param of params) {
        await learner.learnFromTraffic(
          '/users',
          'GET',
          { params: param },
          { status: 200, data: {} },
          50
        );
      }

      const contract = learner.getLearnedContract('/users', 'GET');
      expect(contract?.patterns.commonParams['limit']).toContain(10);
      expect(contract?.patterns.commonParams['limit']).toContain(20);
      expect(contract?.patterns.commonParams['offset']).toContain(0);
      expect(contract?.patterns.commonParams['offset']).toContain(10);
    });

    it('should calculate response time percentiles', async () => {
      const responseTimes = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
      
      for (const time of responseTimes) {
        await learner.learnFromTraffic(
          '/api/data',
          'GET',
          {},
          { status: 200, data: {} },
          time
        );
      }

      const contract = learner.getLearnedContract('/api/data', 'GET');
      const stats = contract?.patterns.commonResponses[0].responseTime;
      
      expect(stats?.avg).toBe(55); // Average of 10-100
      expect(stats?.p95).toBe(100); // 95th percentile
    });
  });
});