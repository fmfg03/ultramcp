#!/bin/bash

# Advanced Web Research: Playwright + CoD Analysis
source "$(dirname "$0")/common.sh"

URL="$1"
TASK_ID=$(generate_task_id)

if [ -z "$URL" ]; then
    echo "Usage: make research URL='https://example.com'"
    echo ""
    echo "Examples:"
    echo "  make research URL='https://anthropic.com'"
    echo "  make research URL='https://news.ycombinator.com'"
    echo "  make research URL='https://arxiv.org/abs/2301.00001'"
    exit 1
fi

log_info "web-research" "Starting research on: $URL (Task: $TASK_ID)"

echo "🔍 UltraMCP Web Research Pipeline"
echo "=================================="
echo "URL: $URL"
echo "Task ID: $TASK_ID"
echo ""

# Ensure data directories exist
ensure_directory "data/scrapes"
ensure_directory "data/research"

# Step 1: Scrape content
echo "📄 Step 1: Extracting content from webpage..."
echo "============================================="

scrape_output=$(make web-scrape URL="$URL" 2>&1)
scrape_exit_code=$?

if [ $scrape_exit_code -ne 0 ]; then
    handle_error "web-research" "SCRAPE_FAILED" "Failed to scrape content from URL" '["Check URL accessibility", "Verify internet connection", "Try manual browser access"]'
    echo "Scrape output:"
    echo "$scrape_output"
    exit 1
fi

echo "✅ Content extraction completed"

# Find the latest scrape file for our task
scrape_file=$(ls -t data/scrapes/task_*_scrape.json 2>/dev/null | head -1)

if [ ! -f "$scrape_file" ]; then
    handle_error "web-research" "NO_SCRAPE_FILE" "Scrape file not found" '["Check scraping step", "Verify file permissions", "Try different URL"]'
    exit 1
fi

# Analyze scraped content
echo ""
echo "🧠 Step 2: Analyzing content with AI..."
echo "======================================="

content_length=$(jq -r '.content_length // 0' "$scrape_file")
title=$(jq -r '.title // "Unknown"' "$scrape_file")

echo "📊 Content Analysis:"
echo "  Title: $title"
echo "  Content Length: $content_length characters"

if [ "$content_length" -gt 200 ]; then
    echo "  ✅ Sufficient content for AI analysis"
    
    # Extract content for analysis
    content=$(jq -r '.content' "$scrape_file")
    content_preview="${content:0:1500}..." # Limit content for analysis
    
    # Create analysis topic for CoD Protocol
    analysis_topic="Analyze and provide key insights from this web content: Title: '$title', URL: '$URL', Content: $content_preview"
    
    echo ""
    echo "🎭 Running Chain-of-Debate analysis..."
    
    # Run CoD analysis
    debate_output=$(make debate TOPIC="$analysis_topic" 2>&1)
    debate_exit_code=$?
    
    if [ $debate_exit_code -eq 0 ]; then
        echo "✅ AI analysis completed"
        
        # Find the latest debate file
        debate_file=$(ls -t data/debates/task_*_results.json 2>/dev/null | head -1)
        
        # Create comprehensive research report
        research_file="data/research/${TASK_ID}_research.json"
        
        # Combine scraping and analysis results
        jq -n \
            --arg task_id "$TASK_ID" \
            --arg url "$URL" \
            --arg timestamp "$(date -Iseconds)" \
            --argjson scrape_data "$(cat "$scrape_file")" \
            --argjson analysis_data "$(cat "$debate_file" 2>/dev/null || echo '{}')" \
            '{
                task_id: $task_id,
                url: $url,
                timestamp: $timestamp,
                research_type: "web_analysis",
                scrape_results: $scrape_data,
                ai_analysis: $analysis_data,
                summary: {
                    title: $scrape_data.title,
                    content_length: $scrape_data.content_length,
                    links_found: ($scrape_data.links | length),
                    analysis_confidence: $analysis_data.confidence_score,
                    key_insights: $analysis_data.consensus
                }
            }' > "$research_file"
        
        echo ""
        echo "📊 Research Complete!"
        echo "===================="
        echo ""
        
        # Display research summary
        echo "🎯 Research Summary:"
        echo "  URL: $URL"
        echo "  Content: ${content_length} characters"
        echo "  Links: $(jq -r '.scrape_results.links | length' "$research_file") found"
        
        if [ -f "$debate_file" ]; then
            confidence=$(jq -r '.confidence_score // "unknown"' "$debate_file")
            echo "  AI Confidence: ${confidence}%"
            
            echo ""
            echo "💡 Key Insights:"
            echo "================"
            jq -r '.consensus // "No analysis available"' "$debate_file" 2>/dev/null || echo "Analysis data not available"
            
            echo ""
            echo "📋 Executive Summaries:"
            echo "======================="
            
            echo ""
            echo "💰 CFO Perspective:"
            jq -r '.explanation.forCFO // "Not available"' "$debate_file" 2>/dev/null || echo "Not available"
            
            echo ""
            echo "🔧 CTO Perspective:"
            jq -r '.explanation.forCTO // "Not available"' "$debate_file" 2>/dev/null || echo "Not available"
        fi
        
        echo ""
        echo "💾 Complete research saved to: $research_file"
        
    else
        echo "⚠️  AI analysis failed, providing basic research summary"
        
        # Create basic research report without AI analysis
        research_file="data/research/${TASK_ID}_research.json"
        
        jq -n \
            --arg task_id "$TASK_ID" \
            --arg url "$URL" \
            --arg timestamp "$(date -Iseconds)" \
            --argjson scrape_data "$(cat "$scrape_file")" \
            '{
                task_id: $task_id,
                url: $url,
                timestamp: $timestamp,
                research_type: "basic_scraping",
                scrape_results: $scrape_data,
                ai_analysis: null,
                summary: {
                    title: $scrape_data.title,
                    content_length: $scrape_data.content_length,
                    links_found: ($scrape_data.links | length),
                    analysis_confidence: 0,
                    note: "AI analysis not available"
                }
            }' > "$research_file"
        
        echo ""
        echo "📊 Basic Research Summary:"
        echo "========================="
        echo "  Title: $title"
        echo "  Content: ${content_length} characters"
        echo "  Links: $(jq -r '.links | length' "$scrape_file") found"
        echo ""
        echo "📖 Content Preview:"
        echo "$content" | head -10
        
        echo ""
        echo "💾 Basic research saved to: $research_file"
    fi
    
else
    echo "⚠️  Content too short for detailed analysis (${content_length} characters)"
    echo ""
    echo "📖 Available Content:"
    echo "===================="
    jq -r '.content' "$scrape_file"
    
    # Create minimal research report
    research_file="data/research/${TASK_ID}_research.json"
    
    jq -n \
        --arg task_id "$TASK_ID" \
        --arg url "$URL" \
        --arg timestamp "$(date -Iseconds)" \
        --argjson scrape_data "$(cat "$scrape_file")" \
        '{
            task_id: $task_id,
            url: $url,
            timestamp: $timestamp,
            research_type: "minimal_content",
            scrape_results: $scrape_data,
            ai_analysis: null,
            summary: {
                title: $scrape_data.title,
                content_length: $scrape_data.content_length,
                note: "Content too short for AI analysis"
            }
        }' > "$research_file"
    
    echo ""
    echo "💾 Minimal research saved to: $research_file"
fi

log_success "web-research" "Research completed: $URL"