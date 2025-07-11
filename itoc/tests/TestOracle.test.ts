import { TestOracle } from '../src/TestOracle';
import { LearnedContract } from '../src/types';

describe('TestOracle', () => {
  let oracle: TestOracle;
  let sampleContract: LearnedContract;

  beforeEach(() => {
    oracle = new TestOracle();
    sampleContract = {
      endpoint: '/users',
      method: 'GET',
      parameters: [
        {
          name: 'limit',
          in: 'query',
          required: false,
          schema: { type: 'integer', minimum: 1, maximum: 100 }
        }
      ],
      responses: {
        '200': {
          description: 'Success',
          schema: {
            type: 'object',
            properties: {
              users: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    id: { type: 'string' },
                    name: { type: 'string' }
                  },
                  required: ['id', 'name']
                }
              },
              total: { type: 'integer' }
            },
            required: ['users', 'total']
          }
        }
      },
      patterns: {
        endpoint: '/users',
        method: 'GET',
        frequency: 100,
        commonParams: {
          limit: [10, 20, 50]
        },
        commonResponses: [
          {
            statusCode: 200,
            frequency: 0.95,
            responseTime: { avg: 50, p95: 100, p99: 150 }
          },
          {
            statusCode: 500,
            frequency: 0.05,
            responseTime: { avg: 100, p95: 200, p99: 300 }
          }
        ]
      },
      anomalies: [],
      lastUpdated: new Date()
    };
  });

  describe('generateAssertions', () => {
    it('should generate status code assertions', () => {
      const response = {
        status: 200,
        data: { users: [], total: 0 },
        responseTime: 45
      };

      const assertions = oracle.generateAssertions(sampleContract, response);
      const statusAssertion = assertions.find(a => a.type === 'status');

      expect(statusAssertion).toBeDefined();
      expect(statusAssertion?.expected).toEqual([200, 500]);
      expect(statusAssertion?.actual).toBe(200);
    });

    it('should generate timing assertions', () => {
      const response = {
        status: 200,
        data: { users: [], total: 0 },
        responseTime: 45
      };

      const assertions = oracle.generateAssertions(sampleContract, response);
      const timingAssertion = assertions.find(a => a.type === 'timing');

      expect(timingAssertion).toBeDefined();
      expect(timingAssertion?.expected).toBe(100); // p95
      expect(timingAssertion?.actual).toBe(45);
    });

    it('should generate schema validation assertions', () => {
      const response = {
        status: 200,
        data: {
          users: [{ id: '1', name: 'John' }],
          total: 1
        },
        responseTime: 50
      };

      const assertions = oracle.generateAssertions(sampleContract, response);
      const schemaAssertions = assertions.filter(a => a.type === 'schema');

      expect(schemaAssertions.length).toBeGreaterThan(0);
      expect(schemaAssertions.some(a => a.path === '' && a.expected === 'object')).toBe(true);
    });

    it('should detect high severity anomalies', () => {
      sampleContract.anomalies.push({
        type: 'performance_degradation',
        description: 'Response time degraded',
        severity: 'high',
        occurrences: 5,
        firstSeen: new Date(),
        lastSeen: new Date()
      });

      const response = {
        status: 200,
        data: { users: [], total: 0 },
        responseTime: 50
      };

      const assertions = oracle.generateAssertions(sampleContract, response);
      const anomalyAssertion = assertions.find(a => 
        a.type === 'contract' && a.message.includes('High severity anomaly')
      );

      expect(anomalyAssertion).toBeDefined();
    });
  });

  describe('generateTestData', () => {
    it('should generate test data from common values', () => {
      const testData = oracle.generateTestData(sampleContract);

      expect(testData.query).toBeDefined();
      expect([10, 20, 50]).toContain(testData.query.limit);
    });

    it('should generate request body from schema', () => {
      const contractWithBody: LearnedContract = {
        ...sampleContract,
        endpoint: '/users',
        method: 'POST',
        requestBody: {
          type: 'object',
          properties: {
            name: { type: 'string' },
            email: { type: 'string' },
            age: { type: 'integer', minimum: 0, maximum: 150 }
          },
          required: ['name', 'email']
        }
      };

      const testData = oracle.generateTestData(contractWithBody);

      expect(testData.body).toBeDefined();
      expect(testData.body.name).toBe('test-string');
      expect(testData.body.email).toBe('test-string');
      expect(typeof testData.body.age).toBe('number');
    });

    it('should handle path parameters', () => {
      const contractWithPath: LearnedContract = {
        ...sampleContract,
        endpoint: '/users/{id}',
        parameters: [
          {
            name: 'id',
            in: 'path',
            required: true,
            schema: { type: 'string' }
          }
        ],
        patterns: {
          ...sampleContract.patterns,
          commonParams: {
            id: ['1', '2', '3']
          }
        }
      };

      const testData = oracle.generateTestData(contractWithPath);

      expect(testData.path).toBeDefined();
      expect(['1', '2', '3']).toContain(testData.path.id);
    });
  });

  describe('evaluateAssertions', () => {
    it('should correctly evaluate passed assertions', () => {
      const assertions = [
        { type: 'status' as const, expected: [200, 201], actual: 200, message: 'Status OK' },
        { type: 'timing' as const, expected: 100, actual: 50, message: 'Response fast' },
        { type: 'schema' as const, expected: 'object', actual: 'object', message: 'Type OK' }
      ];

      const results = oracle.evaluateAssertions(assertions);

      expect(results.passed).toBe(3);
      expect(results.failed).toBe(0);
      expect(results.failures).toHaveLength(0);
    });

    it('should correctly evaluate failed assertions', () => {
      const assertions = [
        { type: 'status' as const, expected: [200, 201], actual: 500, message: 'Status failed' },
        { type: 'timing' as const, expected: 100, actual: 150, message: 'Too slow' },
        { type: 'schema' as const, expected: 'object', actual: 'string', message: 'Wrong type' }
      ];

      const results = oracle.evaluateAssertions(assertions);

      expect(results.passed).toBe(0);
      expect(results.failed).toBe(3);
      expect(results.failures).toHaveLength(3);
    });

    it('should handle comparison operators in value assertions', () => {
      const assertions = [
        { type: 'value' as const, expected: '>= 10', actual: 15, message: 'Min value' },
        { type: 'value' as const, expected: '<= 100', actual: 50, message: 'Max value' },
        { type: 'value' as const, expected: '>= 20', actual: 10, message: 'Below min' },
        { type: 'value' as const, expected: '<= 50', actual: 100, message: 'Above max' }
      ];

      const results = oracle.evaluateAssertions(assertions);

      expect(results.passed).toBe(2);
      expect(results.failed).toBe(2);
      expect(results.failures).toHaveLength(2);
      expect(results.failures[0].message).toBe('Below min');
      expect(results.failures[1].message).toBe('Above max');
    });
  });
});