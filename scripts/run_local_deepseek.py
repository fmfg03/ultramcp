#!/usr/bin/env python3
"""
Script para ejecutar modelo DeepSeek local en formato .gguf

Recibe parámetros como JSON desde stdin y devuelve respuesta como JSON
Optimizado para matemáticas y lógica compleja
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
    """Carga el modelo DeepSeek desde el archivo .gguf"""
    try:
        # Configuración optimizada para DeepSeek (matemáticas y lógica)
        model = Llama(
            model_path=model_path,
            n_ctx=8192,  # Contexto amplio para problemas complejos
            n_threads=8,  # Máximo threads para cálculos intensivos
            n_gpu_layers=0,  # CPU only por defecto
            verbose=False,
            use_mmap=True,
            use_mlock=True,
            rope_scaling_type=1,  # Optimización para secuencias largas
            **kwargs
        )
        return model
    except Exception as e:
        raise Exception(f"Error cargando modelo DeepSeek: {str(e)}")

def generate_response(model, prompt, max_tokens=512, temperature=0.3, **kwargs):
    """Genera respuesta usando el modelo DeepSeek"""
    try:
        # Formato de prompt optimizado para DeepSeek (matemáticas/lógica)
        if any(keyword in prompt.lower() for keyword in ['matemática', 'cálculo', 'ecuación', 'demostrar', 'paradoja']):
            formatted_prompt = f"""Problem: {prompt}

Solution: Let me solve this step by step.

"""
        else:
            formatted_prompt = f"""User: {prompt}

