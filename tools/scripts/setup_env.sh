#!/bin/bash
# Environment Setup Script for Developers

echo "🔧 Setting up environment files..."

# Copy .env.example to .env if doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env from template"
    echo "⚠️  EDIT .env with your actual API keys before running the system"
else
    echo "⚠️  .env already exists"
fi

# Copy voice system env
if [ ! -f voice_system/.env ]; then
    cp voice_system/config/.env.example voice_system/.env
    echo "✅ Created voice_system/.env from template" 
    echo "⚠️  EDIT voice_system/.env with your OpenAI API key"
else
    echo "⚠️  voice_system/.env already exists"
fi

echo ""
echo "🔑 NEXT STEPS:"
echo "1. Edit .env with your actual API keys"
echo "2. Edit voice_system/.env with your OpenAI API key"
echo "3. Never commit .env files to git"
echo ""
echo "📚 See .env.example for all required variables"
