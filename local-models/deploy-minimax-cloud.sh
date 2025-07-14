#!/bin/bash
echo "🌍 Deploy MiniMax-M1-80k to cloud..."
echo "Choose your platform:"
echo "1. AWS EC2 with Terraform"
echo "2. Google Cloud with Terraform" 
echo "3. Manual setup guide"
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "🚀 AWS deployment..."
        cd ../cloud-virtualization/terraform/aws
        terraform init
        terraform apply -var="instance_type=p3.8xlarge" -var="model=minimax-m1-80k"
        ;;
    2)
        echo "🔮 GCP deployment..."
        cd ../cloud-virtualization/terraform/gcp
        terraform init
        terraform apply -var="machine_type=n1-highmem-32" -var="gpu_type=nvidia-tesla-v100" -var="gpu_count=4"
        ;;
    3)
        echo "📖 Manual setup guide:"
        echo "1. Launch GPU instance (p3.8xlarge or equivalent)"
        echo "2. Install CUDA, PyTorch, vLLM"
        echo "3. Download model: huggingface-cli download MiniMaxAI/MiniMax-M1-80k"
        echo "4. Start server: python -m vllm.entrypoints.openai.api_server --model MiniMaxAI/MiniMax-M1-80k"
        ;;
esac
