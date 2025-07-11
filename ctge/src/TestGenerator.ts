import { TestScenario, GeneratedTest, NLPResult, TestStep, APIContext } from './types';
import { OpenAI } from 'openai';

export class TestGenerator {
  private openai: OpenAI | null = null;
  private templates: Map<string, string> = new Map();

  constructor(private openaiApiKey?: string) {
    if (openaiApiKey) {
      this.openai = new OpenAI({ apiKey: openaiApiKey });
    }
    this.initializeTemplates();
  }

  private initializeTemplates() {
    // JavaScript/Jest template
    this.templates.set('javascript-jest', `
describe('{{description}}', () => {
  {{setup}}
  
  {{tests}}
  
  {{teardown}}
});
`);

    // Python/pytest template
    this.templates.set('python-pytest', `
import pytest
import requests

class Test{{className}}:
    {{setup}}
    
    {{tests}}
    
    {{teardown}}
`);

    // TypeScript/Jest template
    this.templates.set('typescript-jest', `
import axios from 'axios';

describe('{{description}}', () => {
  {{setup}}
  
  {{tests}}
  
  {{teardown}}
});
`);
  }

  async generateFromScenario(
    scenario: TestScenario,
    language: GeneratedTest['language'] = 'javascript',
    context?: APIContext
  ): Promise<GeneratedTest> {
    const framework = this.getFramework(language);
    const code = await this.generateTestCode(scenario, language, framework, context);
    const dependencies = this.getDependencies(language, framework);

    return {
      language,
      framework,
      code,
      dependencies,
      setupInstructions: this.getSetupInstructions(language, framework)
    };
  }

  private getFramework(language: GeneratedTest['language']): string {
    const frameworkMap = {
      javascript: 'jest',
      typescript: 'jest',
      python: 'pytest',
      java: 'junit5'
    };
    return frameworkMap[language];
  }

  private async generateTestCode(
    scenario: TestScenario,
    language: GeneratedTest['language'],
    framework: string,
    context?: APIContext
  ): Promise<string> {
    if (this.openai) {
      // Use AI for more sophisticated code generation
      return await this.generateWithAI(scenario, language, framework, context);
    } else {
      // Use template-based generation
      return this.generateWithTemplates(scenario, language, framework, context);
    }
  }

  private async generateWithAI(
    scenario: TestScenario,
    language: GeneratedTest['language'],
    framework: string,
    context?: APIContext
  ): Promise<string> {
    if (!this.openai) throw new Error('OpenAI not initialized');

    const prompt = `Generate a ${language} test using ${framework} framework for the following scenario:

Scenario: ${scenario.description}

Steps:
${scenario.steps.map((step, i) => `${i + 1}. ${this.stepToString(step)}`).join('\n')}

Assertions:
${scenario.assertions.map((a, i) => `${i + 1}. ${a}`).join('\n')}

Context:
- Base URL: ${context?.baseUrl || 'http://localhost:3000'}
- Authentication: ${context?.authentication?.type || 'none'}

Generate clean, readable test code with proper error handling and assertions.`;

    const completion = await this.openai.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [{ role: "user", content: prompt }],
      max_tokens: 1500
    });

    return completion.choices[0]?.message?.content || this.generateWithTemplates(scenario, language, framework, context);
  }

  private generateWithTemplates(
    scenario: TestScenario,
    language: GeneratedTest['language'],
    framework: string,
    context?: APIContext
  ): string {
    const templateKey = `${language}-${framework}`;
    let template = this.templates.get(templateKey) || '';

    // Generate test code based on language
    switch (language) {
      case 'javascript':
      case 'typescript':
        return this.generateJavaScriptTest(scenario, context, language);
      case 'python':
        return this.generatePythonTest(scenario, context);
      case 'java':
        return this.generateJavaTest(scenario, context);
      default:
        return '// Test generation not supported for this language';
    }
  }

  private generateJavaScriptTest(
    scenario: TestScenario,
    context?: APIContext,
    language: 'javascript' | 'typescript' = 'javascript'
  ): string {
    const useAxios = language === 'typescript';
    const importStatement = useAxios 
      ? "import axios from 'axios';" 
      : "const axios = require('axios');";

    let code = `${importStatement}

describe('${scenario.description}', () => {
  const baseURL = '${context?.baseUrl || 'http://localhost:3000'}';
  let authToken${language === 'typescript' ? ': string' : ''};

`;

    // Add setup if needed
    const setupSteps = scenario.steps.filter(s => s.action === 'setup');
    if (setupSteps.length > 0) {
      code += `  beforeAll(async () => {\n`;
      setupSteps.forEach(step => {
        code += `    // ${step.details.description || 'Setup'}\n`;
        if (step.details.description?.includes('auth')) {
          code += `    authToken = 'test-token'; // TODO: Implement actual auth\n`;
        }
      });
      code += `  });\n\n`;
    }

    // Generate test cases
    const requestSteps = scenario.steps.filter(s => s.action === 'request');
    requestSteps.forEach((step, index) => {
      const testName = step.details.description || `Test ${index + 1}`;
      code += `  test('${testName}', async () => {\n`;
      
      // Generate request
      const method = (step.details.method || 'GET').toLowerCase();
      const endpoint = step.details.endpoint || '/';
      
      code += `    const response = await axios.${method}(\`\${baseURL}${endpoint}\``;
      
      if (step.details.body) {
        code += `, ${JSON.stringify(step.details.body, null, 6).split('\n').join('\n    ')}`;
      }
      
      // Add config
      const hasParams = step.details.params;
      const hasHeaders = step.details.headers || context?.authentication;
      
      if (hasParams || hasHeaders) {
        const config${language === 'typescript' ? ': any' : ''} = {};
        if (hasParams) config.params = step.details.params;
        if (hasHeaders || context?.authentication) {
          config.headers = {
            ...step.details.headers,
            ...(context?.authentication?.type === 'bearer' ? { Authorization: `Bearer \${authToken}` } : {})
          };
        }
        code += `, ${JSON.stringify(config, null, 6).split('\n').join('\n    ')}`;
      }
      
      code += `);\n\n`;
      
      // Add assertions
      scenario.assertions.forEach(assertion => {
        code += `    // ${assertion}\n`;
        if (assertion.includes('status')) {
          code += `    expect(response.status).toBe(${step.details.expected?.status || 200});\n`;
        }
        if (assertion.includes('response') || assertion.includes('data')) {
          code += `    expect(response.data).toBeDefined();\n`;
          if (step.details.expected?.data) {
            code += `    expect(response.data).toMatchObject(${JSON.stringify(step.details.expected.data, null, 6).split('\n').join('\n    ')});\n`;
          }
        }
      });
      
      code += `  });\n\n`;
    });

    code += `});`;

    return code;
  }

  private generatePythonTest(scenario: TestScenario, context?: APIContext): string {
    let code = `import pytest
import requests
import json

class Test${this.toCamelCase(scenario.description)}:
    BASE_URL = "${context?.baseUrl || 'http://localhost:3000'}"
    
`;

    // Add setup
    const setupSteps = scenario.steps.filter(s => s.action === 'setup');
    if (setupSteps.length > 0) {
      code += `    @pytest.fixture(scope="class", autouse=True)\n`;
      code += `    def setup(self):\n`;
      setupSteps.forEach(step => {
        code += `        # ${step.details.description || 'Setup'}\n`;
        if (step.details.description?.includes('auth')) {
          code += `        self.auth_token = 'test-token'  # TODO: Implement actual auth\n`;
        }
      });
      code += `        yield\n`;
      code += `        # Teardown if needed\n\n`;
    }

    // Generate test methods
    const requestSteps = scenario.steps.filter(s => s.action === 'request');
    requestSteps.forEach((step, index) => {
      const testName = this.toSnakeCase(step.details.description || `test_${index + 1}`);
      code += `    def ${testName}(self):\n`;
      
      // Generate request
      const method = (step.details.method || 'GET').lower();
      const endpoint = step.details.endpoint || '/';
      
      code += `        response = requests.${method}(\n`;
      code += `            f"{self.BASE_URL}${endpoint}"`;
      
      if (step.details.body) {
        code += `,\n            json=${JSON.stringify(step.details.body, null, 12).split('\n').join('\n            ')}`;
      }
      
      if (step.details.params) {
        code += `,\n            params=${JSON.stringify(step.details.params, null, 12).split('\n').join('\n            ')}`;
      }
      
      if (step.details.headers || context?.authentication) {
        const headers = {
          ...step.details.headers,
          ...(context?.authentication?.type === 'bearer' ? { Authorization: 'Bearer {self.auth_token}' } : {})
        };
        code += `,\n            headers=${JSON.stringify(headers, null, 12).split('\n').join('\n            ')}`;
      }
      
      code += `\n        )\n\n`;
      
      // Add assertions
      scenario.assertions.forEach(assertion => {
        code += `        # ${assertion}\n`;
        if (assertion.includes('status')) {
          code += `        assert response.status_code == ${step.details.expected?.status || 200}\n`;
        }
        if (assertion.includes('response') || assertion.includes('data')) {
          code += `        response_data = response.json()\n`;
          code += `        assert response_data is not None\n`;
          if (step.details.expected?.data) {
            Object.entries(step.details.expected.data).forEach(([key, value]) => {
              code += `        assert response_data.get("${key}") == ${JSON.stringify(value)}\n`;
            });
          }
        }
      });
      
      code += `\n`;
    });

    return code;
  }

  private generateJavaTest(scenario: TestScenario, context?: APIContext): string {
    // Simplified Java test generation
    return `import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeAll;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

public class ${this.toCamelCase(scenario.description)}Test {
    private static final String BASE_URL = "${context?.baseUrl || 'http://localhost:3000'}";
    
    @BeforeAll
    public static void setup() {
        baseURI = BASE_URL;
    }
    
    @Test
    public void test${this.toCamelCase(scenario.description)}() {
        // TODO: Implement test
        given()
            .when()
            .get("/endpoint")
            .then()
            .statusCode(200);
    }
}`;
  }

  private stepToString(step: TestStep): string {
    switch (step.action) {
      case 'request':
        return `${step.details.method} ${step.details.endpoint} - ${step.details.description || 'API request'}`;
      case 'setup':
        return `Setup: ${step.details.description || 'Prepare test environment'}`;
      case 'teardown':
        return `Teardown: ${step.details.description || 'Clean up'}`;
      case 'assertion':
        return `Assert: ${step.details.description || 'Verify response'}`;
      default:
        return step.details.description || 'Unknown step';
    }
  }

  private getDependencies(language: GeneratedTest['language'], framework: string): string[] {
    const deps: { [key: string]: string[] } = {
      'javascript-jest': ['jest', 'axios'],
      'typescript-jest': ['jest', '@types/jest', 'typescript', 'ts-jest', 'axios', '@types/axios'],
      'python-pytest': ['pytest', 'requests'],
      'java-junit5': ['junit-jupiter', 'rest-assured']
    };
    
    return deps[`${language}-${framework}`] || [];
  }

  private getSetupInstructions(language: GeneratedTest['language'], framework: string): string {
    const instructions: { [key: string]: string } = {
      'javascript-jest': 'Run: npm install jest axios\nAdd to package.json scripts: "test": "jest"',
      'typescript-jest': 'Run: npm install jest @types/jest typescript ts-jest axios @types/axios\nCreate jest.config.js with ts-jest preset',
      'python-pytest': 'Run: pip install pytest requests\nExecute tests with: pytest',
      'java-junit5': 'Add dependencies to pom.xml or build.gradle\nRun with: mvn test or gradle test'
    };
    
    return instructions[`${language}-${framework}`] || 'Follow framework documentation for setup';
  }

  private toCamelCase(str: string): string {
    return str
      .replace(/[^a-zA-Z0-9]+(.)/g, (m, chr) => chr.toUpperCase())
      .replace(/^[a-z]/, (m) => m.toUpperCase());
  }

  private toSnakeCase(str: string): string {
    return str
      .replace(/[^a-zA-Z0-9]+/g, '_')
      .replace(/([a-z])([A-Z])/g, '$1_$2')
      .toLowerCase();
  }
}