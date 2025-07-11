import { TestEvolver } from '../src/TestEvolver';
import { CodeChange, APIEndpoint } from '../src/types';

describe('TestEvolver', () => {
  let evolver: TestEvolver;

  beforeEach(() => {
    evolver = new TestEvolver();
  });

  describe('evolveTestSuite', () => {
    it('should create tests for new endpoints', async () => {
      const changes: CodeChange[] = [{
        file: 'api.js',
        type: 'modified',
        changes: [{
          type: 'endpoint',
          path: 'POST /api/users',
          after: {
            path: '/api/users',
            method: 'POST'
          }
        }],
        timestamp: new Date()
      }];

      const evolution = await evolver.evolveTestSuite(changes, 50, 80);

      expect(evolution.changes.length).toBeGreaterThan(0);
      expect(evolution.changes[0].type).toBe('added');
      expect(evolution.changes[0].reason).toContain('New endpoint detected');
    });

    it('should remove tests for deleted endpoints', async () => {
      // First add a test
      const addChanges: CodeChange[] = [{
        file: 'api.js',
        type: 'modified',
        changes: [{
          type: 'endpoint',
          path: 'GET /api/test',
          after: { path: '/api/test', method: 'GET' }
        }],
        timestamp: new Date()
      }];
      
      await evolver.evolveTestSuite(addChanges, 50, 80);

      // Then remove the endpoint
      const removeChanges: CodeChange[] = [{
        file: 'api.js',
        type: 'modified',
        changes: [{
          type: 'endpoint',
          path: 'GET /api/test',
          before: { path: '/api/test', method: 'GET' }
        }],
        timestamp: new Date()
      }];

      const evolution = await evolver.evolveTestSuite(removeChanges, 70, 80);

      expect(evolution.changes.some(c => c.type === 'removed')).toBe(true);
    });

    it('should update tests for modified endpoints', async () => {
      // First add a test
      const endpoint: APIEndpoint = { path: '/api/users', method: 'GET' };
      const addChanges: CodeChange[] = [{
        file: 'api.js',
        type: 'modified',
        changes: [{
          type: 'endpoint',
          path: 'GET /api/users',
          after: endpoint
        }],
        timestamp: new Date()
      }];
      
      await evolver.evolveTestSuite(addChanges, 50, 80);

      // Then modify the endpoint
      const modifyChanges: CodeChange[] = [{
        file: 'api.js',
        type: 'modified',
        changes: [{
          type: 'endpoint',
          path: 'GET /api/users',
          before: endpoint,
          after: { ...endpoint, method: 'POST' }
        }],
        timestamp: new Date()
      }];

      const evolution = await evolver.evolveTestSuite(modifyChanges, 70, 80);

      expect(evolution.changes.some(c => c.type === 'updated')).toBe(true);
    });

    it('should generate additional tests to meet coverage target', async () => {
      const changes: CodeChange[] = [{
        file: 'api.js',
        type: 'modified',
        changes: [{
          type: 'endpoint',
          path: 'GET /api/products',
          after: { path: '/api/products', method: 'GET' }
        }],
        timestamp: new Date()
      }];

      const evolution = await evolver.evolveTestSuite(changes, 30, 80);

      expect(evolution.coverage.after).toBeGreaterThan(evolution.coverage.before);
      expect(evolution.reason).toContain('Evolving test suite');
    });
  });

  describe('test case management', () => {
    it('should export and import tests', async () => {
      // Add some tests
      const changes: CodeChange[] = [{
        file: 'api.js',
        type: 'modified',
        changes: [{
          type: 'endpoint',
          path: 'GET /api/test',
          after: { path: '/api/test', method: 'GET' }
        }],
        timestamp: new Date()
      }];
      
      await evolver.evolveTestSuite(changes, 50, 80);

      // Mock file operations
      const mockWrite = jest.fn();
      const mockRead = jest.fn().mockReturnValue('[]');
      jest.spyOn(require('fs'), 'writeFileSync').mockImplementation(mockWrite);
      jest.spyOn(require('fs'), 'readFileSync').mockImplementation(mockRead);

      // Export
      evolver.exportTests('/tmp/tests.json');
      expect(mockWrite).toHaveBeenCalled();

      // Import
      evolver.importTests('/tmp/tests.json');
      expect(mockRead).toHaveBeenCalled();
    });

    it('should track evolution history', async () => {
      const changes: CodeChange[] = [{
        file: 'api.js',
        type: 'modified',
        changes: [{
          type: 'endpoint',
          path: 'POST /api/users',
          after: { path: '/api/users', method: 'POST' }
        }],
        timestamp: new Date()
      }];

      await evolver.evolveTestSuite(changes, 50, 80);
      await evolver.evolveTestSuite(changes, 60, 80);

      const history = evolver.getEvolutionHistory();
      expect(history).toHaveLength(2);
      expect(history[0].version).toBeDefined();
      expect(history[0].timestamp).toBeDefined();
    });

    it('should return all test cases', async () => {
      const changes: CodeChange[] = [{
        file: 'api.js',
        type: 'modified',
        changes: [
          {
            type: 'endpoint',
            path: 'GET /api/users',
            after: { path: '/api/users', method: 'GET' }
          },
          {
            type: 'endpoint',
            path: 'POST /api/users',
            after: { path: '/api/users', method: 'POST' }
          }
        ],
        timestamp: new Date()
      }];

      await evolver.evolveTestSuite(changes, 50, 80);

      const testCases = evolver.getTestCases();
      expect(testCases.length).toBeGreaterThanOrEqual(2);
      expect(testCases[0].id).toBeDefined();
      expect(testCases[0].endpoint).toBeDefined();
    });
  });
});