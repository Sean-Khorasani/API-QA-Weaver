import { NLPProcessor } from '../src/NLPProcessor';

describe('NLPProcessor', () => {
  let processor: NLPProcessor;

  beforeEach(() => {
    processor = new NLPProcessor();
  });

  describe('intent classification', () => {
    it('should classify create intents correctly', async () => {
      const inputs = [
        'Create a new user',
        'Add a product to the catalog',
        'Insert a new record'
      ];

      for (const input of inputs) {
        const result = await processor.processInput(input);
        expect(result.intent).toBe('create');
      }
    });

    it('should classify read intents correctly', async () => {
      const inputs = [
        'Get all users',
        'Fetch product details',
        'List available items',
        'Search for customers'
      ];

      for (const input of inputs) {
        const result = await processor.processInput(input);
        expect(result.intent).toBe('read');
      }
    });

    it('should classify update intents correctly', async () => {
      const inputs = [
        'Update user profile',
        'Modify product price',
        'Edit customer information'
      ];

      for (const input of inputs) {
        const result = await processor.processInput(input);
        expect(result.intent).toBe('update');
      }
    });

    it('should classify validation intents correctly', async () => {
      const inputs = [
        'Validate email format',
        'Verify user input',
        'Check data correctness'
      ];

      for (const input of inputs) {
        const result = await processor.processInput(input);
        expect(result.intent).toBe('validate');
      }
    });
  });

  describe('entity extraction', () => {
    it('should extract resources correctly', async () => {
      const input = 'Create a new user account for the customer';
      const result = await processor.processInput(input);

      expect(result.entities.resources).toContain('user');
      expect(result.entities.resources).toContain('account');
      expect(result.entities.resources).toContain('customer');
    });

    it('should extract conditions correctly', async () => {
      const input = 'Get users when status is active and age is greater than 18';
      const result = await processor.processInput(input);

      expect(result.entities.conditions.length).toBeGreaterThan(0);
      expect(result.entities.conditions.some(c => c.includes('status'))).toBe(true);
    });

    it('should extract expectations correctly', async () => {
      const input = 'Create user and verify response should return 201 status';
      const result = await processor.processInput(input);

      expect(result.entities.expectations.length).toBeGreaterThan(0);
      expect(result.entities.expectations[0]).toContain('return 201 status');
    });

    it('should extract data values correctly', async () => {
      const input = 'Create user with email test@example.com and age 25';
      const result = await processor.processInput(input);

      expect(result.entities.data).toContainEqual({ type: 'email', value: 'test@example.com' });
      expect(result.entities.data).toContainEqual({ type: 'number', value: 25 });
    });
  });

  describe('edge case suggestions', () => {
    it('should suggest edge cases for create operations', async () => {
      const input = 'Create a new product';
      const result = await processor.processInput(input);

      expect(result.edgeCases.length).toBeGreaterThan(0);
      expect(result.edgeCases.some(e => e.type === 'missing')).toBe(true);
      expect(result.edgeCases.some(e => e.type === 'invalid')).toBe(true);
    });

    it('should suggest security edge cases', async () => {
      const input = 'Test security of login endpoint';
      const result = await processor.processInput(input);

      expect(result.edgeCases.some(e => e.type === 'injection')).toBe(true);
      expect(result.edgeCases.some(e => e.severity === 'high')).toBe(true);
    });

    it('should suggest performance edge cases', async () => {
      const input = 'Test API performance';
      const result = await processor.processInput(input);

      expect(result.edgeCases.length).toBeGreaterThan(0);
    });
  });

  describe('test description generation', () => {
    it('should generate clear test descriptions', async () => {
      const input = 'Create user when email is valid and return success';
      const result = await processor.processInput(input);
      const description = processor.generateTestDescription(result);

      expect(description).toContain('Create user');
      expect(description).toContain('when');
      expect(description).toContain('verify');
    });

    it('should handle multiple resources in description', async () => {
      const input = 'Update user and product information';
      const result = await processor.processInput(input);
      const description = processor.generateTestDescription(result);

      expect(description).toContain('user, product');
    });
  });
});