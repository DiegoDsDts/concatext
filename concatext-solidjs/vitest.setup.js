// vitest.setup.js
import { expect, afterEach } from 'vitest';
// import { cleanup } from '@testing-library/react'; // Or your framework's testing library
// import matchers from '@testing-library/jest-dom/matchers'; // if you need jest-dom matchers

// Extends Vitest's expect method with methods from react-testing-library
// expect.extend(matchers); // Uncomment if using jest-dom matchers

// Runs a cleanup function after each test case (e.g. clearing jsdom)
// afterEach(() => {
//   cleanup(); // Uncomment if using a testing library that needs cleanup
// });

console.log('Vitest setup file loaded.');

// You can add any global setup here, e.g., mocking global objects
// global.myGlobalMock = vi.fn();
