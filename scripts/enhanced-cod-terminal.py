#!/usr/bin/env python3
"""
Terminal interface for Enhanced CoD Protocol with Local LLMs
Optimized for Claude Code integration
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the services directory to Python path
sys.path.append(str(Path(__file__).parent.parent / 'services' / 'cod-protocol'))

try:
    from enhanced_orchestrator import EnhancedCoDOrchestrator, DebateMode, ParticipantConfig
except ImportError:
    print("❌ Enhanced orchestrator not found. Please run the setup script first.")
    sys.exit(1)

async def main():
    parser = argparse.ArgumentParser(description='Enhanced CoD Protocol Terminal Interface')
    parser.add_argument('--topic', required=True, help='Debate topic')
    parser.add_argument('--mode', default='hybrid', 
                       choices=['hybrid', 'local_only', 'api_only', 'cost_optimized', 'privacy_first'],
                       help='Debate mode')
    parser.add_argument('--participants', nargs='+', help='Specific participants')
    parser.add_argument('--rounds', type=int, default=2, help='Number of rounds')
    parser.add_argument('--output', help='Output file for results')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    config = {
        'max_rounds': args.rounds,
        'consensus_threshold': 0.75,
        'enable_local_models': True
    }
    
    orchestrator = EnhancedCoDOrchestrator(config)
    
    try:
        print("🎭 Initializing Enhanced CoD Protocol...")
        await orchestrator.initialize()
        
        # Convert mode string to enum
        mode = DebateMode(args.mode)
        
        # Prepare task
        task = {
            'task_id': f"terminal_debate_{int(datetime.now().timestamp())}",
            'content': args.topic
        }
        
        print(f"\n📋 Starting debate: {args.topic}")
        print(f"🔧 Mode: {mode.value}")
        print(f"🔄 Rounds: {args.rounds}")
        
        # Run debate
        result = await orchestrator.run_cod_session(
            task,
            mode=mode,
            participants=args.participants,
            auto_select=True
        )
        
        # Display results
        print("\n" + "="*60)
        print("🎯 DEBATE RESULTS")
        print("="*60)
        
        print(f"\n💭 Consensus:")
        print(f"   {result.get('consensus', 'No consensus reached')}")
        
        print(f"\n📊 Confidence: {result.get('confidence_score', 0):.1f}%")
        
        # Cost and privacy metrics
        metadata = result.get('metadata', {})
        print(f"\n💰 Cost: ${metadata.get('total_cost', 0):.4f}")
        print(f"🔒 Privacy Score: {metadata.get('privacy_score', 0)*100:.1f}%")
        
        # Model usage
        local_used = metadata.get('local_models_used', 0)
        api_used = metadata.get('api_models_used', 0)
        
        print(f"\n🤖 Models Used:")
        print(f"   Local: {local_used}")
        print(f"   API: {api_used}")
        
        # Save results
        results_dir = Path("data/local_cod_debates")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        default_file = results_dir / f"{result['task_id']}_results.json"
        with open(default_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {default_file}")
        
    except KeyboardInterrupt:
        print("\n🛑 Debate interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
