// src/utils/testUtils.js
let testsRun = 0;
let testsPassed = 0;
let currentSuiteName = "";

export function describe(suiteName, callback) {
  currentSuiteName = suiteName;
  console.log(`\n--- ${suiteName} ---`);
  callback();
  currentSuiteName = ""; // Reset after suite finishes
}

export function it(testName, callback) {
  testsRun++;
  const fullTestName = currentSuiteName ? `${currentSuiteName} > ${testName}` : testName;
  try {
    callback();
    console.log(`  ✓ PASS: ${fullTestName}`);
    testsPassed++;
  } catch (error) {
    console.error(`  ✗ FAIL: ${fullTestName}`);
    console.error(`    Error: ${error.message}`);
    if (error.stack) {
        // Indent stack trace for better readability
        const indentedStack = error.stack.split('\n').map(line => `      ${line}`).join('\n');
        console.error(indentedStack);
    }
  }
}

export function assertEquals(actual, expected, message) {
  if (actual !== expected) {
    const err = new Error(message || `AssertionError: Expected "${expected}" but got "${actual}"`);
    err.name = "AssertionError"; // Differentiate from other errors
    throw err;
  }
}

export function assertThrows(func, expectedErrorMessageSubstring, message) {
  let thrownError = null;
  try {
    func();
  } catch (error) {
    thrownError = error;
  }
  if (!thrownError) {
    throw new Error(message || "AssertionError: Expected function to throw an error, but it did not.");
  }
  if (expectedErrorMessageSubstring && !thrownError.message.includes(expectedErrorMessageSubstring)) {
    throw new Error(message || `AssertionError: Expected error message to include "${expectedErrorMessageSubstring}", but got "${thrownError.message}".`);
  }
}

export function mockFn() {
    let callCount = 0;
    const calls = [];
    const mock = (...args) => {
        callCount++;
        calls.push(args);
        // Return undefined by default, or allow a mock implementation
        if (mock._mockImpl) {
            return mock._mockImpl(...args);
        }
    };
    mock.calledOnce = () => callCount === 1;
    mock.called = () => callCount > 0;
    mock.callCount = () => callCount;
    mock.getCalls = () => calls;
    mock.mockImplementation = (impl) => {
        mock._mockImpl = impl;
        return mock;
    };
    // For expect.objectContaining like behavior (very basic)
    mock.toHaveBeenCalledWith = (expectedArgs) => {
        return calls.some(callArgs => {
            if (typeof expectedArgs === 'function') { // For expect.objectContaining
                 return expectedArgs(callArgs[0]); // Assuming single argument for simplicity
            }
            return JSON.stringify(callArgs) === JSON.stringify(Array.isArray(expectedArgs) ? expectedArgs : [expectedArgs]);
        });
    };
    return mock;
}


export function getTestSummary() {
  console.log(`\n--- Test Summary ---`);
  console.log(`Total tests run: ${testsRun}`);
  console.log(`Tests passed: ${testsPassed}`);
  console.log(`Tests failed: ${testsRun - testsPassed}`);
  if (testsRun > 0 && testsRun === testsPassed) {
    console.log("All tests passed! 🎉");
  } else if (testsRun - testsPassed > 0) {
    console.error("Some tests failed. ✗");
  } else {
    console.log("No tests were run.");
  }
  // Exit with error code if tests failed, for CI environments
  if (testsRun - testsPassed > 0) {
    return 1; // Indicate failure
  }
  return 0; // Indicate success
}
