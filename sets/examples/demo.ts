import { SelfEvolvingTestSuite, EvolutionConfig } from '../src';
import * as path from 'path';
import * as fs from 'fs';

async function runDemo() {
  console.log('=== SETS (Self-Evolving Test Suite) Demo ===\n');

  // Configuration
  const config: EvolutionConfig = {
    watchPaths: [path.join(__dirname, 'sample-api')],
    testPaths: [path.join(__dirname, 'generated-tests')],
    updateThreshold: 10, // Update tests if code changes by 10%
    coverageTarget: 80, // Target 80% coverage
    aiEnabled: !!process.env.OPENAI_API_KEY,
    openaiApiKey: process.env.OPENAI_API_KEY,
    gitEnabled: false // Disable git for demo
  };

  // Create test directory
  if (!fs.existsSync(config.testPaths[0])) {
    fs.mkdirSync(config.testPaths[0], { recursive: true });
  }

  // Initialize SETS
  const sets = new SelfEvolvingTestSuite(config);
  await sets.initialize();

  console.log('\nInitial Metrics:');
  console.log(sets.getMetrics());

  console.log('\n📋 Demo Scenarios:\n');

  // Scenario 1: Initial test generation
  console.log('1. Generating initial test suite from existing endpoints...');
  await simulateInitialGeneration(sets);

  // Scenario 2: Adding a new endpoint
  console.log('\n2. Simulating addition of a new endpoint...');
  await simulateNewEndpoint();

  // Scenario 3: Modifying an existing endpoint
  console.log('\n3. Simulating modification of an existing endpoint...');
  await simulateEndpointModification();

  // Scenario 4: Removing an endpoint
  console.log('\n4. Simulating removal of an endpoint...');
  await simulateEndpointRemoval();

  // Show final metrics
  console.log('\n📊 Final Metrics:');
  console.log(sets.getMetrics());

  // Display evolution history
  console.log('\n📜 Evolution History:');
  displayEvolutionHistory(config.testPaths[0]);

  // Show generated tests
  console.log('\n🧪 Generated Tests:');
  displayGeneratedTests(config.testPaths[0]);

  // Cleanup
  console.log('\n🛑 Stopping SETS...');
  sets.stop();

  console.log('\nDemo completed! Check the generated-tests directory for the evolved test suite.');
}

async function simulateInitialGeneration(sets: SelfEvolvingTestSuite): Promise<void> {
  // Give SETS time to analyze and generate initial tests
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  const metrics = sets.getMetrics();
  console.log(`  ✓ Generated ${metrics.totalTests} initial tests`);
  console.log(`  ✓ Current coverage: ${metrics.coverage}%`);
}

async function simulateNewEndpoint(): Promise<void> {
  const newEndpointCode = `
// New product endpoints
app.get('/api/products', (req, res) => {
  res.json({ products: [] });
});

app.post('/api/products', (req, res) => {
  const { name, price } = req.body;
  if (!name || !price) {
    return res.status(400).json({ error: 'Name and price required' });
  }
  res.status(201).json({ id: 1, name, price });
});
`;

  const serverPath = path.join(__dirname, 'sample-api', 'server.js');
  const currentContent = fs.readFileSync(serverPath, 'utf-8');
  fs.writeFileSync(serverPath, currentContent + newEndpointCode);
  
  console.log('  ✓ Added /api/products endpoints');
  
  // Wait for SETS to detect and evolve
  await new Promise(resolve => setTimeout(resolve, 3000));
}

async function simulateEndpointModification(): Promise<void> {
  const serverPath = path.join(__dirname, 'sample-api', 'server.js');
  let content = fs.readFileSync(serverPath, 'utf-8');
  
  // Modify the users endpoint to add validation
  content = content.replace(
    'if (!name || !email) {',
    'if (!name || !email || !email.includes("@")) {'
  );
  
  fs.writeFileSync(serverPath, content);
  console.log('  ✓ Modified email validation in POST /api/users');
  
  // Wait for SETS to detect and evolve
  await new Promise(resolve => setTimeout(resolve, 3000));
}

async function simulateEndpointRemoval(): Promise<void> {
  const serverPath = path.join(__dirname, 'sample-api', 'server.js');
  let content = fs.readFileSync(serverPath, 'utf-8');
  
  // Remove the search endpoint
  content = content.replace(/\/\/ New endpoint[\s\S]*?res\.json\({ results, query }\);\s*}\);/m, '');
  
  fs.writeFileSync(serverPath, content);
  console.log('  ✓ Removed /api/users/search endpoint');
  
  // Wait for SETS to detect and evolve
  await new Promise(resolve => setTimeout(resolve, 3000));
}

function displayEvolutionHistory(testPath: string): void {
  const historyPath = path.join(testPath, '.evolution-history.json');
  if (fs.existsSync(historyPath)) {
    const history = JSON.parse(fs.readFileSync(historyPath, 'utf-8'));
    history.forEach((evolution: any, index: number) => {
      console.log(`\n  Evolution ${index + 1} (${evolution.version}):`);
      console.log(`    Reason: ${evolution.reason}`);
      console.log(`    Changes: ${evolution.changes.length}`);
      console.log(`    Coverage: ${evolution.coverage.before}% → ${evolution.coverage.after}%`);
      
      evolution.changes.forEach((change: any) => {
        console.log(`      - ${change.type} test: ${change.testId} (${change.reason})`);
      });
    });
  }
}

function displayGeneratedTests(testPath: string): void {
  const testFiles = fs.readdirSync(testPath).filter(f => f.endsWith('.test.js'));
  
  console.log(`\n  Found ${testFiles.length} test files:`);
  testFiles.forEach(file => {
    const content = fs.readFileSync(path.join(testPath, file), 'utf-8');
    const testCount = (content.match(/test\(/g) || []).length;
    console.log(`    - ${file}: ${testCount} tests`);
  });
  
  // Show a sample test
  if (testFiles.length > 0) {
    console.log('\n  Sample generated test:');
    const sampleContent = fs.readFileSync(path.join(testPath, testFiles[0]), 'utf-8');
    console.log('    ' + sampleContent.substring(0, 500).split('\n').join('\n    ') + '...');
  }
}

// Programmatic usage example
async function programmaticExample() {
  console.log('\n\n=== Programmatic Usage Example ===\n');

  const config: EvolutionConfig = {
    watchPaths: ['./src'],
    testPaths: ['./tests'],
    updateThreshold: 5,
    coverageTarget: 90,
    aiEnabled: false,
    gitEnabled: true
  };

  const sets = new SelfEvolvingTestSuite(config);
  
  console.log('Example: Monitoring a real project');
  console.log('1. Initialize SETS on your project:');
  console.log('   await sets.initialize();');
  
  console.log('\n2. SETS will automatically:');
  console.log('   - Watch for code changes');
  console.log('   - Generate tests for new endpoints');
  console.log('   - Update tests when endpoints change');
  console.log('   - Remove obsolete tests');
  console.log('   - Maintain target coverage');
  
  console.log('\n3. Run tests at any time:');
  console.log('   await sets.runTests();');
  
  console.log('\n4. Check metrics:');
  console.log('   const metrics = sets.getMetrics();');
  console.log('   console.log(`Coverage: ${metrics.coverage}%`);');
}

// Run the demo
(async () => {
  try {
    await runDemo();
    await programmaticExample();
  } catch (error) {
    console.error('Demo error:', error);
  }
})();