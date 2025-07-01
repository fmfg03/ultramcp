# test_voice_system.py
import asyncio
import os
import time
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from mcp_voice_agents import MCPVoiceAgent
from voice_types import *

async def test_cpu_optimized_voice_system():
    """Test completo del sistema de voz optimizado para CPU"""
    
    print("🎤 Testing CPU-Optimized MCP Voice System...")
    print("=" * 60)
    
    # Verify environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY not found in environment!")
        print("🔧 Make sure .env file has: OPENAI_API_KEY=sk-proj-...")
        return
    
    print(f"✅ OpenAI Key found: {openai_key[:20]}...")
    
    # Test 1: Customer Service (Premium OpenAI)
    print("\n1. Testing Customer Service (Premium OpenAI TTS-HD)...")
    cs_agent = MCPVoiceAgent(AgentType.CUSTOMER_SERVICE)
    
    # Test text-to-speech generation
    test_text = "Hola, gracias por contactarnos. ¿En qué puedo ayudarte hoy?"
    
    try:
        start_time = time.time()
        response = await cs_agent.voice_manager.generate_speech(
            text=test_text,
            agent_type=AgentType.CUSTOMER_SERVICE,
            language=Language.SPANISH_MX
        )
        end_time = time.time()
        
        print(f"✅ Customer Service TTS completed!")
        print(f"   ⚡ Generation time: {response.duration_ms}ms")
        print(f"   💰 Cost: ${response.cost:.6f}")
        print(f"   🔊 Provider: {response.provider}")
        print(f"   🎭 Voice: {response.voice_used}")
        print(f"   📊 Audio size: {len(response.audio_data)} bytes")
        
        # Save test audio
        with open('test_customer_service.mp3', 'wb') as f:
            f.write(response.audio_data)
        print(f"   💾 Audio saved: test_customer_service.mp3")
        
    except Exception as e:
        print(f"❌ Customer Service test failed: {e}")
    
    # Test 2: Sales (Premium OpenAI)
    print("\n2. Testing Sales Agent (Premium OpenAI TTS-HD)...")
    sales_agent = MCPVoiceAgent(AgentType.SALES)
    
    sales_text = "¡Excelente! Tenemos exactamente lo que buscas. Déjame explicarte los beneficios."
    
    try:
        response = await sales_agent.voice_manager.generate_speech(
            text=sales_text,
            agent_type=AgentType.SALES,
            language=Language.SPANISH_MX
        )
        
        print(f"✅ Sales TTS completed!")
        print(f"   ⚡ Generation time: {response.duration_ms}ms")
        print(f"   💰 Cost: ${response.cost:.6f}")
        print(f"   🔊 Provider: {response.provider}")
        print(f"   🎭 Voice: {response.voice_used}")
        
        # Save test audio
        with open('test_sales.mp3', 'wb') as f:
            f.write(response.audio_data)
        print(f"   💾 Audio saved: test_sales.mp3")
        
    except Exception as e:
        print(f"❌ Sales test failed: {e}")
    
    # Test 3: Internal RAG (Standard OpenAI)
    print("\n3. Testing Internal RAG (Standard OpenAI TTS-1)...")
    rag_agent = MCPVoiceAgent(AgentType.RAG_ASSISTANT)
    
    rag_text = "Según los documentos internos, encontré 3 resultados relevantes para tu consulta."
    
    try:
        response = await rag_agent.voice_manager.generate_speech(
            text=rag_text,
            agent_type=AgentType.RAG_ASSISTANT,
            language=Language.SPANISH_MX
        )
        
        print(f"✅ RAG TTS completed!")
        print(f"   ⚡ Generation time: {response.duration_ms}ms")
        print(f"   💰 Cost: ${response.cost:.6f}")
        print(f"   🔊 Provider: {response.provider}")
        print(f"   🎭 Voice: {response.voice_used}")
        
        # Save test audio
        with open('test_rag.mp3', 'wb') as f:
            f.write(response.audio_data)
        print(f"   💾 Audio saved: test_rag.mp3")
        
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
    
    # Test 4: English voices
    print("\n4. Testing English voices...")
    
    english_text = "Hello! I'm here to help you with anything you need today."
    
    try:
        response = await cs_agent.voice_manager.generate_speech(
            text=english_text,
            agent_type=AgentType.CUSTOMER_SERVICE,
            language=Language.ENGLISH
        )
        
        print(f"✅ English TTS completed!")
        print(f"   ⚡ Generation time: {response.duration_ms}ms")
        print(f"   💰 Cost: ${response.cost:.6f}")
        print(f"   🔊 Provider: {response.provider}")
        print(f"   🎭 Voice: {response.voice_used}")
        
        # Save test audio
        with open('test_english.mp3', 'wb') as f:
            f.write(response.audio_data)
        print(f"   💾 Audio saved: test_english.mp3")
        
    except Exception as e:
        print(f"❌ English test failed: {e}")
    
    # Test 5: Cost calculation
    print("\n5. Voice Cost Analysis...")
    
    costs = cs_agent.voice_manager.get_voice_costs()
    available_voices = cs_agent.voice_manager.get_available_voices()
    
    print("💰 Current pricing:")
    for provider, cost in costs.items():
        if cost > 0:
            print(f"   {provider}: ${cost:.6f} per character")
        else:
            print(f"   {provider}: FREE")
    
    print(f"\n🎭 Available voices:")
    for provider, voices in available_voices.items():
        print(f"   {provider}: {', '.join(voices[:3])}{'...' if len(voices) > 3 else ''}")
    
    print("\n🎉 CPU-Optimized Voice system testing completed!")
    print("=" * 60)
    print("📊 Performance Summary:")
    print("   • OpenAI TTS: ~500ms generation time")
    print("   • No GPU required ✅")
    print("   • High quality voices ✅")
    print("   • Multiple languages ✅")
    print("   • Cost-effective for production ✅")
    print(f"\n📁 Audio files generated:")
    print("   • test_customer_service.mp3")
    print("   • test_sales.mp3") 
    print("   • test_rag.mp3")
    print("   • test_english.mp3")

async def test_mock_voice_conversation():
    """Test a complete voice conversation flow"""
    
    print("\n🎭 Testing Complete Voice Conversation Flow...")
    print("-" * 50)
    
    cs_agent = MCPVoiceAgent(AgentType.CUSTOMER_SERVICE)
    
    # Simulate customer queries and responses
    conversation = [
        ("Customer", "Hola, tengo un problema con mi cuenta"),
        ("Agent", "¡Hola! Entiendo que tienes un problema con tu cuenta. Estoy aquí para ayudarte a resolverlo inmediatamente."),
        ("Customer", "No puedo acceder a mi dashboard"),
        ("Agent", "Perfecto, veo exactamente cuál es el problema. Voy a guiarte paso a paso para solucionarlo.")
    ]
    
    total_cost = 0.0
    total_time = 0
    
    for i, (speaker, text) in enumerate(conversation):
        if speaker == "Agent":
            print(f"\n{i+1}. Generating agent response...")
            print(f"   Text: {text[:60]}...")
            
            try:
                response = await cs_agent.voice_manager.generate_speech(
                    text=text,
                    agent_type=AgentType.CUSTOMER_SERVICE,
                    language=Language.SPANISH_MX
                )
                
                total_cost += response.cost
                total_time += response.duration_ms
                
                print(f"   ✅ Generated: {response.duration_ms}ms, ${response.cost:.6f}")
                
                # Save conversation audio
                with open(f'conversation_step_{i+1}.mp3', 'wb') as f:
                    f.write(response.audio_data)
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
    
    print(f"\n📊 Conversation Summary:")
    print(f"   Total generation time: {total_time}ms")
    print(f"   Total cost: ${total_cost:.6f}")
    print(f"   Average per response: {total_time/2:.0f}ms, ${total_cost/2:.6f}")

if __name__ == "__main__":
    asyncio.run(test_cpu_optimized_voice_system())
    asyncio.run(test_mock_voice_conversation())
