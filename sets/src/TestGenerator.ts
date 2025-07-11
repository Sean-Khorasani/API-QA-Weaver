import { TestCase } from './types';
import { OpenAI } from 'openai';

export class TestGenerator {
  private openai: OpenAI | null = null;

  constructor(private openaiApiKey?: string) {
    if (openaiApiKey) {
      this.openai = new OpenAI({ apiKey: openaiApiKey });
    }
  }

  async generateTestCode(testCase: TestCase): Promise<string> {
    if (this.openai) {
      return await this.generateWithAI(testCase);
    } else {
      return this.generateWithTemplate(testCase);
    }
  }

  private async generateWithAI(testCase: TestCase): Promise<string> {
    if (!this.openai) return this.generateWithTemplate(testCase);

    try {
      const prompt = `Generate a Jest test for this API endpoint:
${JSON.stringify(testCase, null, 2)}

Requirements:
1. Use Jest and axios
2. Include all assertions from the test case
3. Add descriptive test names
4. Include proper error handling
5. Add edge case tests

Generate clean, production-ready test code.`;

      const completion = await this.openai.chat.completions.create({
        model: "gpt-3.5-turbo",
        messages: [{ role: "user", content: prompt }],
        max_tokens: 1500
      });

      return completion.choices[0]?.message?.content || this.generateWithTemplate(testCase);
    } catch (error) {
      console.error('AI generation failed:', error);
      return this.generateWithTemplate(testCase);
    }
  }

  private generateWithTemplate(testCase: TestCase): string {
    const endpoint = testCase.endpoint;
    const testName = testCase.name.replace(/[^a-zA-Z0-9 ]/g, '');
    
    let code = `const axios = require('axios');

describe('${testName}', () => {
  const baseURL = process.env.API_BASE_URL || 'http://localhost:3000';
  
  test('${testCase.name}', async () => {
    try {
`;

    // Generate request
    const method = endpoint.method.toLowerCase();
    let url = `\${baseURL}${endpoint.path}`;
    
    // Replace path parameters
    if (testCase.input.params) {
      Object.entries(testCase.input.params).forEach(([key, value]) => {
        url = url.replace(`{${key}}`, value as string);
      });
    }

    code += `      const response = await axios.${method}('${url}'`;
    
    // Add request body
    if (testCase.input.body) {
      code += `,\n        ${JSON.stringify(testCase.input.body, null, 8).split('\n').join('\n        ')}`;
    }
    
    // Add query parameters
    if (testCase.input.query) {
      const config = { params: testCase.input.query };
      code += `,\n        ${JSON.stringify(config, null, 8).split('\n').join('\n        ')}`;
    }
    
    code += `);\n\n`;

    // Add assertions
    testCase.assertions.forEach(assertion => {
      switch (assertion.type) {
        case 'status':
          code += `      expect(response.status).toBe(${assertion.expected});\n`;
          break;
        case 'schema':
          code += `      expect(typeof response.data).toBe('${assertion.expected}');\n`;
          break;
        case 'value':
          if (assertion.path) {
            code += `      expect(response.data${this.pathToAccessor(assertion.path)})`;
            if (assertion.operator === 'exists') {
              code += `.toBeDefined();\n`;
            } else {
              code += `.toBe(${JSON.stringify(assertion.expected)});\n`;
            }
          }
          break;
        case 'header':
          code += `      expect(response.headers['${assertion.expected}']).toBeDefined();\n`;
          break;
        case 'performance':
          code += `      // Performance assertion: Response time should be under ${assertion.expected}ms\n`;
          break;
      }
    });

    code += `    } catch (error) {
      if (error.response) {
        console.error('Response error:', error.response.data);
        console.error('Status:', error.response.status);
      }
      throw error;
    }
  });
`;

    // Add edge case tests
    code += this.generateEdgeCaseTests(testCase);

    code += `});\n`;

    return code;
  }

  private generateEdgeCaseTests(testCase: TestCase): string {
    const endpoint = testCase.endpoint;
    let edgeCases = '';

    // Invalid input test
    if (['POST', 'PUT', 'PATCH'].includes(endpoint.method)) {
      edgeCases += `
  test('${testCase.name} - Invalid Input', async () => {
    try {
      const response = await axios.${endpoint.method.toLowerCase()}(
        \`\${baseURL}${endpoint.path}\`,
        {} // Empty body
      );
      
      // Should not reach here
      expect(response.status).toBe(400);
    } catch (error) {
      expect(error.response.status).toBe(400);
      expect(error.response.data).toHaveProperty('error');
    }
  });
`;
    }

    // Not found test for GET/PUT/DELETE with ID
    if (endpoint.path.includes('{id}') && ['GET', 'PUT', 'DELETE'].includes(endpoint.method)) {
      edgeCases += `
  test('${testCase.name} - Not Found', async () => {
    try {
      const response = await axios.${endpoint.method.toLowerCase()}(
        \`\${baseURL}${endpoint.path.replace('{id}', '99999999')}\`
      );
      
      // Should not reach here for 404
      expect(response.status).toBe(404);
    } catch (error) {
      expect(error.response.status).toBe(404);
    }
  });
`;
    }

    // Authorization test
    edgeCases += `
  test('${testCase.name} - Unauthorized', async () => {
    try {
      const response = await axios.${endpoint.method.toLowerCase()}(
        \`\${baseURL}${endpoint.path}\`,
        ${testCase.input.body ? JSON.stringify(testCase.input.body) : 'undefined'},
        {
          headers: { 'Authorization': 'Bearer invalid-token' }
        }
      );
      
      // May succeed if endpoint doesn't require auth
      expect([200, 201, 204, 401]).toContain(response.status);
    } catch (error) {
      expect(error.response.status).toBe(401);
    }
  });
`;

    return edgeCases;
  }

  private pathToAccessor(path: string): string {
    // Convert path like "data.users[0].name" to proper accessor
    return path.split('.').map(part => {
      if (part.includes('[')) {
        return part;
      }
      return `.${part}`;
    }).join('');
  }

  async generateTestSuite(testCases: TestCase[]): Promise<string> {
    let suite = `const axios = require('axios');

// Auto-generated test suite
describe('API Test Suite', () => {
  const baseURL = process.env.API_BASE_URL || 'http://localhost:3000';
  
  beforeAll(() => {
    // Setup if needed
  });

  afterAll(() => {
    // Cleanup if needed
  });

`;

    // Group tests by endpoint
    const groupedTests = new Map<string, TestCase[]>();
    testCases.forEach(tc => {
      const key = tc.endpoint.path;
      if (!groupedTests.has(key)) {
        groupedTests.set(key, []);
      }
      groupedTests.get(key)!.push(tc);
    });

    // Generate tests for each group
    for (const [endpoint, tests] of groupedTests) {
      suite += `  describe('${endpoint}', () => {\n`;
      
      for (const test of tests) {
        const testCode = await this.generateTestCode(test);
        // Extract just the test content
        const match = testCode.match(/test\('.*?',.*?\n  \}\);/s);
        if (match) {
          suite += `    ${match[0]}\n\n`;
        }
      }
      
      suite += `  });\n\n`;
    }

    suite += `});\n`;

    return suite;
  }
}