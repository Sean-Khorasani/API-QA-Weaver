import { APIContract, TrafficPattern, LearnedContract, Anomaly, Schema } from './types';
import SwaggerParser from '@apidevtools/swagger-parser';
import { OpenAI } from 'openai';

export class ContractLearner {
  private openai: OpenAI | null = null;
  private contracts: Map<string, LearnedContract> = new Map();
  private trafficHistory: Map<string, any[]> = new Map();

  constructor(private openaiApiKey?: string) {
    if (openaiApiKey) {
      this.openai = new OpenAI({ apiKey: openaiApiKey });
    }
  }

  async learnFromOpenAPI(specPath: string): Promise<APIContract[]> {
    try {
      const api = await SwaggerParser.validate(specPath);
      const contracts: APIContract[] = [];

      if (api.paths) {
        for (const [path, pathItem] of Object.entries(api.paths)) {
          for (const [method, operation] of Object.entries(pathItem)) {
            if (['get', 'post', 'put', 'delete', 'patch'].includes(method)) {
              const contract = this.extractContract(path, method, operation);
              contracts.push(contract);
              
              const key = `${method.toUpperCase()} ${path}`;
              this.contracts.set(key, {
                ...contract,
                patterns: {
                  endpoint: path,
                  method: method.toUpperCase(),
                  frequency: 0,
                  commonParams: {},
                  commonResponses: []
                },
                anomalies: [],
                lastUpdated: new Date()
              });
            }
          }
        }
      }

      return contracts;
    } catch (error) {
      throw new Error(`Failed to parse OpenAPI spec: ${error}`);
    }
  }

  private extractContract(path: string, method: string, operation: any): APIContract {
    const contract: APIContract = {
      endpoint: path,
      method: method.toUpperCase(),
      parameters: [],
      responses: {}
    };

    // Extract parameters
    if (operation.parameters) {
      contract.parameters = operation.parameters.map((param: any) => ({
        name: param.name,
        in: param.in,
        required: param.required || false,
        schema: param.schema || { type: 'string' }
      }));
    }

    // Extract request body
    if (operation.requestBody?.content?.['application/json']?.schema) {
      contract.requestBody = operation.requestBody.content['application/json'].schema;
    }

    // Extract responses
    if (operation.responses) {
      for (const [statusCode, response] of Object.entries(operation.responses)) {
        contract.responses[statusCode] = {
          description: (response as any).description || '',
          schema: (response as any).content?.['application/json']?.schema
        };
      }
    }

    return contract;
  }

  async learnFromTraffic(
    endpoint: string,
    method: string,
    request: any,
    response: any,
    responseTime: number
  ): Promise<void> {
    const key = `${method.toUpperCase()} ${endpoint}`;
    
    // Store traffic data
    if (!this.trafficHistory.has(key)) {
      this.trafficHistory.set(key, []);
    }
    
    const traffic = this.trafficHistory.get(key)!;
    traffic.push({
      request,
      response,
      responseTime,
      timestamp: new Date()
    });

    // Keep only last 1000 entries
    if (traffic.length > 1000) {
      traffic.shift();
    }

    // Update learned contract
    let contract = this.contracts.get(key);
    if (!contract) {
      // Create new contract from traffic
      contract = this.createContractFromTraffic(endpoint, method, traffic);
      this.contracts.set(key, contract);
    } else {
      // Update existing contract
      this.updateContractFromTraffic(contract, traffic);
    }

    // Detect anomalies
    await this.detectAnomalies(contract, request, response, responseTime);
  }

  private createContractFromTraffic(
    endpoint: string,
    method: string,
    traffic: any[]
  ): LearnedContract {
    const responses: { [key: string]: { count: number; times: number[] } } = {};
    const params: { [key: string]: Set<any> } = {};

    traffic.forEach(t => {
      // Collect response patterns
      const status = t.response.status.toString();
      if (!responses[status]) {
        responses[status] = { count: 0, times: [] };
      }
      responses[status].count++;
      responses[status].times.push(t.responseTime);

      // Collect parameter patterns
      if (t.request.params) {
        Object.entries(t.request.params).forEach(([key, value]) => {
          if (!params[key]) params[key] = new Set();
          params[key].add(value);
        });
      }
    });

    // Build contract
    const commonResponses = Object.entries(responses).map(([status, data]) => ({
      statusCode: parseInt(status),
      frequency: data.count / traffic.length,
      responseTime: {
        avg: data.times.reduce((a, b) => a + b, 0) / data.times.length,
        p95: this.percentile(data.times, 95),
        p99: this.percentile(data.times, 99)
      }
    }));

    const commonParams: { [key: string]: any[] } = {};
    Object.entries(params).forEach(([key, values]) => {
      commonParams[key] = Array.from(values);
    });

    return {
      endpoint,
      method: method.toUpperCase(),
      responses: {},
      patterns: {
        endpoint,
        method: method.toUpperCase(),
        frequency: traffic.length,
        commonParams,
        commonResponses
      },
      anomalies: [],
      lastUpdated: new Date()
    };
  }

  private updateContractFromTraffic(contract: LearnedContract, traffic: any[]): void {
    // Update frequency
    contract.patterns.frequency = traffic.length;
    
    // Update common parameters
    const params: { [key: string]: Set<any> } = {};
    traffic.forEach(t => {
      if (t.request.params) {
        Object.entries(t.request.params).forEach(([key, value]) => {
          if (!params[key]) params[key] = new Set();
          params[key].add(value);
        });
      }
    });
    
    Object.entries(params).forEach(([key, values]) => {
      contract.patterns.commonParams[key] = Array.from(values);
    });

    // Update response patterns
    const responses: { [key: string]: { count: number; times: number[] } } = {};
    traffic.forEach(t => {
      const status = t.response.status.toString();
      if (!responses[status]) {
        responses[status] = { count: 0, times: [] };
      }
      responses[status].count++;
      responses[status].times.push(t.responseTime);
    });

    contract.patterns.commonResponses = Object.entries(responses).map(([status, data]) => ({
      statusCode: parseInt(status),
      frequency: data.count / traffic.length,
      responseTime: {
        avg: data.times.reduce((a, b) => a + b, 0) / data.times.length,
        p95: this.percentile(data.times, 95),
        p99: this.percentile(data.times, 99)
      }
    }));

    contract.lastUpdated = new Date();
  }

  private async detectAnomalies(
    contract: LearnedContract,
    request: any,
    response: any,
    responseTime: number
  ): Promise<void> {
    const anomalies: Anomaly[] = [];

    // Check for unexpected status codes
    const expectedStatuses = contract.patterns.commonResponses.map(r => r.statusCode);
    if (!expectedStatuses.includes(response.status)) {
      this.addAnomaly(contract, {
        type: 'unexpected_status',
        description: `Unexpected status code ${response.status}`,
        severity: response.status >= 500 ? 'high' : 'medium',
        occurrences: 1,
        firstSeen: new Date(),
        lastSeen: new Date()
      });
    }

    // Check for performance degradation
    const avgResponseTime = contract.patterns.commonResponses
      .find(r => r.statusCode === response.status)?.responseTime.avg || 0;
    
    if (responseTime > avgResponseTime * 2 && avgResponseTime > 0) {
      this.addAnomaly(contract, {
        type: 'performance_degradation',
        description: `Response time ${responseTime}ms is 2x slower than average ${avgResponseTime}ms`,
        severity: responseTime > avgResponseTime * 5 ? 'high' : 'medium',
        occurrences: 1,
        firstSeen: new Date(),
        lastSeen: new Date()
      });
    }

    // Use AI to detect semantic anomalies if available
    if (this.openai && response.data) {
      try {
        const aiAnalysis = await this.analyzeWithAI(contract, request, response);
        if (aiAnalysis) {
          anomalies.push(aiAnalysis);
        }
      } catch (error) {
        // AI analysis is optional, don't fail on errors
        console.error('AI analysis failed:', error);
      }
    }
  }

  private addAnomaly(contract: LearnedContract, anomaly: Anomaly): void {
    const existing = contract.anomalies.find(
      a => a.type === anomaly.type && a.description === anomaly.description
    );
    
    if (existing) {
      existing.occurrences++;
      existing.lastSeen = new Date();
    } else {
      contract.anomalies.push(anomaly);
    }
  }

  private async analyzeWithAI(
    contract: LearnedContract,
    request: any,
    response: any
  ): Promise<Anomaly | null> {
    if (!this.openai) return null;

    try {
      const prompt = `Analyze this API response for anomalies:
        Endpoint: ${contract.endpoint}
        Method: ${contract.method}
        Expected patterns: ${JSON.stringify(contract.patterns.commonResponses)}
        Actual response: ${JSON.stringify(response.data).slice(0, 500)}
        
        Is there anything unusual or concerning about this response?`;

      const completion = await this.openai.chat.completions.create({
        model: "gpt-3.5-turbo",
        messages: [{ role: "user", content: prompt }],
        max_tokens: 200
      });

      const analysis = completion.choices[0]?.message?.content;
      if (analysis && analysis.toLowerCase().includes('unusual')) {
        return {
          type: 'schema_mismatch',
          description: analysis.slice(0, 200),
          severity: 'low',
          occurrences: 1,
          firstSeen: new Date(),
          lastSeen: new Date()
        };
      }
    } catch (error) {
      console.error('AI analysis error:', error);
    }

    return null;
  }

  private percentile(arr: number[], p: number): number {
    const sorted = [...arr].sort((a, b) => a - b);
    const index = Math.ceil((p / 100) * sorted.length) - 1;
    return sorted[index] || 0;
  }

  getLearnedContract(endpoint: string, method: string): LearnedContract | undefined {
    return this.contracts.get(`${method.toUpperCase()} ${endpoint}`);
  }

  getAllContracts(): LearnedContract[] {
    return Array.from(this.contracts.values());
  }
}