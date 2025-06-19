#!/usr/bin/env python3
"""
Script para ejecutar modelo LLaMA local en formato .gguf

Recibe parámetros como JSON desde stdin y devuelve respuesta como JSON
Optimizado para comprensión y generación de texto
"""

import sys
import json
import time
import os
from pathlib import Path

try:
    from llama_cpp import Llama
except ImportError:
    print(json.dumps({
        "success": False,
        "error": "llama-cpp-python no está instalado. Ejecuta: pip install llama-cpp-python"
    }))
    sys.exit(1)

def load_model(model_path, **kwargs):
    """Carga el modelo LLaMA desde el archivo .gguf"""
    try:
        # Configuración optimizada para LLaMA
        model = Llama(
            model_path=model_path,
            n_ctx=4096,  # Contexto más amplio para LLaMA
            n_threads=6,  # Más threads para mejor rendimiento
            n_gpu_layers=0,  # CPU only por defecto
            verbose=False,
            use_mmap=True,  # Usar memory mapping para eficiencia
            use_mlock=True,  # Lock memory para estabilidad
            **kwargs
        )
        return model
    except Exception as e:
        raise Exception(f"Error cargando modelo LLaMA: {str(e)}")

def generate_response(model, prompt, max_tokens=512, temperature=0.7, **kwargs):
    """Genera respuesta usando el modelo LLaMA"""
    try:
        # Formato de prompt para LLaMA (estilo chat)
        formatted_prompt = f"""### Human: {prompt}

### Assistant: """
        
        start_time = time.time()
        
        # Generar respuesta
        response = model(
            formatted_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.95,
            top_k=50,
            repeat_penalty=1.05,
            stop=["### Human:", "### Assistant:", "\n\n###"],
            echo=False
        )
        
        generation_time = time.time() - start_time
        
        # Extraer texto de respuesta
        response_text = response['choices'][0]['text'].strip()
        
        # Limpiar respuesta de artefactos
        if response_text.startswith("### Assistant:"):
            response_text = response_text[14:].strip()
        
        # Calcular tokens (estimación mejorada)
        prompt_tokens = len(formatted_prompt.split())
        completion_tokens = len(response_text.split())
        
        return {
            "response": response_text,
            "promptTokens": prompt_tokens,
            "completionTokens": completion_tokens,
            "totalTokens": prompt_tokens + completion_tokens,
            "generationTime": generation_time,
            "model": "llama-local"
        }
        
    except Exception as e:
        raise Exception(f"Error generando respuesta: {str(e)}")

def main():
    """Función principal"""
    try:
        # Leer parámetros desde stdin
        input_data = sys.stdin.read().strip()
        if not input_data:
            raise Exception("No se recibieron parámetros")
        
        params = json.loads(input_data)
        
        # Validar parámetros requeridos
        required_params = ['prompt', 'modelPath']
        for param in required_params:
            if param not in params:
                raise Exception(f"Parámetro requerido faltante: {param}")
        
        prompt = params['prompt']
        model_path = params['modelPath']
        max_tokens = params.get('maxTokens', 512)
        temperature = params.get('temperature', 0.7)
        session_id = params.get('sessionId', 'unknown')
        
        # Verificar que existe el archivo del modelo
        if not os.path.exists(model_path):
            # Intentar paths alternativos para LLaMA
            alternative_paths = [
                'models/llama-2-7b-chat.Q4_K_M.gguf',
                'models/llama-2-7b.Q4_K_M.gguf',
                'models/llama-7b.Q4_K_M.gguf',
                'models/llama.gguf'
            ]
            
            model_found = False
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    model_path = alt_path
                    model_found = True
                    break
            
            if not model_found:
                raise Exception(f"Archivo de modelo no encontrado: {model_path}")
        
        # Cargar modelo
        model = load_model(model_path)
        
        # Generar respuesta
        result = generate_response(
            model, 
            prompt, 
            max_tokens=max_tokens, 
            temperature=temperature
        )
        
        # Agregar metadata
        result.update({
            "success": True,
            "sessionId": session_id,
            "modelPath": model_path,
            "timestamp": time.time()
        })
        
        # Devolver resultado como JSON
        print(json.dumps(result, ensure_ascii=False))
        
    except json.JSONDecodeError as e:
        error_response = {
            "success": False,
            "error": f"Error parseando JSON: {str(e)}",
            "model": "llama-local"
        }
        print(json.dumps(error_response))
        sys.exit(1)
        
    except Exception as e:
        error_response = {
            "success": False,
            "error": str(e),
            "model": "llama-local"
        }
        print(json.dumps(error_response))
        sys.exit(1)

if __name__ == "__main__":
    main()

