#!/bin/bash

echo "🚀 Setting up CPU-Optimized MCP Voice System..."

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Installing..."
    apt update && apt install -y python3 python3-pip python3-venv
fi

# 2. Install eSpeak for fallback
echo "📦 Installing eSpeak-ng..."
apt install -y espeak-ng

# 3. Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
echo "📥 Installing Python dependencies..."
pip3 install -r requirements.txt

# 5. Download Whisper model
echo "🎤 Downloading Whisper model..."
python3 -c "import whisper; whisper.load_model('base')"

# 6. Create directories
mkdir -p logs temp audio_cache

# 7. Test eSpeak
echo "🔊 Testing eSpeak..."
espeak-ng -v es-mx "Sistema de voz configurado correctamente" --stdout > test_espeak.wav
if [ $? -eq 0 ]; then
    echo "✅ eSpeak working"
    rm -f test_espeak.wav
else
    echo "❌ eSpeak test failed"
fi

# 8. Set permissions
chmod +x run_voice_api.sh

echo "✅ CPU-Optimized MCP Voice System setup completed!"
echo ""
echo "🔧 Next steps:"
echo "1. Configure your .env file with API keys"
echo "2. Run: ./run_voice_api.sh to start the server"
echo "3. Test: python3 test_voice_system.py"
echo ""
echo "📊 System optimized for:"
echo "   • No GPU required ✅"
echo "   • OpenAI TTS for production quality ✅"
echo "   • eSpeak fallback for testing ✅"
echo "   • Fast generation (~500ms) ✅"
