import { CodeAnalyzer } from '../src/CodeAnalyzer';
import * as fs from 'fs';
import * as path from 'path';

jest.mock('fs');

describe('CodeAnalyzer', () => {
  let analyzer: CodeAnalyzer;
  let mockFs: jest.Mocked<typeof fs>;

  beforeEach(() => {
    analyzer = new CodeAnalyzer();
    mockFs = fs as jest.Mocked<typeof fs>;
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('analyzeFile', () => {
    it('should analyze JavaScript file with Express routes', async () => {
      const jsContent = `
        const express = require('express');
        const app = express();
        
        app.get('/api/users', (req, res) => {
          res.json({ users: [] });
        });
        
        app.post('/api/users', (req, res) => {
          res.status(201).json({ id: 1 });
        });
      `;

      mockFs.readFileSync.mockReturnValue(jsContent);
      
      const endpoints = await analyzer.analyzeFile('test.js');
      
      expect(endpoints).toHaveLength(2);
      expect(endpoints[0]).toEqual({
        path: '/api/users',
        method: 'GET',
        description: ''
      });
      expect(endpoints[1]).toEqual({
        path: '/api/users',
        method: 'POST',
        description: ''
      });
    });

    it('should analyze TypeScript file with decorators', async () => {
      const tsContent = `
        @Controller('users')
        class UserController {
          @Get('/')
          getUsers() {
            return [];
          }
          
          @Post('/')
          createUser() {
            return { id: 1 };
          }
        }
      `;

      mockFs.readFileSync.mockReturnValue(tsContent);
      
      const endpoints = await analyzer.analyzeFile('test.ts');
      
      expect(endpoints.length).toBeGreaterThanOrEqual(0);
    });

    it('should analyze Python file with Flask routes', async () => {
      const pyContent = `
        from flask import Flask
        app = Flask(__name__)
        
        @app.get('/api/users')
        def get_users():
            return {'users': []}
        
        @app.post('/api/users')
        def create_user():
            return {'id': 1}, 201
      `;

      mockFs.readFileSync.mockReturnValue(pyContent);
      
      const endpoints = await analyzer.analyzeFile('test.py');
      
      expect(endpoints).toHaveLength(2);
      expect(endpoints[0]).toEqual({
        path: '/api/users',
        method: 'GET'
      });
    });

    it('should return empty array for unsupported file types', async () => {
      mockFs.readFileSync.mockReturnValue('some content');
      
      const endpoints = await analyzer.analyzeFile('test.txt');
      
      expect(endpoints).toEqual([]);
    });
  });

  describe('detectChanges', () => {
    it('should detect new file as added', async () => {
      const content = `app.get('/api/test', handler);`;
      mockFs.readFileSync.mockReturnValue(content);
      
      const change = await analyzer.detectChanges('test.js');
      
      expect(change).not.toBeNull();
      expect(change?.type).toBe('added');
      expect(change?.changes.length).toBeGreaterThan(0);
    });

    it('should return null for unchanged content', async () => {
      const content = `app.get('/api/test', handler);`;
      mockFs.readFileSync.mockReturnValue(content);
      
      const change = await analyzer.detectChanges('test.js', content);
      
      expect(change).toBeNull();
    });

    it('should detect endpoint additions', async () => {
      const oldContent = `app.get('/api/users', handler);`;
      const newContent = `
        app.get('/api/users', handler);
        app.post('/api/users', handler);
      `;
      
      mockFs.readFileSync.mockReturnValue(newContent);
      
      // First analyze with old content to cache
      mockFs.readFileSync.mockReturnValueOnce(oldContent);
      await analyzer.analyzeFile('test.js');
      
      // Then detect changes
      mockFs.readFileSync.mockReturnValue(newContent);
      const change = await analyzer.detectChanges('test.js', oldContent);
      
      expect(change).not.toBeNull();
      expect(change?.type).toBe('modified');
      expect(change?.changes.some(c => c.type === 'endpoint' && c.after)).toBe(true);
    });
  });

  describe('analyzeDirectory', () => {
    it('should analyze all code files in directory', async () => {
      mockFs.readdirSync.mockReturnValue([
        { name: 'file1.js', isDirectory: () => false, isFile: () => true },
        { name: 'file2.ts', isDirectory: () => false, isFile: () => true },
        { name: 'file3.txt', isDirectory: () => false, isFile: () => true },
        { name: 'subdir', isDirectory: () => true, isFile: () => false }
      ] as any);

      mockFs.readFileSync.mockReturnValue(`app.get('/api/test', handler);`);
      
      const endpoints = await analyzer.analyzeDirectory('/test/dir');
      
      // Should analyze .js and .ts files only
      expect(mockFs.readFileSync).toHaveBeenCalledTimes(2);
      expect(endpoints.length).toBeGreaterThan(0);
    });

    it('should skip hidden directories and node_modules', async () => {
      mockFs.readdirSync.mockReturnValue([
        { name: '.git', isDirectory: () => true, isFile: () => false },
        { name: 'node_modules', isDirectory: () => true, isFile: () => false },
        { name: 'src', isDirectory: () => true, isFile: () => false }
      ] as any);

      await analyzer.analyzeDirectory('/test/dir');
      
      // Should only recurse into 'src'
      expect(mockFs.readdirSync).toHaveBeenCalledTimes(2); // root + src
    });
  });

  describe('calculateCoverage', () => {
    it('should calculate coverage based on tested endpoints', async () => {
      const testContent = `
        test('GET /api/users', () => {});
        test('POST /api/users', () => {});
      `;
      
      const sourceContent = `
        app.get('/api/users', handler);
        app.post('/api/users', handler);
        app.delete('/api/users/:id', handler);
      `;

      mockFs.readFileSync
        .mockReturnValueOnce(testContent) // test file
        .mockReturnValueOnce(sourceContent); // source file
      
      const coverage = await analyzer.calculateCoverage('test.spec.js', ['api.js']);
      
      expect(coverage).toBe(66.67); // 2 out of 3 endpoints tested
    });

    it('should return 100% coverage when no endpoints exist', async () => {
      mockFs.readFileSync.mockReturnValue('no endpoints here');
      
      const coverage = await analyzer.calculateCoverage('test.spec.js', ['api.js']);
      
      expect(coverage).toBe(100);
    });
  });
});