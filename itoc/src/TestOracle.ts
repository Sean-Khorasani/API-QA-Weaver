import { LearnedContract, TestAssertion, Schema } from './types';
import jsf from 'json-schema-faker';

export class TestOracle {
  generateAssertions(contract: LearnedContract, response: any): TestAssertion[] {
    const assertions: TestAssertion[] = [];

    // Status code assertion
    const expectedStatuses = contract.patterns.commonResponses.map(r => r.statusCode);
    assertions.push({
      type: 'status',
      expected: expectedStatuses,
      actual: response.status,
      message: `Status code should be one of: ${expectedStatuses.join(', ')}`
    });

    // Response time assertion
    const avgResponseTime = contract.patterns.commonResponses
      .find(r => r.statusCode === response.status)?.responseTime.p95 || 1000;
    
    assertions.push({
      type: 'timing',
      expected: avgResponseTime,
      actual: response.responseTime,
      message: `Response time should be under ${avgResponseTime}ms (95th percentile)`
    });

    // Schema validation if available
    const responseSchema = contract.responses[response.status]?.schema;
    if (responseSchema && response.data) {
      const schemaAssertions = this.validateSchema(response.data, responseSchema);
      assertions.push(...schemaAssertions);
    }

    // Contract-specific assertions based on patterns
    if (contract.patterns.commonResponses.length > 0) {
      const mostCommonStatus = contract.patterns.commonResponses
        .sort((a, b) => b.frequency - a.frequency)[0];
      
      if (response.status === mostCommonStatus.statusCode) {
        assertions.push({
          type: 'contract',
          expected: true,
          actual: true,
          message: `Response matches most common pattern (${mostCommonStatus.frequency * 100}% of traffic)`
        });
      }
    }

    // Check for known anomalies
    contract.anomalies.forEach(anomaly => {
      if (anomaly.severity === 'high') {
        assertions.push({
          type: 'contract',
          expected: 0,
          actual: anomaly.occurrences,
          message: `High severity anomaly detected: ${anomaly.description}`
        });
      }
    });

    return assertions;
  }

  generateTestData(contract: LearnedContract): any {
    const testData: any = {};

    // Generate path parameters
    if (contract.parameters) {
      contract.parameters.forEach(param => {
        if (param.in === 'path') {
          testData.path = testData.path || {};
          testData.path[param.name] = this.generateValue(param.schema, contract.patterns.commonParams[param.name]);
        } else if (param.in === 'query') {
          testData.query = testData.query || {};
          testData.query[param.name] = this.generateValue(param.schema, contract.patterns.commonParams[param.name]);
        }
      });
    }

    // Generate request body
    if (contract.requestBody) {
      try {
        testData.body = jsf.generate(contract.requestBody);
      } catch (error) {
        testData.body = this.generateFromSchema(contract.requestBody);
      }
    }

    return testData;
  }

  private generateValue(schema: Schema, commonValues?: any[]): any {
    // Use common values if available
    if (commonValues && commonValues.length > 0) {
      return commonValues[Math.floor(Math.random() * commonValues.length)];
    }

    // Generate based on schema
    switch (schema.type) {
      case 'string':
        if (schema.enum) {
          return schema.enum[0];
        }
        if (schema.pattern) {
          return 'test-value'; // Simplified for POC
        }
        return 'test-string';
      
      case 'number':
      case 'integer':
        if (schema.minimum !== undefined && schema.maximum !== undefined) {
          return Math.floor((schema.minimum + schema.maximum) / 2);
        }
        return 42;
      
      case 'boolean':
        return true;
      
      case 'array':
        return [this.generateValue(schema.items || { type: 'string' })];
      
      case 'object':
        return this.generateFromSchema(schema);
      
      default:
        return null;
    }
  }

  private generateFromSchema(schema: Schema): any {
    if (schema.type !== 'object' || !schema.properties) {
      return {};
    }

    const obj: any = {};
    Object.entries(schema.properties).forEach(([key, propSchema]) => {
      if (schema.required?.includes(key)) {
        obj[key] = this.generateValue(propSchema);
      }
    });

    return obj;
  }

  private validateSchema(data: any, schema: Schema, path: string = ''): TestAssertion[] {
    const assertions: TestAssertion[] = [];

    switch (schema.type) {
      case 'object':
        assertions.push({
          type: 'schema',
          expected: 'object',
          actual: typeof data,
          path,
          message: `${path || 'Response'} should be an object`
        });

        if (schema.properties && typeof data === 'object' && data !== null) {
          // Check required properties
          schema.required?.forEach(key => {
            assertions.push({
              type: 'schema',
              expected: true,
              actual: key in data,
              path: `${path}.${key}`,
              message: `Required property '${key}' should exist`
            });
          });

          // Validate each property
          Object.entries(schema.properties).forEach(([key, propSchema]) => {
            if (key in data) {
              assertions.push(...this.validateSchema(data[key], propSchema, `${path}.${key}`));
            }
          });
        }
        break;

      case 'array':
        assertions.push({
          type: 'schema',
          expected: 'array',
          actual: Array.isArray(data) ? 'array' : typeof data,
          path,
          message: `${path || 'Response'} should be an array`
        });

        if (Array.isArray(data) && schema.items) {
          data.forEach((item, index) => {
            assertions.push(...this.validateSchema(item, schema.items!, `${path}[${index}]`));
          });
        }
        break;

      case 'string':
        assertions.push({
          type: 'schema',
          expected: 'string',
          actual: typeof data,
          path,
          message: `${path || 'Response'} should be a string`
        });

        if (typeof data === 'string') {
          if (schema.minLength !== undefined) {
            assertions.push({
              type: 'value',
              expected: schema.minLength,
              actual: data.length,
              path,
              message: `String length should be at least ${schema.minLength}`
            });
          }
          if (schema.pattern) {
            const regex = new RegExp(schema.pattern);
            assertions.push({
              type: 'value',
              expected: true,
              actual: regex.test(data),
              path,
              message: `String should match pattern: ${schema.pattern}`
            });
          }
        }
        break;

      case 'number':
      case 'integer':
        assertions.push({
          type: 'schema',
          expected: schema.type,
          actual: typeof data,
          path,
          message: `${path || 'Response'} should be a ${schema.type}`
        });

        if (typeof data === 'number') {
          if (schema.minimum !== undefined) {
            assertions.push({
              type: 'value',
              expected: `>= ${schema.minimum}`,
              actual: data,
              path,
              message: `Value should be at least ${schema.minimum}`
            });
          }
          if (schema.maximum !== undefined) {
            assertions.push({
              type: 'value',
              expected: `<= ${schema.maximum}`,
              actual: data,
              path,
              message: `Value should be at most ${schema.maximum}`
            });
          }
        }
        break;

      case 'boolean':
        assertions.push({
          type: 'schema',
          expected: 'boolean',
          actual: typeof data,
          path,
          message: `${path || 'Response'} should be a boolean`
        });
        break;
    }

    return assertions;
  }

  evaluateAssertions(assertions: TestAssertion[]): {
    passed: number;
    failed: number;
    failures: TestAssertion[];
  } {
    const failures = assertions.filter(a => {
      if (a.type === 'status' && Array.isArray(a.expected)) {
        return !a.expected.includes(a.actual);
      }
      if (a.type === 'timing') {
        return a.actual > a.expected;
      }
      if (a.type === 'value' && typeof a.expected === 'string' && a.expected.startsWith('>=')) {
        return a.actual < parseFloat(a.expected.substring(2));
      }
      if (a.type === 'value' && typeof a.expected === 'string' && a.expected.startsWith('<=')) {
        return a.actual > parseFloat(a.expected.substring(2));
      }
      return a.expected !== a.actual;
    });

    return {
      passed: assertions.length - failures.length,
      failed: failures.length,
      failures
    };
  }
}