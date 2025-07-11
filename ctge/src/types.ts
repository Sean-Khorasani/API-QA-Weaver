export interface TestScenario {
  description: string;
  steps: TestStep[];
  assertions: string[];
  metadata?: {
    priority?: 'high' | 'medium' | 'low';
    category?: string;
    tags?: string[];
  };
}

export interface TestStep {
  action: 'request' | 'setup' | 'teardown' | 'assertion';
  details: StepDetails;
}

export interface StepDetails {
  method?: string;
  endpoint?: string;
  params?: any;
  headers?: any;
  body?: any;
  description?: string;
  expected?: any;
}

export interface GeneratedTest {
  language: 'javascript' | 'python' | 'java' | 'typescript';
  framework: string;
  code: string;
  dependencies: string[];
  setupInstructions?: string;
}

export interface NLPResult {
  intent: 'create' | 'read' | 'update' | 'delete' | 'search' | 'validate' | 'performance' | 'security';
  entities: {
    resources: string[];
    conditions: string[];
    expectations: string[];
    data: any[];
  };
  edgeCases: EdgeCase[];
}

export interface EdgeCase {
  type: 'boundary' | 'invalid' | 'missing' | 'malformed' | 'injection' | 'overflow';
  description: string;
  suggestion: string;
  severity: 'high' | 'medium' | 'low';
}

export interface TestSuggestion {
  scenario: string;
  rationale: string;
  coverage: string[];
}

export interface APIContext {
  baseUrl?: string;
  authentication?: {
    type: 'bearer' | 'basic' | 'apikey' | 'oauth2';
    credentials?: any;
  };
  headers?: { [key: string]: string };
  timeout?: number;
}