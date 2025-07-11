export interface APIContract {
  endpoint: string;
  method: string;
  parameters?: Parameter[];
  requestBody?: Schema;
  responses: {
    [statusCode: string]: {
      description: string;
      schema?: Schema;
    };
  };
}

export interface Parameter {
  name: string;
  in: 'query' | 'path' | 'header' | 'cookie';
  required: boolean;
  schema: Schema;
}

export interface Schema {
  type: string;
  properties?: { [key: string]: Schema };
  items?: Schema;
  required?: string[];
  enum?: any[];
  minimum?: number;
  maximum?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
}

export interface TestAssertion {
  type: 'status' | 'schema' | 'value' | 'header' | 'timing' | 'contract';
  expected: any;
  actual?: any;
  path?: string;
  message: string;
}

export interface TrafficPattern {
  endpoint: string;
  method: string;
  frequency: number;
  commonParams: { [key: string]: any[] };
  commonResponses: {
    statusCode: number;
    frequency: number;
    responseTime: { avg: number; p95: number; p99: number };
  }[];
}

export interface LearnedContract extends APIContract {
  patterns: TrafficPattern;
  anomalies: Anomaly[];
  lastUpdated: Date;
}

export interface Anomaly {
  type: 'schema_mismatch' | 'unexpected_status' | 'performance_degradation' | 'new_error_pattern';
  description: string;
  severity: 'low' | 'medium' | 'high';
  occurrences: number;
  firstSeen: Date;
  lastSeen: Date;
}