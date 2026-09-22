#!/bin/bash

echo "🔍 Verifying LLM Integration Setup..."
echo ""

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    
    # Check if API key is configured (not the placeholder)
    if grep -q "OPENAI_API_KEY=sk-" .env; then
        echo "✅ API key appears to be configured"
    elif grep -q "OPENAI_API_KEY=your_api_key_here" .env; then
        echo "⚠️  API key is still placeholder - replace with your actual key"
    else
        echo "⚠️  API key format not recognized"
    fi
else
    echo "❌ .env file not found"
fi

echo ""
echo "📁 Checking Swift files..."

# Check if all required Swift files exist
files=(
    "nextmove/Services/ConfigurationManager.swift"
    "nextmove/Services/LLMService.swift"
    "nextmove/Services/EnhancedCoachingEngine.swift"
    "nextmove/Services/AnalysisPipeline+LLM.swift"
    "nextmoveTests/LLMServiceTests.swift"
    "nextmoveTests/ConfigurationManagerTests.swift"
)

all_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
        all_exist=false
    fi
done

echo ""
echo "📝 Checking RecordingViewModel integration..."

if grep -q "AnalysisPipeline.withLLMCoaching" "nextmove/ViewModels/RecordingViewModel.swift"; then
    echo "✅ RecordingViewModel uses LLM-enhanced pipeline"
else
    echo "❌ RecordingViewModel not updated"
fi

if grep -q "checkLLMConfiguration" "nextmove/ViewModels/RecordingViewModel.swift"; then
    echo "✅ Configuration check added"
else
    echo "⚠️  Configuration check not found"
fi

echo ""
echo "📚 Documentation files..."

docs=(
    "QUICKSTART_LLM.md"
    "README_LLM_SETUP.md"
    "CODE_CHANGES_REQUIRED.md"
    "INTEGRATION_CHECKLIST.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "✅ $doc"
    else
        echo "⚠️  $doc (missing)"
    fi
done

echo ""
echo "═══════════════════════════════════════"
echo "Summary:"
echo "═══════════════════════════════════════"

if [ "$all_exist" = true ]; then
    echo "✅ All Swift files present"
else
    echo "⚠️  Some Swift files missing - add them to Xcode"
fi

echo ""
echo "Next steps:"
echo "1. Open nextmove.xcodeproj in Xcode"
echo "2. Add your OpenAI API key to .env file"
echo "3. Build the project (⌘B)"
echo "4. Run tests (⌘U)"
echo "5. Run the app and check console for LLM status"
echo ""
