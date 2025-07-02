#!/bin/bash

# Web Scraping via Playwright MCP
source "$(dirname "$0")/common.sh"

URL="$1"
TASK_ID=$(generate_task_id)

if [ -z "$URL" ]; then
    echo "Usage: make web-scrape URL='https://example.com'"
    echo ""
    echo "Examples:"
    echo "  make web-scrape URL='https://news.ycombinator.com'"
    echo "  make web-scrape URL='https://httpbin.org/get'"
    echo "  make web-scrape URL='https://example.com'"
    exit 1
fi

log_info "playwright-scrape" "Scraping URL: $URL (Task: $TASK_ID)"

echo "🕷️ UltraMCP Web Scraper"
echo "======================="
echo "URL: $URL"
echo "Task ID: $TASK_ID"
echo ""

# Ensure data directory exists
ensure_directory "data/scrapes"

# Check if Playwright is available
if ! command -v npx >/dev/null; then
    handle_error "playwright-scrape" "NPX_NOT_FOUND" "npx command not found" '["Install Node.js", "Verify npm installation", "Add npm to PATH"]'
    exit 1
fi

echo "🎭 Using Playwright for web scraping..."

# Create temporary Node.js script for Playwright scraping
temp_script="/tmp/ultramcp_scrape_${TASK_ID}.js"

cat > "$temp_script" << 'EOF'
const { chromium } = require('playwright');

async function scrapeUrl(url) {
  let browser;
  try {
    // Launch browser with appropriate settings
    browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const context = await browser.newContext({
      userAgent: 'UltraMCP Web Scraper 1.0'
    });
    
    const page = await context.newPage();
    
    // Navigate to URL
    console.log(`Navigating to: ${url}`);
    await page.goto(url, { 
      waitUntil: 'domcontentloaded',
      timeout: 30000 
    });
    
    // Wait a bit for dynamic content
    await page.waitForTimeout(2000);
    
    // Extract basic information
    const title = await page.title().catch(() => 'No title');
    const textContent = await page.textContent('body').catch(() => 'No content');
    
    // Extract links
    const links = await page.$$eval('a[href]', links => 
      links.slice(0, 10).map(link => ({
        text: link.textContent.trim().substring(0, 100),
        href: link.href
      }))
    ).catch(() => []);
    
    // Extract meta information
    const metaDescription = await page.getAttribute('meta[name="description"]', 'content').catch(() => null);
    const metaKeywords = await page.getAttribute('meta[name="keywords"]', 'content').catch(() => null);
    
    // Get page screenshot data URL (small version)
    const screenshot = await page.screenshot({ 
      type: 'png',
      clip: { x: 0, y: 0, width: 800, height: 600 }
    }).catch(() => null);
    
    const result = {
      success: true,
      url: url,
      title: title,
      content: textContent.substring(0, 5000), // Limit content length
      content_length: textContent.length,
      links: links,
      meta: {
        description: metaDescription,
        keywords: metaKeywords
      },
      screenshot_available: !!screenshot,
      timestamp: new Date().toISOString(),
      task_id: process.argv[3] || 'unknown'
    };
    
    console.log(JSON.stringify(result, null, 2));
    
  } catch (error) {
    console.log(JSON.stringify({
      success: false,
      error: error.message,
      url: url,
      task_id: process.argv[3] || 'unknown',
      timestamp: new Date().toISOString()
    }, null, 2));
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Get URL from command line argument
const url = process.argv[2];
if (!url) {
  console.error('URL argument required');
  process.exit(1);
}

scrapeUrl(url);
EOF

# Execute Playwright scraping
echo "🔄 Processing webpage..."
result=$(timeout 60s npx playwright install chromium >/dev/null 2>&1 && node "$temp_script" "$URL" "$TASK_ID" 2>&1)
exit_code=$?

# Cleanup temp script
rm -f "$temp_script"

if [ $exit_code -eq 124 ]; then
    handle_error "playwright-scrape" "TIMEOUT" "Scraping operation timed out" '["Try a simpler URL", "Check internet connection", "Increase timeout"]'
    exit 1
elif [ $exit_code -ne 0 ]; then
    handle_error "playwright-scrape" "SCRAPING_FAILED" "Playwright execution failed" '["Install Playwright: npx playwright install", "Check URL accessibility", "Verify Node.js installation"]'
    echo "Error output: $result"
    exit 1
fi

# Parse and display results
if echo "$result" | jq -e '.success' >/dev/null 2>&1; then
    
    # Extract information from JSON result
    title=$(echo "$result" | jq -r '.title // "Unknown"')
    content_length=$(echo "$result" | jq -r '.content_length // 0')
    links_count=$(echo "$result" | jq -r '.links | length')
    meta_description=$(echo "$result" | jq -r '.meta.description // "None"')
    
    echo "✅ Scraping completed successfully!"
    echo ""
    echo "📊 Results Summary:"
    echo "=================="
    echo "📄 Title: $title"
    echo "📝 Content: ${content_length} characters"
    echo "🔗 Links found: $links_count"
    echo "📋 Description: $meta_description"
    echo ""
    
    # Show content preview
    echo "📖 Content Preview:"
    echo "==================="
    echo "$result" | jq -r '.content' | head -10
    echo ""
    
    # Show top links
    if [ "$links_count" -gt 0 ]; then
        echo "🔗 Top Links:"
        echo "============="
        echo "$result" | jq -r '.links[] | "• \(.text) -> \(.href)"' | head -5
        echo ""
    fi
    
    # Save full results
    results_file="data/scrapes/${TASK_ID}_scrape.json"
    echo "$result" > "$results_file"
    
    log_success "playwright-scrape" "Scraping completed: $URL (${content_length} chars)"
    echo "💾 Full results saved to: $results_file"
    
else
    # Try to extract error from result
    if echo "$result" | jq -e '.error' >/dev/null 2>&1; then
        error_msg=$(echo "$result" | jq -r '.error')
        handle_error "playwright-scrape" "SCRAPE_ERROR" "$error_msg" '["Check URL format", "Verify site accessibility", "Try with different browser settings"]'
    else
        handle_error "playwright-scrape" "UNKNOWN_ERROR" "Unknown scraping error" '["Check Playwright installation", "Verify URL accessibility", "Review error logs"]'
        echo "Raw output for debugging:"
        echo "$result"
    fi
    exit 1
fi