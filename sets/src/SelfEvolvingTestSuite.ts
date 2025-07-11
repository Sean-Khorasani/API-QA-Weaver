import { CodeAnalyzer } from './CodeAnalyzer';
import { TestEvolver } from './TestEvolver';
import { TestGenerator } from './TestGenerator';
import { EvolutionConfig, CodeChange, TestCase } from './types';
import chokidar from 'chokidar';
import simpleGit, { SimpleGit } from 'simple-git';
import * as path from 'path';
import * as fs from 'fs';

export class SelfEvolvingTestSuite {
  private codeAnalyzer: CodeAnalyzer;
  private testEvolver: TestEvolver;
  private testGenerator: TestGenerator;
  private watcher: chokidar.FSWatcher | null = null;
  private git: SimpleGit | null = null;
  private fileSnapshots: Map<string, string> = new Map();
  private isEvolving: boolean = false;

  constructor(private config: EvolutionConfig) {
    this.codeAnalyzer = new CodeAnalyzer();
    this.testEvolver = new TestEvolver(config.openaiApiKey);
    this.testGenerator = new TestGenerator(config.openaiApiKey);

    if (config.gitEnabled) {
      this.git = simpleGit();
    }
  }

  async initialize(): Promise<void> {
    console.log('Initializing Self-Evolving Test Suite...');
    
    // Analyze existing code
    for (const watchPath of this.config.watchPaths) {
      const endpoints = await this.codeAnalyzer.analyzeDirectory(watchPath);
      console.log(`Found ${endpoints.length} endpoints in ${watchPath}`);
    }

    // Load existing tests
    for (const testPath of this.config.testPaths) {
      if (fs.existsSync(testPath)) {
        this.testEvolver.importTests(testPath);
      }
    }

    // Calculate initial coverage
    const coverage = await this.calculateCurrentCoverage();
    console.log(`Initial test coverage: ${coverage.toFixed(2)}%`);

    // Start watching for changes
    this.startWatching();
  }

  private startWatching(): void {
    this.watcher = chokidar.watch(this.config.watchPaths, {
      ignored: /(^|[\/\\])\.|node_modules|test|spec/,
      persistent: true,
      ignoreInitial: true
    });

    this.watcher
      .on('add', path => this.handleFileChange(path, 'add'))
      .on('change', path => this.handleFileChange(path, 'change'))
      .on('unlink', path => this.handleFileChange(path, 'delete'));

    console.log('Watching for code changes...');
  }

  private async handleFileChange(filePath: string, event: string): Promise<void> {
    if (this.isEvolving) {
      console.log('Evolution already in progress, queuing change...');
      return;
    }

    console.log(`File ${event}: ${filePath}`);
    
    this.isEvolving = true;
    try {
      // Detect what changed
      const previousContent = this.fileSnapshots.get(filePath);
      const change = await this.codeAnalyzer.detectChanges(filePath, previousContent);
      
      if (change) {
        // Store new snapshot
        if (event !== 'delete') {
          this.fileSnapshots.set(filePath, fs.readFileSync(filePath, 'utf-8'));
        } else {
          this.fileSnapshots.delete(filePath);
        }

        // Evolve test suite
        await this.evolveTestSuite([change]);
      }
    } catch (error) {
      console.error('Error during evolution:', error);
    } finally {
      this.isEvolving = false;
    }
  }

  private async evolveTestSuite(changes: CodeChange[]): Promise<void> {
    console.log('Evolving test suite...');
    
    // Calculate current coverage
    const currentCoverage = await this.calculateCurrentCoverage();
    
    // Evolve tests based on changes
    const evolution = await this.testEvolver.evolveTestSuite(
      changes,
      currentCoverage,
      this.config.coverageTarget
    );

    console.log(`Evolution complete: ${evolution.changes.length} test changes`);
    console.log(`Coverage: ${evolution.coverage.before}% → ${evolution.coverage.after}%`);

    // Generate test code for new/updated tests
    for (const change of evolution.changes) {
      if (change.type === 'added' || change.type === 'updated') {
        await this.generateTestCode(change.details as TestCase);
      }
    }

    // Save evolution history
    this.saveEvolutionHistory();

    // Commit changes if git is enabled
    if (this.config.gitEnabled && this.git) {
      await this.commitChanges(evolution.reason);
    }
  }

  private async generateTestCode(testCase: TestCase): Promise<void> {
    const testCode = await this.testGenerator.generateTestCode(testCase);
    
    // Determine test file path
    const testFileName = `${testCase.endpoint.path.replace(/[^a-zA-Z0-9]/g, '_')}.test.js`;
    const testFilePath = path.join(this.config.testPaths[0], testFileName);
    
    // Create directory if it doesn't exist
    const testDir = path.dirname(testFilePath);
    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }
    
    // Write test file
    fs.writeFileSync(testFilePath, testCode);
    console.log(`Generated test: ${testFilePath}`);
  }

  private async calculateCurrentCoverage(): Promise<number> {
    const sourceFiles: string[] = [];
    
    // Collect all source files
    for (const watchPath of this.config.watchPaths) {
      const files = this.getAllFiles(watchPath, ['.js', '.ts']);
      sourceFiles.push(...files);
    }

    // Calculate coverage for each test file
    let totalCoverage = 0;
    let testCount = 0;
    
    for (const testPath of this.config.testPaths) {
      if (fs.existsSync(testPath)) {
        const testFiles = this.getAllFiles(testPath, ['.test.js', '.spec.js']);
        for (const testFile of testFiles) {
          const coverage = await this.codeAnalyzer.calculateCoverage(testFile, sourceFiles);
          totalCoverage += coverage;
          testCount++;
        }
      }
    }

    return testCount === 0 ? 0 : totalCoverage / testCount;
  }

  private getAllFiles(dir: string, extensions: string[]): string[] {
    const files: string[] = [];
    
    const walk = (currentDir: string) => {
      const entries = fs.readdirSync(currentDir, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(currentDir, entry.name);
        
        if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
          walk(fullPath);
        } else if (entry.isFile() && extensions.some(ext => entry.name.endsWith(ext))) {
          files.push(fullPath);
        }
      }
    };
    
    if (fs.existsSync(dir)) {
      const stat = fs.statSync(dir);
      if (stat.isDirectory()) {
        walk(dir);
      } else {
        files.push(dir);
      }
    }
    
    return files;
  }

  private saveEvolutionHistory(): void {
    const history = this.testEvolver.getEvolutionHistory();
    const historyPath = path.join(this.config.testPaths[0], '.evolution-history.json');
    fs.writeFileSync(historyPath, JSON.stringify(history, null, 2));
  }

  private async commitChanges(message: string): Promise<void> {
    if (!this.git) return;

    try {
      await this.git.add('.');
      await this.git.commit(`[SETS] ${message}`);
      console.log('Changes committed to git');
    } catch (error) {
      console.error('Git commit failed:', error);
    }
  }

  async runTests(): Promise<void> {
    console.log('Running evolved test suite...');
    
    // Export current tests
    const exportPath = path.join(this.config.testPaths[0], 'evolved-tests.json');
    this.testEvolver.exportTests(exportPath);
    
    // Run tests using Jest or other test runner
    // This is a simplified version - in production would integrate with actual test runner
    const testCommand = 'npm test';
    const { exec } = require('child_process');
    
    exec(testCommand, (error, stdout, stderr) => {
      if (error) {
        console.error(`Test execution error: ${error}`);
        return;
      }
      console.log(`Test output: ${stdout}`);
      if (stderr) {
        console.error(`Test errors: ${stderr}`);
      }
    });
  }

  stop(): void {
    if (this.watcher) {
      this.watcher.close();
      console.log('Stopped watching for changes');
    }
  }

  getMetrics(): {
    totalTests: number;
    autoGeneratedTests: number;
    coverage: number;
    lastEvolution: Date | null;
  } {
    const tests = this.testEvolver.getTestCases();
    const history = this.testEvolver.getEvolutionHistory();
    
    return {
      totalTests: tests.length,
      autoGeneratedTests: tests.filter(t => t.autoGenerated).length,
      coverage: history.length > 0 ? history[history.length - 1].coverage.after : 0,
      lastEvolution: history.length > 0 ? history[history.length - 1].timestamp : null
    };
  }
}