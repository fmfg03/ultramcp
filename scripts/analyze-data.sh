#!/bin/bash

# Data Analysis Script with CoD Protocol
source "$(dirname "$0")/common.sh"

FILE="$1"
TASK_ID=$(generate_task_id)

if [ -z "$FILE" ]; then
    echo "Usage: make analyze FILE='path/to/file'"
    echo ""
    echo "Supported formats:"
    echo "  • JSON files (.json)"
    echo "  • CSV files (.csv)"
    echo "  • Text files (.txt, .md)"
    echo "  • Research files from web-research"
    echo ""
    echo "Examples:"
    echo "  make analyze FILE='data/research/task_123_research.json'"
    echo "  make analyze FILE='data/scrapes/task_456_scrape.json'"
    echo "  make analyze FILE='data.csv'"
    exit 1
fi

if [ ! -f "$FILE" ]; then
    handle_error "analyze-data" "FILE_NOT_FOUND" "File not found: $FILE" '["Check file path", "Verify file exists", "Use absolute or relative path"]'
    exit 1
fi

log_info "analyze-data" "Starting analysis of: $FILE (Task: $TASK_ID)"

echo "🧠 UltraMCP Data Analysis"
echo "========================="
echo "File: $FILE"
echo "Task ID: $TASK_ID"
echo ""

# Ensure data directory exists
ensure_directory "data/analysis"

# Determine file type and size
file_size=$(stat -f%z "$FILE" 2>/dev/null || stat -c%s "$FILE" 2>/dev/null || echo "unknown")
file_ext="${FILE##*.}"

echo "📊 File Information:"
echo "  Type: $file_ext"
echo "  Size: $file_size bytes"

# Analyze based on file type
case "$file_ext" in
    json)
        echo ""
        echo "🔍 JSON Analysis:"
        echo "================"
        
        # Validate JSON
        if jq . "$FILE" >/dev/null 2>&1; then
            echo "  ✅ Valid JSON format"
            
            # Extract basic JSON statistics
            key_count=$(jq -r 'if type == "object" then keys | length elif type == "array" then length else 1 end' "$FILE" 2>/dev/null || echo "unknown")
            data_type=$(jq -r 'type' "$FILE" 2>/dev/null || echo "unknown")
            
            echo "  📋 Structure: $data_type"
            echo "  🔢 Keys/Items: $key_count"
            
            # Extract content for analysis
            if [ "$key_count" != "unknown" ] && [ "$data_type" = "object" ]; then
                # For object, create a summary
                content_summary=$(jq -r 'to_entries | map("\(.key): \(.value | type)") | join(", ")' "$FILE" 2>/dev/null || echo "complex structure")
                analysis_data="JSON object with $key_count fields: $content_summary"
            elif [ "$data_type" = "array" ]; then
                # For array, analyze first few elements
                sample_items=$(jq -r '.[0:3] | map(tostring) | join("; ")' "$FILE" 2>/dev/null || echo "array elements")
                analysis_data="JSON array with $key_count items. Sample: $sample_items"
            else
                # For primitive types
                content_value=$(jq -r 'tostring' "$FILE" 2>/dev/null || echo "JSON value")
                analysis_data="JSON value: $content_value"
            fi
        else
            echo "  ❌ Invalid JSON format"
            analysis_data="Invalid JSON file"
        fi
        ;;
        
    csv)
        echo ""
        echo "📈 CSV Analysis:"
        echo "==============="
        
        if [ -s "$FILE" ]; then
            # Count lines and columns
            line_count=$(wc -l < "$FILE")
            if [ "$line_count" -gt 0 ]; then
                col_count=$(head -1 "$FILE" | tr ',' '\n' | wc -l)
                headers=$(head -1 "$FILE")
                
                echo "  📊 Rows: $line_count"
                echo "  📋 Columns: $col_count"
                echo "  🏷️  Headers: $headers"
                
                # Sample data
                sample_data=$(head -3 "$FILE" | tail -2)
                analysis_data="CSV file with $line_count rows and $col_count columns. Headers: $headers. Sample data: $sample_data"
            else
                echo "  ❌ Empty CSV file"
                analysis_data="Empty CSV file"
            fi
        else
            echo "  ❌ CSV file is empty"
            analysis_data="Empty CSV file"
        fi
        ;;
        
    txt|md)
        echo ""
        echo "📄 Text Analysis:"
        echo "================"
        
        if [ -s "$FILE" ]; then
            word_count=$(wc -w < "$FILE")
            line_count=$(wc -l < "$FILE")
            char_count=$(wc -c < "$FILE")
            
            echo "  📝 Words: $word_count"
            echo "  📄 Lines: $line_count"
            echo "  🔤 Characters: $char_count"
            
            # Extract first few lines for analysis
            preview=$(head -10 "$FILE" | tr '\n' ' ')
            analysis_data="Text file with $word_count words, $line_count lines. Preview: ${preview:0:500}..."
        else
            echo "  ❌ Text file is empty"
            analysis_data="Empty text file"
        fi
        ;;
        
    *)
        echo ""
        echo "⚠️  Unknown file type: $file_ext"
        echo "Attempting generic text analysis..."
        
        # Try to read as text
        if [ -s "$FILE" ]; then
            preview=$(head -5 "$FILE" 2>/dev/null | tr '\n' ' ')
            analysis_data="Unknown file type ($file_ext). Content preview: ${preview:0:300}..."
        else
            analysis_data="Unknown or empty file type: $file_ext"
        fi
        ;;
esac

# Run AI analysis if we have meaningful data
if [ ${#analysis_data} -gt 50 ]; then
    echo ""
    echo "🎭 Running AI Analysis..."
    echo "========================"
    
    # Create analysis topic for CoD Protocol
    analysis_topic="Analyze this data file and provide insights: File: $FILE, Type: $file_ext, Data: $analysis_data"
    
    # Run CoD analysis
    debate_output=$(make debate TOPIC="$analysis_topic" 2>&1)
    debate_exit_code=$?
    
    if [ $debate_exit_code -eq 0 ]; then
        echo "✅ AI analysis completed"
        
        # Find the latest debate file
        debate_file=$(ls -t data/debates/task_*_results.json 2>/dev/null | head -1)
        
        # Create comprehensive analysis report
        analysis_file="data/analysis/${TASK_ID}_analysis.json"
        
        # Read original file data
        if [ "$file_ext" = "json" ] && jq . "$FILE" >/dev/null 2>&1; then
            file_data=$(cat "$FILE")
        else
            # For non-JSON files, store as string
            file_data=$(jq -Rs . "$FILE")
        fi
        
        # Combine file and analysis results
        jq -n \
            --arg task_id "$TASK_ID" \
            --arg file_path "$FILE" \
            --arg file_type "$file_ext" \
            --arg file_size "$file_size" \
            --arg timestamp "$(date -Iseconds)" \
            --argjson file_data "$file_data" \
            --argjson ai_analysis "$(cat "$debate_file" 2>/dev/null || echo '{}')" \
            '{
                task_id: $task_id,
                file_path: $file_path,
                file_type: $file_type,
                file_size: $file_size,
                timestamp: $timestamp,
                analysis_type: "ai_enhanced",
                file_data: $file_data,
                ai_analysis: $ai_analysis,
                summary: {
                    confidence: $ai_analysis.confidence_score,
                    insights: $ai_analysis.consensus,
                    recommendations: $ai_analysis.explanation
                }
            }' > "$analysis_file"
        
        echo ""
        echo "📊 Analysis Complete!"
        echo "===================="
        
        if [ -f "$debate_file" ]; then
            confidence=$(jq -r '.confidence_score // "unknown"' "$debate_file")
            echo "🎯 AI Confidence: ${confidence}%"
            
            echo ""
            echo "💡 Key Insights:"
            echo "================"
            jq -r '.consensus // "No insights available"' "$debate_file" 2>/dev/null || echo "Analysis data not available"
            
            echo ""
            echo "📋 Recommendations:"
            echo "=================="
            
            echo ""
            echo "💰 Business Perspective:"
            jq -r '.explanation.forCFO // "Not available"' "$debate_file" 2>/dev/null || echo "Not available"
            
            echo ""
            echo "🔧 Technical Perspective:"
            jq -r '.explanation.forCTO // "Not available"' "$debate_file" 2>/dev/null || echo "Not available"
        fi
        
        echo ""
        echo "💾 Complete analysis saved to: $analysis_file"
        
    else
        echo "⚠️  AI analysis failed, providing basic file summary"
        
        # Create basic analysis report
        analysis_file="data/analysis/${TASK_ID}_analysis.json"
        
        jq -n \
            --arg task_id "$TASK_ID" \
            --arg file_path "$FILE" \
            --arg file_type "$file_ext" \
            --arg file_size "$file_size" \
            --arg timestamp "$(date -Iseconds)" \
            --arg analysis_data "$analysis_data" \
            '{
                task_id: $task_id,
                file_path: $file_path,
                file_type: $file_type,
                file_size: $file_size,
                timestamp: $timestamp,
                analysis_type: "basic_summary",
                file_data: null,
                ai_analysis: null,
                summary: {
                    basic_info: $analysis_data,
                    note: "AI analysis not available"
                }
            }' > "$analysis_file"
        
        echo ""
        echo "📊 Basic Analysis Summary:"
        echo "========================="
        echo "$analysis_data"
        
        echo ""
        echo "💾 Basic analysis saved to: $analysis_file"
    fi
    
else
    echo ""
    echo "⚠️  Insufficient data for meaningful analysis"
    
    # Create minimal analysis report
    analysis_file="data/analysis/${TASK_ID}_analysis.json"
    
    jq -n \
        --arg task_id "$TASK_ID" \
        --arg file_path "$FILE" \
        --arg file_type "$file_ext" \
        --arg file_size "$file_size" \
        --arg timestamp "$(date -Iseconds)" \
        '{
            task_id: $task_id,
            file_path: $file_path,
            file_type: $file_type,
            file_size: $file_size,
            timestamp: $timestamp,
            analysis_type: "insufficient_data",
            summary: {
                note: "File contains insufficient data for analysis"
            }
        }' > "$analysis_file"
    
    echo "💾 Minimal analysis saved to: $analysis_file"
fi

log_success "analyze-data" "Analysis completed: $FILE"