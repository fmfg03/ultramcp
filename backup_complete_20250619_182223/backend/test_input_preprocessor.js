const InputPreprocessorService = require("./src/services/InputPreprocessorService.js");
const fs = require("fs");
const path = require("path");

const UPLOAD_DIR_FOR_TEST = "/home/ubuntu/project/uploads/";

async function runTests() {
    console.log("--- Starting InputPreprocessorService Tests ---");

    // Ensure upload directory exists for test files
    if (!fs.existsSync(UPLOAD_DIR_FOR_TEST)) {
        fs.mkdirSync(UPLOAD_DIR_FOR_TEST, { recursive: true });
    }

    // Test Case 1: Simple text input (below thresholds)
    console.log("\n--- Test Case 1: Simple Text ---");
    let result1 = await InputPreprocessorService.process("Hello world, this is a simple test.");
    console.log("Result 1:", JSON.stringify(result1, null, 2));

    // Test Case 2: Long text input (above word/char threshold for rephrasing)
    console.log("\n--- Test Case 2: Long Text for Rephrasing ---");
    const longText = "This is a very long text input that is designed to exceed the one hundred word limit or the seven hundred character limit to trigger the LLM rephrasing logic. We need to ensure that the rephrasing mechanism is invoked correctly and that the output reflects this. Let's add some more words to make absolutely sure we cross the threshold. This sentence should definitely do it, as it contains many words and characters, pushing it well beyond the specified limits for automatic rephrasing by the language model integrated within the preprocessor service.";
    let result2 = await InputPreprocessorService.process(longText);
    console.log("Result 2:", JSON.stringify(result2, null, 2));

    // Test Case 3: Text input with conditional keywords
    console.log("\n--- Test Case 3: Text with Conditional Keywords ---");
    let result3 = await InputPreprocessorService.process("If the weather is good, then we will go to the park, but only if it's not raining.");
    console.log("Result 3:", JSON.stringify(result3, null, 2));

    // Test Case 4: Text input with JSON
    console.log("\n--- Test Case 4: Text with JSON ---");
    const textWithJson = 'Here is some data: { "name": "Test User", "id": 123, "active": true }. And some more text.';
    let result4 = await InputPreprocessorService.process(textWithJson);
    console.log("Result 4:", JSON.stringify(result4, null, 2));

    // Test Case 5: Text input with CSV-like data
    console.log("\n--- Test Case 5: Text with CSV-like data ---");
    const textWithCsv = "Review this data:\nid,name,value\n1,itemA,100\n2,itemB,200\n3,itemC,300";
    let result5 = await InputPreprocessorService.process(textWithCsv);
    console.log("Result 5:", JSON.stringify(result5, null, 2));

    // Test Case 6: Text input with URL
    console.log("\n--- Test Case 6: Text with URL ---");
    const textWithUrl = "Check out this website: https://www.example.com for more information.";
    let result6 = await InputPreprocessorService.process(textWithUrl);
    console.log("Result 6:", JSON.stringify(result6, null, 2));

    // Test Case 7: Text input with a mix of JSON and URL
    console.log("\n--- Test Case 7: Text with JSON and URL ---");
    const textWithMix = 'Data: { "item": "sample" }, Link: http://anotherexample.com/path?query=true';
    let result7 = await InputPreprocessorService.process(textWithMix);
    console.log("Result 7:", JSON.stringify(result7, null, 2));

    // Test Case 8: File handling simulation
    console.log("\n--- Test Case 8: File Handling Simulation ---");
    // Create dummy files for testing
    const dummyFile1Path = path.join(UPLOAD_DIR_FOR_TEST, "test_file1.txt");
    const dummyFile2Path = path.join(UPLOAD_DIR_FOR_TEST, "test_file2.json");
    const dummyFile3Path_large = path.join(UPLOAD_DIR_FOR_TEST, "large_file.bin");
    const dummyFile4Path_invalid_ext = path.join(UPLOAD_DIR_FOR_TEST, "script.js");
    const dummyFile5Path_md_script = path.join(UPLOAD_DIR_FOR_TEST, "doc_with_script.md");

    fs.writeFileSync(dummyFile1Path, "This is a test text file.");
    fs.writeFileSync(dummyFile2Path, JSON.stringify({ "data": "sample json" }));
    // Create a large file ( > 10MB is too slow, simulate with size property)
    // fs.writeFileSync(dummyFile3Path_large, Buffer.alloc(11 * 1024 * 1024)); 
    fs.writeFileSync(dummyFile4Path_invalid_ext, "alert('hello');");
    fs.writeFileSync(dummyFile5Path_md_script, "# Markdown\nSome text <script>alert('danger')</script> more text.");

    const filesToProcess = [
        { tempFilePath: dummyFile1Path, originalFilename: "test_file1.txt", size: fs.statSync(dummyFile1Path).size },
        { tempFilePath: dummyFile2Path, originalFilename: "test_file2.json", size: fs.statSync(dummyFile2Path).size },
        { tempFilePath: "/tmp/placeholder_large.bin", originalFilename: "large_file.bin", size: 11 * 1024 * 1024 }, // Simulate large file via size prop
        { tempFilePath: dummyFile4Path_invalid_ext, originalFilename: "script.js", size: fs.statSync(dummyFile4Path_invalid_ext).size },
        { tempFilePath: dummyFile5Path_md_script, originalFilename: "doc_with_script.md", size: fs.statSync(dummyFile5Path_md_script).size },
    ];
    let result8 = await InputPreprocessorService.process("Processing files attached.", filesToProcess);
    console.log("Result 8 (File Handling):", JSON.stringify(result8, null, 2));

    // Clean up dummy files (actual processed files by the service are in UPLOAD_DIR)
    // The service moves files, so original tempFilePaths might not exist if they were actual temp files.
    // For this test, dummyFile1Path, dummyFile2Path etc. were used as tempFilePaths and then moved.
    // So we check the target paths in UPLOAD_DIR for cleanup.
    console.log("\nCleaning up test files...");
    const finalFile1 = path.join(UPLOAD_DIR_FOR_TEST, InputPreprocessorService._sanitizeFilename("test_file1.txt"));
    const finalFile2 = path.join(UPLOAD_DIR_FOR_TEST, InputPreprocessorService._sanitizeFilename("test_file2.json"));
    // large_file.bin and script.js should have been rejected
    // doc_with_script.md should have been rejected and deleted by the service
    if (fs.existsSync(finalFile1)) fs.unlinkSync(finalFile1);
    if (fs.existsSync(finalFile2)) fs.unlinkSync(finalFile2);
    if (fs.existsSync(dummyFile4Path_invalid_ext)) fs.unlinkSync(dummyFile4Path_invalid_ext); // if it wasn't moved/deleted
    const finalMdScriptPath = path.join(UPLOAD_DIR_FOR_TEST, InputPreprocessorService._sanitizeFilename("doc_with_script.md"));
    if (fs.existsSync(finalMdScriptPath)) fs.unlinkSync(finalMdScriptPath); // if it wasn't deleted by service
    if (fs.existsSync(dummyFile5Path_md_script)) fs.unlinkSync(dummyFile5Path_md_script); // original if not moved


    console.log("\n--- InputPreprocessorService Tests Completed ---");
}

runTests().catch(error => console.error("Error during tests:", error));

