#!/usr/bin/env python3
import asyncio
import subprocess
import os
from mcp_voice_agents import MCPVoiceAgent
from voice_types import *

async def create_audio_file(text, filename):
    """Crear archivo de audio con eSpeak"""
    subprocess.run([
        "espeak-ng", "-v", "es-mx", "-s", "150", 
        text, "--stdout"
    ], stdout=open(filename, 'wb'))
    print(f"🔊 Created: {filename}")

async def test_conversation():
    print("🎭 Testing REAL Voice Conversation...")
    print("=" * 50)
    
    agent = MCPVoiceAgent(AgentType.CUSTOMER_SERVICE)
    
    # Crear queries de prueba
    customer_queries = [
        "Hola, tengo un problema con mi cuenta bancaria",
        "No puedo acceder a mi banca en línea desde ayer",
        "Me dice que mi contraseña es incorrecta pero estoy seguro que es la correcta"
    ]
    
    total_cost = 0
    
    for i, query in enumerate(customer_queries):
        print(f"\n--- Conversación {i+1} ---")
        print(f"Cliente dice: '{query}'")
        
        # Crear audio del cliente
        input_file = f"customer_query_{i+1}.wav"
        await create_audio_file(query, input_file)
        
        # Leer audio
        with open(input_file, 'rb') as f:
            audio_data = f.read()
        
        # Procesar con el agente
        response = await agent.handle_customer_service_call(
            audio_input=audio_data,
            user_id=f"customer_{i+1}",
            language=Language.SPANISH_MX
        )
        
        # Guardar respuesta del agente
        response_file = f"agent_response_{i+1}.mp3"
        with open(response_file, 'wb') as f:
            f.write(response.audio_data)
        
        total_cost += response.cost
        
        print(f"✅ Respuesta generada: {response.duration_ms}ms, ${response.cost:.6f}")
        print(f"💾 Archivos: {input_file} -> {response_file}")
        
        # Limpiar archivo temporal
        os.remove(input_file)
    
    print(f"\n📊 Conversación completa:")
    print(f"   Total cost: ${total_cost:.6f}")
    print(f"   Archivos generados: agent_response_1.mp3, agent_response_2.mp3, agent_response_3.mp3")

if __name__ == "__main__":
    asyncio.run(test_conversation())
