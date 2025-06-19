async function retryOperation(operation, maxRetries = 3, initialDelayMs = 100, factor = 2, jitter = true) {
  let attempts = 0;
  let delayMs = initialDelayMs;
  while (attempts < maxRetries) {
    try {
      return await operation();
    } catch (error) {
      attempts++;
      if (attempts >= maxRetries) {
        console.error(`[RetryUtils] Operation failed after ${maxRetries} attempts. Error:`, error.message);
        throw error; // Re-throw the last error
      }
      console.warn(`[RetryUtils] Operation failed (attempt ${attempts}/${maxRetries}). Retrying in ${delayMs}ms. Error:`, error.message);
      await new Promise(resolve => setTimeout(resolve, delayMs + (jitter ? Math.random() * delayMs * 0.5 : 0)));
      delayMs *= factor;
    }
  }
}

module.exports = { retryOperation };
