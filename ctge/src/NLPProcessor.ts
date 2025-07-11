import natural from 'natural';
import { NLPResult, EdgeCase } from './types';

export class NLPProcessor {
  private tokenizer: natural.WordTokenizer;
  private tfidf: natural.TfIdf;
  private classifier: natural.BayesClassifier;

  constructor() {
    this.tokenizer = new natural.WordTokenizer();
    this.tfidf = new natural.TfIdf();
    this.classifier = new natural.BayesClassifier();
    
    this.trainClassifier();
  }

  private trainClassifier() {
    // Train intent classifier
    this.classifier.addDocument('create new user account registration', 'create');
    this.classifier.addDocument('add insert post new record', 'create');
    this.classifier.addDocument('get fetch retrieve find show', 'read');
    this.classifier.addDocument('list all users search query', 'read');
    this.classifier.addDocument('update modify change edit patch', 'update');
    this.classifier.addDocument('delete remove destroy purge', 'delete');
    this.classifier.addDocument('validate verify check ensure correct', 'validate');
    this.classifier.addDocument('performance speed fast slow response time', 'performance');
    this.classifier.addDocument('security authentication authorization injection xss', 'security');
    
    this.classifier.train();
  }

  async processInput(input: string): Promise<NLPResult> {
    const tokens = this.tokenizer.tokenize(input.toLowerCase());
    const intent = this.classifier.classify(input) as NLPResult['intent'];
    
    // Extract entities
    const resources = this.extractResources(input);
    const conditions = this.extractConditions(input);
    const expectations = this.extractExpectations(input);
    const data = this.extractData(input);
    
    // Suggest edge cases
    const edgeCases = this.suggestEdgeCases(intent, resources);
    
    return {
      intent,
      entities: {
        resources,
        conditions,
        expectations,
        data
      },
      edgeCases
    };
  }

  private extractResources(input: string): string[] {
    const resources: string[] = [];
    const resourcePatterns = [
      /\b(user|users|account|accounts|product|products|order|orders|item|items|customer|customers)\b/gi,
      /\b(api|endpoint|service|resource|entity|object|record|document)\b/gi
    ];
    
    resourcePatterns.forEach(pattern => {
      const matches = input.match(pattern);
      if (matches) {
        resources.push(...matches.map(m => m.toLowerCase()));
      }
    });
    
    return [...new Set(resources)];
  }

  private extractConditions(input: string): string[] {
    const conditions: string[] = [];
    const conditionPatterns = [
      /when\s+([^,\.]+)/gi,
      /if\s+([^,\.]+)/gi,
      /with\s+([^,\.]+)/gi,
      /where\s+([^,\.]+)/gi,
      /having\s+([^,\.]+)/gi
    ];
    
    conditionPatterns.forEach(pattern => {
      const matches = input.matchAll(pattern);
      for (const match of matches) {
        conditions.push(match[1].trim());
      }
    });
    
    return conditions;
  }

  private extractExpectations(input: string): string[] {
    const expectations: string[] = [];
    const expectationPatterns = [
      /should\s+([^,\.]+)/gi,
      /must\s+([^,\.]+)/gi,
      /expect\s+([^,\.]+)/gi,
      /verify\s+([^,\.]+)/gi,
      /ensure\s+([^,\.]+)/gi,
      /check\s+([^,\.]+)/gi,
      /return\s+([^,\.]+)/gi
    ];
    
    expectationPatterns.forEach(pattern => {
      const matches = input.matchAll(pattern);
      for (const match of matches) {
        expectations.push(match[1].trim());
      }
    });
    
    return expectations;
  }

  private extractData(input: string): any[] {
    const data: any[] = [];
    
    // Extract email patterns
    const emailPattern = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
    const emails = input.match(emailPattern);
    if (emails) data.push(...emails.map(e => ({ type: 'email', value: e })));
    
    // Extract numbers
    const numberPattern = /\b\d+\b/g;
    const numbers = input.match(numberPattern);
    if (numbers) data.push(...numbers.map(n => ({ type: 'number', value: parseInt(n) })));
    
    // Extract quoted strings
    const quotedPattern = /"([^"]*)"|'([^']*)'/g;
    const quoted = input.matchAll(quotedPattern);
    for (const match of quoted) {
      data.push({ type: 'string', value: match[1] || match[2] });
    }
    
    return data;
  }

  private suggestEdgeCases(intent: NLPResult['intent'], resources: string[]): EdgeCase[] {
    const edgeCases: EdgeCase[] = [];
    
    switch (intent) {
      case 'create':
        edgeCases.push(
          {
            type: 'missing',
            description: 'Test with missing required fields',
            suggestion: 'Try creating without mandatory fields like email or name',
            severity: 'high'
          },
          {
            type: 'invalid',
            description: 'Test with invalid data formats',
            suggestion: 'Use malformed email, negative age, or special characters in names',
            severity: 'medium'
          },
          {
            type: 'boundary',
            description: 'Test field length boundaries',
            suggestion: 'Try maximum length strings, minimum values, or empty strings',
            severity: 'medium'
          }
        );
        break;
        
      case 'read':
        edgeCases.push(
          {
            type: 'missing',
            description: 'Test with non-existent resources',
            suggestion: 'Query for IDs that don\'t exist',
            severity: 'medium'
          },
          {
            type: 'boundary',
            description: 'Test pagination limits',
            suggestion: 'Try extreme limit values (0, negative, very large)',
            severity: 'low'
          }
        );
        break;
        
      case 'update':
      case 'delete':
        edgeCases.push(
          {
            type: 'missing',
            description: 'Test operations on non-existent resources',
            suggestion: 'Try to update/delete using invalid IDs',
            severity: 'high'
          },
          {
            type: 'invalid',
            description: 'Test concurrent modifications',
            suggestion: 'Simulate race conditions with multiple updates',
            severity: 'medium'
          }
        );
        break;
        
      case 'security':
        edgeCases.push(
          {
            type: 'injection',
            description: 'Test SQL/NoSQL injection vulnerabilities',
            suggestion: 'Include SQL keywords or special characters in inputs',
            severity: 'high'
          },
          {
            type: 'overflow',
            description: 'Test buffer overflow scenarios',
            suggestion: 'Send extremely large payloads',
            severity: 'high'
          }
        );
        break;
    }
    
    // Add general edge cases
    if (resources.length > 0) {
      edgeCases.push({
        type: 'malformed',
        description: 'Test with malformed JSON/XML payloads',
        suggestion: 'Send requests with syntax errors or wrong content-types',
        severity: 'medium'
      });
    }
    
    return edgeCases;
  }

  generateTestDescription(nlpResult: NLPResult): string {
    const { intent, entities } = nlpResult;
    let description = '';
    
    switch (intent) {
      case 'create':
        description = `Create ${entities.resources.join(', ')}`;
        break;
      case 'read':
        description = `Retrieve ${entities.resources.join(', ')}`;
        break;
      case 'update':
        description = `Update ${entities.resources.join(', ')}`;
        break;
      case 'delete':
        description = `Delete ${entities.resources.join(', ')}`;
        break;
      case 'validate':
        description = `Validate ${entities.resources.join(', ')}`;
        break;
      case 'performance':
        description = `Test performance of ${entities.resources.join(', ')}`;
        break;
      case 'security':
        description = `Test security of ${entities.resources.join(', ')}`;
        break;
    }
    
    if (entities.conditions.length > 0) {
      description += ` when ${entities.conditions.join(' and ')}`;
    }
    
    if (entities.expectations.length > 0) {
      description += ` and verify ${entities.expectations.join(', ')}`;
    }
    
    return description;
  }
}