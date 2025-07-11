import { TestGenerator } from '../src/TestGenerator';
import { TestScenario, APIContext } from '../src/types';

describe('TestGenerator', () => {
  let generator: TestGenerator;
  let sampleScenario: TestScenario;
  let context: APIContext;

  beforeEach(() => {
    generator = new TestGenerator();
    context = {
      baseUrl: 'http://localhost:3000',
      authentication: {
        type: 'bearer'
      }
    };
    
    sampleScenario = {
      description: 'Test user creation',
      steps: [
        {
          action: 'request',
          details: {
            method: 'POST',
            endpoint: '/api/users',
            body: {
              name: 'John Doe',
              email: 'john@example.com'
            },
            description: 'Create new user',
            expected: {
              status: 201
            }
          }
        }
      ],
      assertions: [
        'Response status should be 201',
        'Response should contain user ID'
      ]
    };
  });

  describe('generateFromScenario', () => {
    it('should generate JavaScript test', async () => {
      const result = await generator.generateFromScenario(sampleScenario, 'javascript', context);

      expect(result.language).toBe('javascript');
      expect(result.framework).toBe('jest');
      expect(result.code).toContain('describe');
      expect(result.code).toContain('test');
      expect(result.code).toContain('axios');
      expect(result.code).toContain('expect');
      expect(result.dependencies).toContain('jest');
      expect(result.dependencies).toContain('axios');
    });

    it('should generate TypeScript test', async () => {
      const result = await generator.generateFromScenario(sampleScenario, 'typescript', context);

      expect(result.language).toBe('typescript');
      expect(result.code).toContain('import axios from');
      expect(result.code).toContain(': string');
      expect(result.dependencies).toContain('typescript');
      expect(result.dependencies).toContain('@types/jest');
    });

    it('should generate Python test', async () => {
      const result = await generator.generateFromScenario(sampleScenario, 'python', context);

      expect(result.language).toBe('python');
      expect(result.framework).toBe('pytest');
      expect(result.code).toContain('import pytest');
      expect(result.code).toContain('import requests');
      expect(result.code).toContain('class Test');
      expect(result.code).toContain('assert');
      expect(result.dependencies).toContain('pytest');
      expect(result.dependencies).toContain('requests');
    });

    it('should generate Java test', async () => {
      const result = await generator.generateFromScenario(sampleScenario, 'java', context);

      expect(result.language).toBe('java');
      expect(result.framework).toBe('junit5');
      expect(result.code).toContain('import org.junit.jupiter.api.Test');
      expect(result.code).toContain('public class');
      expect(result.dependencies).toContain('junit-jupiter');
    });
  });

  describe('authentication handling', () => {
    it('should include bearer token in JavaScript tests', async () => {
      const result = await generator.generateFromScenario(sampleScenario, 'javascript', context);

      expect(result.code).toContain('Authorization');
      expect(result.code).toContain('Bearer');
    });

    it('should include bearer token in Python tests', async () => {
      const result = await generator.generateFromScenario(sampleScenario, 'python', context);

      expect(result.code).toContain('Authorization');
      expect(result.code).toContain('Bearer');
    });
  });

  describe('complex scenarios', () => {
    it('should handle multiple test steps', async () => {
      const multiStepScenario: TestScenario = {
        description: 'Test user CRUD operations',
        steps: [
          {
            action: 'setup',
            details: {
              description: 'Authenticate user'
            }
          },
          {
            action: 'request',
            details: {
              method: 'POST',
              endpoint: '/api/users',
              body: { name: 'Test', email: 'test@example.com' },
              description: 'Create user'
            }
          },
          {
            action: 'request',
            details: {
              method: 'GET',
              endpoint: '/api/users/{id}',
              description: 'Retrieve created user'
            }
          }
        ],
        assertions: [
          'All requests should succeed',
          'Data should be consistent'
        ]
      };

      const result = await generator.generateFromScenario(multiStepScenario, 'javascript', context);

      expect(result.code).toContain('beforeAll');
      expect(result.code.match(/test\(/g)?.length).toBeGreaterThanOrEqual(2);
    });

    it('should handle query parameters', async () => {
      const scenarioWithParams: TestScenario = {
        description: 'Test user search',
        steps: [
          {
            action: 'request',
            details: {
              method: 'GET',
              endpoint: '/api/users',
              params: { limit: 10, offset: 0, filter: 'active' },
              description: 'Search users with filters'
            }
          }
        ],
        assertions: ['Response should contain filtered results']
      };

      const result = await generator.generateFromScenario(scenarioWithParams, 'javascript', context);

      expect(result.code).toContain('params');
      expect(result.code).toContain('limit');
      expect(result.code).toContain('filter');
    });
  });

  describe('setup instructions', () => {
    it('should provide setup instructions for each language', async () => {
      const languages: Array<'javascript' | 'python' | 'typescript' | 'java'> = 
        ['javascript', 'python', 'typescript', 'java'];

      for (const lang of languages) {
        const result = await generator.generateFromScenario(sampleScenario, lang, context);
        expect(result.setupInstructions).toBeDefined();
        expect(result.setupInstructions).not.toBe('');
      }
    });
  });
});