import { ConversationalEngine } from '../src/ConversationalEngine';
import { APIContext } from '../src/types';

describe('ConversationalEngine', () => {
  let engine: ConversationalEngine;
  let context: APIContext;

  beforeEach(() => {
    engine = new ConversationalEngine();
    context = {
      baseUrl: 'http://localhost:3000',
      authentication: {
        type: 'bearer'
      }
    };
  });

  describe('processUserInput', () => {
    it('should generate test scenario for create operation', async () => {
      const input = 'Create a new user with email test@example.com';
      const result = await engine.processUserInput(input, context);

      expect(result.scenario).toBeDefined();
      expect(result.scenario.steps.length).toBeGreaterThan(0);
      expect(result.scenario.steps[0].action).toBe('request');
      expect(result.scenario.steps[0].details.method).toBe('POST');
      expect(result.generatedTests.length).toBeGreaterThan(0);
    });

    it('should generate test scenario for read operation', async () => {
      const input = 'Get all users with pagination';
      const result = await engine.processUserInput(input, context);

      expect(result.scenario.steps[0].details.method).toBe('GET');
      expect(result.scenario.steps[0].details.params).toBeDefined();
      expect(result.scenario.assertions).toContain('Response status should be 200 (OK)');
    });

    it('should generate test scenario for validation testing', async () => {
      const input = 'Test user creation with invalid email format';
      const result = await engine.processUserInput(input, context);

      expect(result.scenario.description).toContain('Validate');
      expect(result.scenario.assertions).toContain('Response status should be 400 (Bad Request)');
    });

    it('should include edge case suggestions', async () => {
      const input = 'Create a product with price';
      const result = await engine.processUserInput(input, context);

      expect(result.suggestions.length).toBeGreaterThan(0);
      expect(result.suggestions.some(s => s.coverage.includes('boundary'))).toBe(true);
    });

    it('should generate tests in multiple languages', async () => {
      const input = 'Delete a user by ID';
      const result = await engine.processUserInput(input, context);

      expect(result.generatedTests.length).toBe(3); // JavaScript, Python, TypeScript
      expect(result.generatedTests.map(t => t.language)).toContain('javascript');
      expect(result.generatedTests.map(t => t.language)).toContain('python');
      expect(result.generatedTests.map(t => t.language)).toContain('typescript');
    });
  });

  describe('conversation management', () => {
    it('should maintain conversation history', async () => {
      await engine.processUserInput('Create a user', context);
      await engine.processUserInput('Now update that user', context);

      const history = engine.getConversationHistory();
      expect(history.length).toBe(4); // 2 user + 2 assistant
      expect(history[0].role).toBe('user');
      expect(history[1].role).toBe('assistant');
    });

    it('should clear conversation history', async () => {
      await engine.processUserInput('Test request', context);
      engine.clearConversation();

      const history = engine.getConversationHistory();
      expect(history.length).toBe(0);
    });
  });

  describe('edge cases', () => {
    it('should handle empty input gracefully', async () => {
      const result = await engine.processUserInput('', context);
      expect(result.scenario).toBeDefined();
      expect(result.scenario.steps.length).toBeGreaterThanOrEqual(0);
    });

    it('should handle complex multi-step requests', async () => {
      const input = 'First create a user, then update their email, and finally verify the change';
      const result = await engine.processUserInput(input, context);

      expect(result.scenario.steps.length).toBeGreaterThanOrEqual(1);
      expect(result.scenario.assertions.length).toBeGreaterThan(0);
    });

    it('should generate security test scenarios', async () => {
      const input = 'Test API security with invalid tokens';
      const result = await engine.processUserInput(input, context);

      expect(result.scenario.steps[0].details.headers).toBeDefined();
      expect(result.scenario.assertions).toContain('Response status should be 401 (Unauthorized)');
    });

    it('should generate performance test scenarios', async () => {
      const input = 'Test API performance with concurrent requests';
      const result = await engine.processUserInput(input, context);

      expect(result.scenario.steps.some(s => s.action === 'setup')).toBe(true);
      expect(result.scenario.assertions.some(a => a.includes('response time'))).toBe(true);
    });
  });
});