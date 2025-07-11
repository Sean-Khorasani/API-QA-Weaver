import * as parser from '@babel/parser';
import traverse from '@babel/traverse';
import * as t from '@babel/types';
import * as fs from 'fs';
import * as path from 'path';
import { APIEndpoint, CodeChange, Change } from './types';

export class CodeAnalyzer {
  private endpointCache: Map<string, APIEndpoint[]> = new Map();

  async analyzeFile(filePath: string): Promise<APIEndpoint[]> {
    const content = fs.readFileSync(filePath, 'utf-8');
    const ext = path.extname(filePath);
    
    switch (ext) {
      case '.js':
      case '.ts':
        return this.analyzeJavaScript(content, filePath);
      case '.py':
        return this.analyzePython(content, filePath);
      default:
        return [];
    }
  }

  private analyzeJavaScript(content: string, filePath: string): APIEndpoint[] {
    const endpoints: APIEndpoint[] = [];
    
    try {
      const ast = parser.parse(content, {
        sourceType: 'module',
        plugins: ['typescript', 'decorators-legacy']
      });

      traverse(ast, {
        CallExpression(path) {
          // Express routes: app.get('/path', handler)
          if (t.isMemberExpression(path.node.callee)) {
            const object = path.node.callee.object;
            const property = path.node.callee.property;
            
            if (t.isIdentifier(property) && 
                ['get', 'post', 'put', 'delete', 'patch'].includes(property.name)) {
              const args = path.node.arguments;
              if (args.length >= 2 && t.isStringLiteral(args[0])) {
                endpoints.push({
                  path: args[0].value,
                  method: property.name.toUpperCase(),
                  description: this.extractDescription(path)
                });
              }
            }
          }
        },
        
        // Decorator-based routes: @Get('/path')
        Decorator(path) {
          if (t.isCallExpression(path.node.expression)) {
            const callee = path.node.expression.callee;
            if (t.isIdentifier(callee) && 
                ['Get', 'Post', 'Put', 'Delete', 'Patch'].includes(callee.name)) {
              const args = path.node.expression.arguments;
              if (args.length >= 1 && t.isStringLiteral(args[0])) {
                endpoints.push({
                  path: args[0].value,
                  method: callee.name.toUpperCase(),
                  description: this.extractDescription(path)
                });
              }
            }
          }
        }
      });
    } catch (error) {
      console.error(`Error parsing ${filePath}:`, error);
    }

    this.endpointCache.set(filePath, endpoints);
    return endpoints;
  }

  private analyzePython(content: string, filePath: string): APIEndpoint[] {
    const endpoints: APIEndpoint[] = [];
    
    // Simple regex-based parsing for Python Flask/FastAPI
    const routePatterns = [
      /@app\.(get|post|put|delete|patch)\(['"]([^'"]+)['"]\)/g,
      /@router\.(get|post|put|delete|patch)\(['"]([^'"]+)['"]\)/g
    ];
    
    routePatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(content)) !== null) {
        endpoints.push({
          path: match[2],
          method: match[1].toUpperCase()
        });
      }
    });

    this.endpointCache.set(filePath, endpoints);
    return endpoints;
  }

  private extractDescription(path: any): string {
    // Try to find comments above the route
    const comments = path.node.leadingComments;
    if (comments && comments.length > 0) {
      return comments[comments.length - 1].value.trim();
    }
    return '';
  }

  async detectChanges(filePath: string, previousContent?: string): Promise<CodeChange | null> {
    const currentContent = fs.readFileSync(filePath, 'utf-8');
    
    if (!previousContent) {
      return {
        file: filePath,
        type: 'added',
        changes: await this.analyzeNewFile(filePath),
        timestamp: new Date()
      };
    }

    if (currentContent === previousContent) {
      return null;
    }

    const previousEndpoints = this.endpointCache.get(filePath) || [];
    const currentEndpoints = await this.analyzeFile(filePath);
    
    const changes: Change[] = [];
    
    // Detect new endpoints
    currentEndpoints.forEach(current => {
      const previous = previousEndpoints.find(
        e => e.path === current.path && e.method === current.method
      );
      
      if (!previous) {
        changes.push({
          type: 'endpoint',
          path: `${current.method} ${current.path}`,
          after: current
        });
      }
    });
    
    // Detect removed endpoints
    previousEndpoints.forEach(previous => {
      const current = currentEndpoints.find(
        e => e.path === previous.path && e.method === previous.method
      );
      
      if (!current) {
        changes.push({
          type: 'endpoint',
          path: `${previous.method} ${previous.path}`,
          before: previous
        });
      }
    });

    // TODO: Detect schema and logic changes
    
    if (changes.length === 0) {
      return null;
    }

    return {
      file: filePath,
      type: 'modified',
      changes,
      timestamp: new Date()
    };
  }

  private async analyzeNewFile(filePath: string): Promise<Change[]> {
    const endpoints = await this.analyzeFile(filePath);
    
    return endpoints.map(endpoint => ({
      type: 'endpoint' as const,
      path: `${endpoint.method} ${endpoint.path}`,
      after: endpoint
    }));
  }

  async analyzeDirectory(dirPath: string): Promise<APIEndpoint[]> {
    const allEndpoints: APIEndpoint[] = [];
    
    const analyzeRecursive = async (dir: string) => {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
          await analyzeRecursive(fullPath);
        } else if (entry.isFile() && this.isCodeFile(entry.name)) {
          const endpoints = await this.analyzeFile(fullPath);
          allEndpoints.push(...endpoints);
        }
      }
    };
    
    await analyzeRecursive(dirPath);
    return allEndpoints;
  }

  private isCodeFile(filename: string): boolean {
    const extensions = ['.js', '.ts', '.jsx', '.tsx', '.py'];
    return extensions.some(ext => filename.endsWith(ext));
  }

  async calculateCoverage(testFile: string, sourceFiles: string[]): Promise<number> {
    // Simplified coverage calculation
    // In real implementation, would use nyc or similar tool
    
    const testContent = fs.readFileSync(testFile, 'utf-8');
    const allEndpoints = new Set<string>();
    const testedEndpoints = new Set<string>();
    
    // Collect all endpoints
    for (const sourceFile of sourceFiles) {
      const endpoints = await this.analyzeFile(sourceFile);
      endpoints.forEach(e => allEndpoints.add(`${e.method} ${e.path}`));
    }
    
    // Find tested endpoints
    allEndpoints.forEach(endpoint => {
      if (testContent.includes(endpoint)) {
        testedEndpoints.add(endpoint);
      }
    });
    
    return allEndpoints.size === 0 ? 100 : (testedEndpoints.size / allEndpoints.size) * 100;
  }
}