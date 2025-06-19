const mcpBrokerService = require("./mcpBrokerService.js"); // Assuming this path is correct for actual LLM calls
const fs = require("fs");
const path = require("path");

const UPLOAD_DIR = "/home/ubuntu/project/uploads/";
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB
const ALLOWED_EXTENSIONS = [".json", ".csv", ".txt", ".md", ".pdf"];

class InputPreprocessorService {
  constructor() {
    console.log("InputPreprocessorService initialized.");
    this.conditionalKeywords = ["and", "if", "then", "but", "or", "when", "unless", "else"];
    if (!fs.existsSync(UPLOAD_DIR)) {
      fs.mkdirSync(UPLOAD_DIR, { recursive: true });
      console.log(`InputPreprocessorService: Created upload directory at ${UPLOAD_DIR}`);
    }
  }

  _shouldRephrase(textInput) {
    if (!textInput || typeof textInput !== "string") {
      return false;
    }
    const wordCount = textInput.split(/\s+/).length;
    const charCount = textInput.length;
    if (wordCount > 100 || charCount > 700) {
      return true;
    }
    const lowercasedInput = textInput.toLowerCase();
    for (const keyword of this.conditionalKeywords) {
      if (lowercasedInput.includes(` ${keyword} `) || lowercasedInput.startsWith(`${keyword} `) || lowercasedInput.endsWith(` ${keyword}`)) {
        return true;
      }
    }
    return false;
  }

  async _rephraseInputWithLLM(textInput) {
    console.log("InputPreprocessorService: Simulating LLM rephrasing for:", textInput);
    // In a real scenario, this would call an LLM (e.g., via mcpBrokerService or a direct SDK)
    return {
      rephrasedText: `(LLM-Rephrased) ${textInput}`,
      llm_used: "claude-3-sonnet-simulated-rephrase"
    };
  }

  _sanitizeFilename(filename) {
    return path.basename(filename).replace(/[^a-zA-Z0-9._-]/g, "_").substring(0, 255);
  }

  async _handleFileUploads(uploadedFiles) {
    if (!uploadedFiles || !Array.isArray(uploadedFiles) || uploadedFiles.length === 0) {
      return [];
    }
    const processedFilePaths = [];
    const errors = [];
    for (const file of uploadedFiles) {
      const originalFilename = file.originalFilename || path.basename(file.tempFilePath);
      const sanitizedFilename = this._sanitizeFilename(originalFilename);
      const targetPath = path.join(UPLOAD_DIR, sanitizedFilename);
      const extension = path.extname(originalFilename).toLowerCase();
      let fileSize = file.size;
      if (!fileSize && file.tempFilePath && fs.existsSync(file.tempFilePath)) {
          try {
              fileSize = fs.statSync(file.tempFilePath).size;
          } catch (statError) {
              errors.push(`Error stating file ${originalFilename}: ${statError.message}`);
              continue;
          }
      }
      if (!ALLOWED_EXTENSIONS.includes(extension)) {
        errors.push(`File type not allowed: ${originalFilename} (extension: ${extension})`);
        continue;
      }
      if (fileSize > MAX_FILE_SIZE_BYTES) {
        errors.push(`File too large: ${originalFilename} (size: ${fileSize} bytes)`);
        continue;
      }
      try {
        if (file.tempFilePath && fs.existsSync(file.tempFilePath)) {
            fs.renameSync(file.tempFilePath, targetPath);
            console.log(`InputPreprocessorService: File moved to ${targetPath}`);
        } else {
            fs.writeFileSync(targetPath, file.content || "Simulated file content");
            console.log(`InputPreprocessorService: File created/simulated at ${targetPath}`);
        }
        processedFilePaths.push(targetPath);
        if (extension === ".md") {
          const content = fs.readFileSync(targetPath, "utf-8");
          if (/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script\s*>/gi.test(content)) {
            errors.push(`Potential script detected in Markdown file: ${originalFilename}. File quarantined/rejected.`);
            fs.unlinkSync(targetPath);
            processedFilePaths.pop();
            console.warn(`InputPreprocessorService: Potential script in ${originalFilename}, file removed.`);
          }
        }
      } catch (moveError) {
        errors.push(`Error processing file ${originalFilename}: ${moveError.message}`);
      }
    }
    if (errors.length > 0) {
        console.warn("InputPreprocessorService: Errors during file handling:", errors);
    }
    return processedFilePaths;
  }

  _extractJson(textInput) {
    const jsonObjects = [];
    const jsonRegex = /({(?:[^{}]|\"|\\|\n|\r|\t)*?}|\G\[(?:[^\[\]]|\"|\\|\n|\r|\t)*?\])/g;
    let match;
    while ((match = jsonRegex.exec(textInput)) !== null) {
        try {
            const potentialJson = match[0].trim();
            if ((potentialJson.startsWith("{") && potentialJson.endsWith("}")) || (potentialJson.startsWith("[") && potentialJson.endsWith("]"))) {
                const parsed = JSON.parse(potentialJson);
                jsonObjects.push({ type: "json", value: parsed });
            }
        } catch (e) {}
    }
    return jsonObjects;
  }

  _extractCsv(textInput) {
    const detectedCsv = [];
    const lines = textInput.trim().split(/\r?\n/);
    if (lines.length >= 2) {
        const firstLineCommas = (lines[0].match(/,/g) || []).length;
        if (firstLineCommas > 0) {
            let consistentCommas = true;
            for (let i = 1; i < lines.length; i++) {
                if ((lines[i].match(/,/g) || []).length !== firstLineCommas) {
                    consistentCommas = false;
                    break;
                }
            }
            if (consistentCommas) {
                detectedCsv.push({ type: "csv", value: textInput });
                return detectedCsv;
            }
        }
    }
    const commonHeaders = ["id", "name", "email", "date", "value", "category"];
    const firstLine = lines[0].toLowerCase();
    if (commonHeaders.some(header => firstLine.includes(header))) {
        if (lines.length >=1 && (firstLine.match(/,/g) || []).length > 0) {
             detectedCsv.push({ type: "csv", value: textInput });
        }
    }
    return detectedCsv;
  }

  _extractUrls(textInput) {
    const urls = [];
    const urlRegex = /https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)/gi;
    let match;
    while ((match = urlRegex.exec(textInput)) !== null) {
      urls.push({ type: "url", value: match[0] });
    }
    return urls;
  }

  async _extractStructuredData(textInput) {
    if (typeof textInput !== "string" || !textInput.trim()) {
        return [];
    }
    console.log("InputPreprocessorService: Attempting to extract structured data.");
    const allStructuredData = [];
    allStructuredData.push(...this._extractJson(textInput));
    allStructuredData.push(...this._extractCsv(textInput));
    allStructuredData.push(...this._extractUrls(textInput));
    console.log("InputPreprocessorService: Extracted structured data:", allStructuredData);
    return allStructuredData;
  }

  async _determineIntentAndRoute(textInput, files, structuredData) {
    console.log("InputPreprocessorService: Determining intent and route for:", textInput);
    const lowerInput = textInput.toLowerCase();
    let routingDecision;

    // Rule for Embedding Search (if files are present or specific keywords)
    if (files && files.length > 0) {
        routingDecision = {
            adapter_id: "embedding_search",
            confidence: 0.8,
            reasoning: "Files present in input, suggesting a need for document-based search/retrieval.",
            llm_used: "keyword-based-router-v1"
        };
        console.log("Routing to embedding_search due to file presence.");
        return routingDecision;
    }
    const embeddingKeywords = ["search my documents", "find in my knowledge base", "relevant files for", "based on my uploads"];
    if (embeddingKeywords.some(kw => lowerInput.includes(kw))) {
        routingDecision = {
            adapter_id: "embedding_search",
            confidence: 0.75,
            reasoning: `Keyword match for embedding search: ${embeddingKeywords.find(kw => lowerInput.includes(kw))}`,
            llm_used: "keyword-based-router-v1"
        };
        console.log(`Routing to embedding_search due to keyword: ${routingDecision.reasoning}`);
        return routingDecision;
    }

    // Rule for Web Search
    const webSearchKeywords = ["search for", "what is", "who is", "find information on", "latest news", "look up", "google"];
    if (webSearchKeywords.some(kw => lowerInput.includes(kw))) {
        routingDecision = {
            adapter_id: "claude_web_search",
            confidence: 0.8,
            reasoning: `Keyword match for web search: ${webSearchKeywords.find(kw => lowerInput.includes(kw))}`,
            llm_used: "keyword-based-router-v1"
        };
        console.log(`Routing to claude_web_search due to keyword: ${routingDecision.reasoning}`);
        return routingDecision;
    }

    // Rule for Tool Agent (complex tasks) - Primary Keywords
    const toolAgentKeywords = ["book a", "schedule a", "order a", "plan my", "organize a", "execute task", "create a plan", "generate a report that involves", "help me with a multi-step process"];
    if (toolAgentKeywords.some(kw => lowerInput.includes(kw))) {
        routingDecision = {
            adapter_id: "claude_tool_agent",
            confidence: 0.75, 
            reasoning: `Explicit keyword match for tool agent: ${toolAgentKeywords.find(kw => lowerInput.includes(kw))}`,
            llm_used: "keyword-based-router-v1"
        };
        console.log(`Routing to claude_tool_agent due to explicit keyword: ${routingDecision.reasoning}`);
        return routingDecision;
    }

    // Rule for Tool Agent (complex tasks) - Secondary: Conditional Keywords + Complexity
    const containsConditional = this.conditionalKeywords.some(kw => 
        lowerInput.includes(` ${kw} `) || lowerInput.startsWith(`${kw} `) || lowerInput.endsWith(` ${kw}`)
    );
    const wordCount = textInput.split(/\s+/).length;
    if (containsConditional && wordCount > 7) { 
        routingDecision = {
            adapter_id: "claude_tool_agent",
            confidence: 0.65, 
            reasoning: `Conditional keyword match suggesting complex task: ${this.conditionalKeywords.find(kw => lowerInput.includes(` ${kw} `) || lowerInput.startsWith(`${kw} `) || lowerInput.endsWith(` ${kw}`))}`,
            llm_used: "keyword-based-router-v1"
        };
        console.log(`Routing to claude_tool_agent due to conditional keyword(s) and complexity: ${routingDecision.reasoning}`);
        return routingDecision;
    }
    
    // If the query is very short and simple, it might be a direct question for a general LLM.
    if (wordCount < 5 && !structuredData.length && !files.length) {
        routingDecision = {
            adapter_id: "default_llm_service", 
            confidence: 0.6,
            reasoning: "Short, simple query, likely a direct question.",
            llm_used: "keyword-based-router-v1"
        };
        console.log("Routing to default_llm_service (or orchestrator) for simple query.");
        return routingDecision;
    }

    // Default route if no other rules matched
    routingDecision = {
        adapter_id: "orchestration_service", 
        confidence: 0.5,
        reasoning: "Default route, no specific keywords matched for specialized adapters.",
        llm_used: "keyword-based-router-v1"
    };
    console.log("Default routing decision applied.");
    return routingDecision;
  }

  async process(rawData, filesToProcess = []) {
    console.log("InputPreprocessorService: Processing raw data:", rawData, "Files:", filesToProcess);
    const originalInputText = typeof rawData === "string" ? rawData : rawData.text || JSON.stringify(rawData);

    const processedData = {
      original_input: originalInputText,
      cleaned_prompt: originalInputText,
      structured_data: [],
      files: [],
      llm_used_rephrase: null,
      routing_decision: null,
    };

    if (this._shouldRephrase(originalInputText)) {
      console.log("InputPreprocessorService: Rephrasing conditions met.");
      try {
        const llmResponse = await this._rephraseInputWithLLM(originalInputText);
        processedData.cleaned_prompt = llmResponse.rephrasedText;
        processedData.llm_used_rephrase = llmResponse.llm_used;
        console.log("InputPreprocessorService: Input rephrased by LLM.");
      } catch (error) {
        console.error("InputPreprocessorService: Error during LLM rephrasing:", error);
      }
    }

    if (filesToProcess && filesToProcess.length > 0) {
        try {
            const savedFilePaths = await this._handleFileUploads(filesToProcess);
            processedData.files = savedFilePaths;
            console.log("InputPreprocessorService: Files processed:", savedFilePaths);
        } catch (fileError) {
            console.error("InputPreprocessorService: Error during file processing step:", fileError);
        }
    }

    try {
        const structuredItems = await this._extractStructuredData(processedData.cleaned_prompt);
        processedData.structured_data = structuredItems;
    } catch (structDataError) {
        console.error("InputPreprocessorService: Error during structured data extraction:", structDataError);
    }

    try {
        const routing = await this._determineIntentAndRoute(processedData.cleaned_prompt, processedData.files, processedData.structured_data);
        processedData.routing_decision = routing;
        console.log("InputPreprocessorService: Intent determined and route suggested:", routing);
    } catch (routingError) {
        console.error("InputPreprocessorService: Error during intent determination:", routingError);
        processedData.routing_decision = {
            adapter_id: "orchestration_service",
            confidence: 0.0,
            reasoning: "Error during intent determination, falling back to default.",
            llm_used: "error_fallback"
        };
    }

    console.log("InputPreprocessorService: Processed data output:", processedData);
    return processedData;
  }
}

module.exports = new InputPreprocessorService();

