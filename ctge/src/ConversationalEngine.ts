import { NLPProcessor } from './NLPProcessor';
import { TestGenerator } from './TestGenerator';
import { TestScenario, GeneratedTest, APIContext, TestStep, TestSuggestion } from './types';
import { OpenAI } from 'openai';

export class ConversationalEngine {
  private nlpProcessor: NLPProcessor;
  private testGenerator: TestGenerator;
  private openai: OpenAI | null = null;
  private conversationHistory: { role: 'user' | 'assistant'; content: string }[] = [];

  constructor(private openaiApiKey?: string) {
    this.nlpProcessor = new NLPProcessor();
    this.testGenerator = new TestGenerator(openaiApiKey);
    
    if (openaiApiKey) {
      this.openai = new OpenAI({ apiKey: openaiApiKey });
    }
  }

  async processUserInput(
    input: string,
    context?: APIContext
  ): Promise<{
    scenario: TestScenario;
    generatedTests: GeneratedTest[];
    suggestions: TestSuggestion[];
  }> {
    // Add to conversation history
    this.conversationHistory.push({ role: 'user', content: input });

    // Process with NLP
    const nlpResult = await this.nlpProcessor.processInput(input);
    
    // Create test scenario
    const scenario = await this.createTestScenario(input, nlpResult);
    
    // Generate tests in multiple languages
    const generatedTests = await this.generateTests(scenario, context);
    
    // Generate suggestions for additional tests
    const suggestions = await this.generateSuggestions(scenario, nlpResult);

    // Add assistant response to history
    const response = `Generated ${generatedTests.length} test implementations with ${suggestions.length} additional suggestions.`;
    this.conversationHistory.push({ role: 'assistant', content: response });

    return {
      scenario,
      generatedTests,
      suggestions
    };
  }

  private async createTestScenario(input: string, nlpResult: any): Promise<TestScenario> {
    const steps: TestStep[] = [];
    const assertions: string[] = [];

    // Create request steps based on intent
    switch (nlpResult.intent) {
      case 'create':
        steps.push({
          action: 'request',
          details: {
            method: 'POST',
            endpoint: this.inferEndpoint(nlpResult.entities.resources),
            body: this.inferRequestBody(nlpResult.entities),
            description: `Create new ${nlpResult.entities.resources[0] || 'resource'}`
          }
        });
        assertions.push('Response status should be 201 (Created)');
        assertions.push('Response should contain the created resource with an ID');
        break;

      case 'read':
        steps.push({
          action: 'request',
          details: {
            method: 'GET',
            endpoint: this.inferEndpoint(nlpResult.entities.resources),
            params: this.inferQueryParams(nlpResult.entities),
            description: `Retrieve ${nlpResult.entities.resources[0] || 'resources'}`
          }
        });
        assertions.push('Response status should be 200 (OK)');
        assertions.push('Response should contain the requested data');
        break;

      case 'update':
        steps.push({
          action: 'request',
          details: {
            method: 'PUT',
            endpoint: this.inferEndpoint(nlpResult.entities.resources, true),
            body: this.inferRequestBody(nlpResult.entities),
            description: `Update existing ${nlpResult.entities.resources[0] || 'resource'}`
          }
        });
        assertions.push('Response status should be 200 (OK)');
        assertions.push('Response should contain the updated resource');
        break;

      case 'delete':
        steps.push({
          action: 'request',
          details: {
            method: 'DELETE',
            endpoint: this.inferEndpoint(nlpResult.entities.resources, true),
            description: `Delete ${nlpResult.entities.resources[0] || 'resource'}`
          }
        });
        assertions.push('Response status should be 204 (No Content)');
        break;

      case 'validate':
        // Add validation-specific steps
        steps.push({
          action: 'request',
          details: {
            method: 'POST',
            endpoint: this.inferEndpoint(nlpResult.entities.resources),
            body: { invalid: 'data' },
            description: 'Send invalid data to test validation'
          }
        });
        assertions.push('Response status should be 400 (Bad Request)');
        assertions.push('Response should contain validation error messages');
        break;

      case 'performance':
        steps.push({
          action: 'setup',
          details: {
            description: 'Prepare performance test environment'
          }
        });
        steps.push({
          action: 'request',
          details: {
            method: 'GET',
            endpoint: this.inferEndpoint(nlpResult.entities.resources),
            description: 'Execute performance test'
          }
        });
        assertions.push('Response time should be under 200ms');
        assertions.push('Server should handle concurrent requests');
        break;

      case 'security':
        steps.push({
          action: 'request',
          details: {
            method: 'GET',
            endpoint: this.inferEndpoint(nlpResult.entities.resources),
            headers: { Authorization: 'Invalid Token' },
            description: 'Test with invalid authentication'
          }
        });
        assertions.push('Response status should be 401 (Unauthorized)');
        assertions.push('Response should not leak sensitive information');
        break;
    }

    // Add custom expectations from NLP
    nlpResult.entities.expectations.forEach(exp => {
      assertions.push(exp);
    });

    // Use AI to enhance scenario if available
    if (this.openai) {
      const enhanced = await this.enhanceScenarioWithAI(input, steps, assertions);
      return enhanced;
    }

    return {
      description: this.nlpProcessor.generateTestDescription(nlpResult),
      steps,
      assertions,
      metadata: {
        priority: this.inferPriority(nlpResult),
        category: nlpResult.intent,
        tags: nlpResult.entities.resources
      }
    };
  }

  private async enhanceScenarioWithAI(
    input: string,
    steps: TestStep[],
    assertions: string[]
  ): Promise<TestScenario> {
    if (!this.openai) {
      return {
        description: input,
        steps,
        assertions
      };
    }

    try {
      const prompt = `Given this test request: "${input}"
      
Current steps: ${JSON.stringify(steps, null, 2)}
Current assertions: ${JSON.stringify(assertions, null, 2)}

Enhance this test scenario by:
1. Adding any missing test steps
2. Including edge cases
3. Adding comprehensive assertions
4. Providing a clear test description

Return a JSON object with: description, steps (array), assertions (array)`;

      const completion = await this.openai.chat.completions.create({
        model: "gpt-3.5-turbo",
        messages: [{ role: "user", content: prompt }],
        max_tokens: 1000
      });

      const enhanced = JSON.parse(completion.choices[0]?.message?.content || '{}');
      
      return {
        description: enhanced.description || input,
        steps: enhanced.steps || steps,
        assertions: enhanced.assertions || assertions,
        metadata: {
          priority: 'medium',
          category: 'ai-enhanced'
        }
      };
    } catch (error) {
      // Fallback to original if AI fails
      return {
        description: input,
        steps,
        assertions
      };
    }
  }

  private async generateTests(
    scenario: TestScenario,
    context?: APIContext
  ): Promise<GeneratedTest[]> {
    const languages: GeneratedTest['language'][] = ['javascript', 'python', 'typescript'];
    const tests: GeneratedTest[] = [];

    for (const language of languages) {
      const test = await this.testGenerator.generateFromScenario(scenario, language, context);
      tests.push(test);
    }

    return tests;
  }

  private async generateSuggestions(
    scenario: TestScenario,
    nlpResult: any
  ): Promise<TestSuggestion[]> {
    const suggestions: TestSuggestion[] = [];

    // Add edge case suggestions
    nlpResult.edgeCases.forEach(edge => {
      suggestions.push({
        scenario: edge.description,
        rationale: edge.suggestion,
        coverage: [edge.type]
      });
    });

    // Add standard test suggestions based on intent
    switch (nlpResult.intent) {
      case 'create':
        suggestions.push(
          {
            scenario: 'Test duplicate creation prevention',
            rationale: 'Ensure the system prevents creating duplicate resources with the same unique fields',
            coverage: ['business-logic', 'data-integrity']
          },
          {
            scenario: 'Test resource creation with minimal data',
            rationale: 'Verify that resources can be created with only required fields',
            coverage: ['api-contract', 'validation']
          }
        );
        break;

      case 'read':
        suggestions.push(
          {
            scenario: 'Test filtering and sorting capabilities',
            rationale: 'Ensure data can be filtered and sorted according to API documentation',
            coverage: ['functionality', 'performance']
          },
          {
            scenario: 'Test response caching behavior',
            rationale: 'Verify that appropriate cache headers are set for read operations',
            coverage: ['performance', 'http-compliance']
          }
        );
        break;

      case 'update':
        suggestions.push(
          {
            scenario: 'Test partial updates (PATCH)',
            rationale: 'Verify that partial updates only modify specified fields',
            coverage: ['functionality', 'data-integrity']
          },
          {
            scenario: 'Test optimistic locking',
            rationale: 'Ensure concurrent updates are handled properly',
            coverage: ['concurrency', 'data-integrity']
          }
        );
        break;
    }

    // Add performance and security suggestions if not already covered
    if (nlpResult.intent !== 'performance') {
      suggestions.push({
        scenario: 'Load test with concurrent requests',
        rationale: 'Ensure the API can handle expected load',
        coverage: ['performance', 'scalability']
      });
    }

    if (nlpResult.intent !== 'security') {
      suggestions.push({
        scenario: 'Test authorization boundaries',
        rationale: 'Verify users can only access their own resources',
        coverage: ['security', 'authorization']
      });
    }

    return suggestions;
  }

  private inferEndpoint(resources: string[], includeId: boolean = false): string {
    if (resources.length === 0) return '/api/resources';
    
    const resource = resources[0];
    const plural = resource.endsWith('s') ? resource : `${resource}s`;
    const endpoint = `/api/${plural}`;
    
    return includeId ? `${endpoint}/{id}` : endpoint;
  }

  private inferRequestBody(entities: any): any {
    const body: any = {};
    
    // Add common fields based on resource type
    if (entities.resources.includes('user') || entities.resources.includes('account')) {
      body.name = 'Test User';
      body.email = 'test@example.com';
    } else if (entities.resources.includes('product')) {
      body.name = 'Test Product';
      body.price = 99.99;
    } else {
      body.name = 'Test Resource';
    }

    // Add any extracted data
    entities.data.forEach(item => {
      if (item.type === 'email') {
        body.email = item.value;
      } else if (item.type === 'string' && !body.name) {
        body.name = item.value;
      }
    });

    return body;
  }

  private inferQueryParams(entities: any): any {
    const params: any = {};
    
    // Add common query parameters
    if (entities.conditions.some(c => c.includes('limit') || c.includes('page'))) {
      params.limit = 10;
      params.offset = 0;
    }

    // Extract specific values
    entities.data.forEach(item => {
      if (item.type === 'number') {
        if (!params.limit) params.limit = item.value;
      }
    });

    return Object.keys(params).length > 0 ? params : undefined;
  }

  private inferPriority(nlpResult: any): 'high' | 'medium' | 'low' {
    if (nlpResult.intent === 'security') return 'high';
    if (nlpResult.intent === 'create' || nlpResult.intent === 'delete') return 'high';
    if (nlpResult.edgeCases.some(e => e.severity === 'high')) return 'high';
    if (nlpResult.intent === 'performance') return 'medium';
    return 'medium';
  }

  getConversationHistory(): { role: 'user' | 'assistant'; content: string }[] {
    return this.conversationHistory;
  }

  clearConversation(): void {
    this.conversationHistory = [];
  }
}