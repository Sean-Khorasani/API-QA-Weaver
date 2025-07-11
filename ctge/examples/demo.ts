import { ConversationalEngine, APIContext } from '../src';
import * as fs from 'fs';
import * as path from 'path';

async function runDemo() {
  console.log('=== CTGE (Conversational Test Generation Engine) Demo ===\n');

  // Initialize the engine
  const engine = new ConversationalEngine(process.env.OPENAI_API_KEY);
  
  // API context
  const context: APIContext = {
    baseUrl: 'http://localhost:3000',
    authentication: {
      type: 'bearer'
    }
  };

  // Demo scenarios
  const testRequests = [
    "I want to test creating a new user with name John Doe and email john@example.com, and verify the response returns the user with an ID",
    "Test retrieving a list of users with pagination, limit should be 10 and offset 0, ensure the response contains an array of users",
    "Create a test to update a user's email address and verify the change was saved",
    "Test what happens when I try to create a user without providing an email address",
    "Check that deleting a user returns proper status code and the user cannot be retrieved afterwards",
    "Test API performance by creating 100 users and measuring response times",
    "Verify that unauthorized requests to user endpoints return 401 status"
  ];

  console.log('Processing natural language test requests...\n');

  for (let i = 0; i < testRequests.length; i++) {
    const request = testRequests[i];
    console.log(`\n${i + 1}. User Request: "${request}"\n`);

    try {
      const result = await engine.processUserInput(request, context);
      
      // Display the generated scenario
      console.log('Generated Test Scenario:');
      console.log(`  Description: ${result.scenario.description}`);
      console.log(`  Steps: ${result.scenario.steps.length}`);
      console.log(`  Assertions: ${result.scenario.assertions.length}`);
      
      // Display edge cases and suggestions
      if (result.suggestions.length > 0) {
        console.log('\n  Additional Test Suggestions:');
        result.suggestions.forEach((suggestion, idx) => {
          console.log(`    ${idx + 1}. ${suggestion.scenario}`);
          console.log(`       Rationale: ${suggestion.rationale}`);
        });
      }

      // Save generated tests
      const outputDir = path.join(__dirname, 'generated-tests', `scenario-${i + 1}`);
      fs.mkdirSync(outputDir, { recursive: true });

      // Save each language implementation
      result.generatedTests.forEach(test => {
        const extension = test.language === 'python' ? 'py' : test.language === 'java' ? 'java' : 'js';
        const filename = `test.${extension}`;
        const filepath = path.join(outputDir, filename);
        
        fs.writeFileSync(filepath, test.code);
        console.log(`\n  Generated ${test.language} test saved to: ${filepath}`);
      });

      // Save test scenario details
      const scenarioPath = path.join(outputDir, 'scenario.json');
      fs.writeFileSync(scenarioPath, JSON.stringify(result.scenario, null, 2));

    } catch (error) {
      console.error(`  Error processing request: ${error}`);
    }
  }

  // Interactive mode demo
  console.log('\n\n=== Interactive Mode Demo ===\n');
  console.log('Example conversation flow:\n');

  const interactiveEngine = new ConversationalEngine(process.env.OPENAI_API_KEY);
  
  const conversation = [
    "I need to test our product API",
    "The products have name, price, and category fields",
    "Add tests for creating products with invalid prices like negative numbers",
    "Also test searching products by category"
  ];

  for (const input of conversation) {
    console.log(`User: ${input}`);
    const result = await interactiveEngine.processUserInput(input, context);
    console.log(`Assistant: Generated ${result.generatedTests.length} tests with ${result.suggestions.length} suggestions\n`);
  }

  // Show conversation history
  console.log('Conversation History:');
  interactiveEngine.getConversationHistory().forEach(msg => {
    console.log(`  ${msg.role}: ${msg.content}`);
  });
}

// Example: Using CTGE programmatically
async function programmaticExample() {
  console.log('\n\n=== Programmatic Usage Example ===\n');

  const engine = new ConversationalEngine();
  
  // Process a complex test request
  const complexRequest = `
    I need comprehensive tests for a REST API user management system.
    The tests should cover:
    - Creating users with validation
    - Retrieving users with filtering and pagination
    - Updating user profiles
    - Deleting users with proper authorization
    - Edge cases like SQL injection attempts
    - Performance under load
  `;

  const result = await engine.processUserInput(complexRequest);
  
  console.log('Generated comprehensive test suite:');
  console.log(`- Main scenario: ${result.scenario.description}`);
  console.log(`- Total steps: ${result.scenario.steps.length}`);
  console.log(`- Total assertions: ${result.scenario.assertions.length}`);
  console.log(`- Additional suggestions: ${result.suggestions.length}`);
  
  // Example: Accessing specific generated test
  const jsTest = result.generatedTests.find(t => t.language === 'javascript');
  if (jsTest) {
    console.log('\nJavaScript test preview:');
    console.log(jsTest.code.substring(0, 500) + '...');
    console.log(`\nDependencies needed: ${jsTest.dependencies.join(', ')}`);
    console.log(`Setup: ${jsTest.setupInstructions}`);
  }
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