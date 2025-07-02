/**
 * UltraMCP Agent Types for Claudia Integration
 * 
 * Defines specialized agent types that leverage UltraMCP's hybrid local+API capabilities
 * for visual multi-LLM debate management, cost optimization, and privacy-first processing.
 */

import { z } from 'zod';

// =============================================================================
// BASE TYPES
// =============================================================================

export enum LocalModelType {
  QWEN_25_14B = 'qwen2.5:14b',
  LLAMA_31_8B = 'llama3.1:8b', 
  QWEN_CODER_7B = 'qwen-coder:7b',
  MISTRAL_7B = 'mistral:7b',
  DEEPSEEK_CODER_6_7B = 'deepseek-coder:6.7b'
}

export enum DebateRole {
  CFO = 'CFO',
  CTO = 'CTO', 
  ANALYST = 'Analyst',
  VISIONARY = 'Visionary',
  CRITIC = 'Devil\'s Advocate',
  MODERATOR = 'Moderator'
}

export enum DebateMode {
  LOCAL_ONLY = 'local_only',
  HYBRID = 'hybrid',
  PRIVACY_FIRST = 'privacy_first',
  COST_OPTIMIZED = 'cost_optimized'
}

export enum AgentType {
  COD_DEBATE = 'cod-debate',
  LOCAL_LLM = 'local-llm',
  HYBRID_DECISION = 'hybrid-decision',
  PRIVACY_GUARDIAN = 'privacy-guardian',
  COST_OPTIMIZER = 'cost-optimizer'
}

// =============================================================================
// VALIDATION SCHEMAS
// =============================================================================

const LocalModelSchema = z.nativeEnum(LocalModelType);
const DebateRoleSchema = z.nativeEnum(DebateRole);
const DebateModeSchema = z.nativeEnum(DebateMode);
const AgentTypeSchema = z.nativeEnum(AgentType);

// =============================================================================
// AGENT CONFIGURATIONS
// =============================================================================

/**
 * Chain-of-Debate Protocol Agent
 * Orchestrates multi-LLM debates with specialized roles and intelligent consensus building
 */
export interface CoDAgent {
  type: AgentType.COD_DEBATE;
  name: string;
  description: string;
  icon: string;
  
  // Debate Configuration
  debateRole: DebateRole;
  participants: LocalModelType[];
  mode: DebateMode;
  
  // Quality Controls
  confidenceThreshold: number; // 0.0 - 1.0
  maxRounds: number; // 1-10
  consensusRequired: boolean;
  
  // Cost & Privacy
  maxCostPerDebate: number; // USD
  privacyMode: boolean;
  auditTrail: boolean;
  
  // Performance
  responseTimeout: number; // seconds
  enableParallelProcessing: boolean;
  
  // System Prompt Template
  systemPrompt: string;
  roleContext: string;
}

/**
 * Local LLM Agent  
 * Direct interface to UltraMCP's local models with privacy and performance optimization
 */
export interface LocalLLMAgent {
  type: AgentType.LOCAL_LLM;
  name: string;
  description: string;
  icon: string;
  
  // Model Configuration
  model: LocalModelType;
  specialization: 'coding' | 'analysis' | 'strategy' | 'rapid' | 'architecture';
  
  // Privacy & Security
  privacyMode: boolean;
  offlineOnly: boolean;
  sandboxed: boolean;
  
  // Performance Tuning
  temperature: number; // 0.0 - 1.0
  maxTokens: number;
  responseTimeout: number;
  
  // Usage Controls
  rateLimitPerHour: number;
  usageTracking: boolean;
  
  // System Configuration
  systemPrompt: string;
  contextLength: number;
}

/**
 * Hybrid Decision Agent
 * Intelligent routing between local and API models based on cost, privacy, and quality requirements
 */
export interface HybridAgent {
  type: AgentType.HYBRID_DECISION;
  name: string;
  description: string;
  icon: string;
  
  // Decision Logic
  localFirst: boolean;
  costBudget: number; // USD per session
  privacyRequirement: 'low' | 'medium' | 'high';
  qualityThreshold: number; // 0.0 - 1.0
  
  // Fallback Strategy
  fallbackStrategy: 'local_only' | 'api_only' | 'mixed' | 'escalate';
  escalationThreshold: number;
  
  // Model Selection
  preferredLocalModels: LocalModelType[];
  preferredAPIModels: string[];
  
  // Optimization
  adaptiveLearning: boolean;
  performanceTracking: boolean;
  costOptimization: boolean;
  
  // Configuration
  systemPrompt: string;
  decisionCriteria: string[];
}

/**
 * Privacy Guardian Agent
 * Ensures compliance with privacy requirements and data sovereignty
 */
export interface PrivacyGuardianAgent {
  type: AgentType.PRIVACY_GUARDIAN;
  name: string;
  description: string;
  icon: string;
  
  // Privacy Controls
  dataClassification: 'public' | 'internal' | 'confidential' | 'restricted';
  localProcessingOnly: boolean;
  auditLogging: boolean;
  dataRetention: number; // days
  
  // Compliance
  gdprCompliant: boolean;
  hipaaCompliant: boolean;
  soc2Compliant: boolean;
  
  // Monitoring
  privacyScoring: boolean;
  complianceReporting: boolean;
  alertThresholds: {
    externalDataTransfer: boolean;
    apiUsage: boolean;
    dataRetention: boolean;
  };
  
  // Configuration
  systemPrompt: string;
  compliancePolicies: string[];
}

/**
 * Cost Optimizer Agent
 * Minimizes costs while maintaining quality through intelligent model selection and usage patterns
 */
export interface CostOptimizerAgent {
  type: AgentType.COST_OPTIMIZER;
  name: string;
  description: string;
  icon: string;
  
  // Cost Controls
  dailyBudget: number; // USD
  costPerToken: Record<string, number>;
  savingsTarget: number; // percentage
  
  // Optimization Strategy
  preferLocalModels: boolean;
  dynamicPricing: boolean;
  batchProcessing: boolean;
  cacheResults: boolean;
  
  // Quality Balance
  qualityFloor: number; // minimum acceptable quality 0.0-1.0
  costQualityRatio: number;
  fallbackBehavior: 'maintain_quality' | 'minimize_cost' | 'balanced';
  
  // Analytics
  trackingEnabled: boolean;
  reportingFrequency: 'daily' | 'weekly' | 'monthly';
  optimizationMetrics: string[];
  
  // Configuration
  systemPrompt: string;
  optimizationRules: string[];
}

// =============================================================================
// UNIFIED AGENT TYPE
// =============================================================================

export type UltraMCPAgent = 
  | CoDAgent 
  | LocalLLMAgent 
  | HybridAgent 
  | PrivacyGuardianAgent 
  | CostOptimizerAgent;

// =============================================================================
// AGENT TEMPLATES
// =============================================================================

/**
 * Pre-configured agent templates for common use cases
 */
export const AgentTemplates = {
  // Strategic Decision Making
  STRATEGIC_COD: {
    type: AgentType.COD_DEBATE,
    name: 'Strategic Decision Maker',
    description: 'Multi-LLM debate for complex business decisions',
    icon: '🎯',
    debateRole: DebateRole.CFO,
    participants: [LocalModelType.QWEN_25_14B, LocalModelType.LLAMA_31_8B],
    mode: DebateMode.HYBRID,
    confidenceThreshold: 0.85,
    maxRounds: 3,
    consensusRequired: true,
    maxCostPerDebate: 0.50,
    privacyMode: false,
    auditTrail: true,
    responseTimeout: 60,
    enableParallelProcessing: true,
    systemPrompt: 'You are a strategic business advisor participating in a multi-perspective analysis...',
    roleContext: 'Focus on financial implications, risk assessment, and long-term strategic value.'
  } as CoDAgent,

  // Privacy-First Technical Analysis
  PRIVACY_TECHNICAL: {
    type: AgentType.LOCAL_LLM,
    name: 'Privacy-First Technical Analyst',
    description: 'Local-only technical analysis with maximum privacy',
    icon: '🔒',
    model: LocalModelType.QWEN_CODER_7B,
    specialization: 'coding',
    privacyMode: true,
    offlineOnly: true,
    sandboxed: true,
    temperature: 0.3,
    maxTokens: 4000,
    responseTimeout: 30,
    rateLimitPerHour: 100,
    usageTracking: true,
    systemPrompt: 'You are a technical expert specializing in secure, privacy-first code analysis...',
    contextLength: 32000
  } as LocalLLMAgent,

  // Cost-Optimized Research
  COST_OPTIMIZED_RESEARCH: {
    type: AgentType.HYBRID_DECISION,
    name: 'Cost-Optimized Researcher',
    description: 'Intelligent cost optimization for research tasks',
    icon: '💰',
    localFirst: true,
    costBudget: 1.00,
    privacyRequirement: 'medium',
    qualityThreshold: 0.8,
    fallbackStrategy: 'mixed',
    escalationThreshold: 0.9,
    preferredLocalModels: [LocalModelType.MISTRAL_7B, LocalModelType.LLAMA_31_8B],
    preferredAPIModels: ['gpt-4', 'claude-3-sonnet'],
    adaptiveLearning: true,
    performanceTracking: true,
    costOptimization: true,
    systemPrompt: 'You intelligently route tasks between local and API models to optimize cost while maintaining quality...',
    decisionCriteria: ['cost_per_token', 'response_quality', 'privacy_requirement', 'processing_speed']
  } as HybridAgent,

  // Enterprise Compliance Guardian
  ENTERPRISE_GUARDIAN: {
    type: AgentType.PRIVACY_GUARDIAN,
    name: 'Enterprise Compliance Guardian',
    description: 'Ensures enterprise compliance and data sovereignty',
    icon: '🛡️',
    dataClassification: 'confidential',
    localProcessingOnly: true,
    auditLogging: true,
    dataRetention: 90,
    gdprCompliant: true,
    hipaaCompliant: false,
    soc2Compliant: true,
    privacyScoring: true,
    complianceReporting: true,
    alertThresholds: {
      externalDataTransfer: true,
      apiUsage: true,
      dataRetention: true
    },
    systemPrompt: 'You are responsible for ensuring all AI interactions comply with enterprise privacy and security policies...',
    compliancePolicies: ['data_sovereignty', 'audit_trail', 'encryption_at_rest', 'access_control']
  } as PrivacyGuardianAgent,

  // Budget-Conscious Assistant
  BUDGET_ASSISTANT: {
    type: AgentType.COST_OPTIMIZER,
    name: 'Budget-Conscious Assistant',
    description: 'Minimizes costs while maintaining productivity',
    icon: '📊',
    dailyBudget: 5.00,
    costPerToken: {
      'local': 0.0,
      'gpt-4': 0.03,
      'claude-3-sonnet': 0.015
    },
    savingsTarget: 80,
    preferLocalModels: true,
    dynamicPricing: true,
    batchProcessing: true,
    cacheResults: true,
    qualityFloor: 0.75,
    costQualityRatio: 0.8,
    fallbackBehavior: 'balanced',
    trackingEnabled: true,
    reportingFrequency: 'daily',
    optimizationMetrics: ['cost_per_task', 'quality_score', 'response_time', 'local_usage_percentage'],
    systemPrompt: 'You optimize AI task execution to minimize costs while maintaining acceptable quality levels...',
    optimizationRules: ['prefer_local_models', 'batch_similar_requests', 'cache_frequent_patterns', 'escalate_only_when_necessary']
  } as CostOptimizerAgent
};

// =============================================================================
// VALIDATION FUNCTIONS
// =============================================================================

/**
 * Validates an UltraMCP agent configuration
 */
export function validateAgent(agent: Partial<UltraMCPAgent>): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // Basic validation
  if (!agent.type) errors.push('Agent type is required');
  if (!agent.name || agent.name.trim().length === 0) errors.push('Agent name is required');
  if (!agent.description) errors.push('Agent description is required');

  // Type-specific validation
  switch (agent.type) {
    case AgentType.COD_DEBATE:
      const codAgent = agent as CoDAgent;
      if (!codAgent.participants || codAgent.participants.length === 0) {
        errors.push('CoD agent must have at least one participant');
      }
      if (codAgent.confidenceThreshold && (codAgent.confidenceThreshold < 0 || codAgent.confidenceThreshold > 1)) {
        errors.push('Confidence threshold must be between 0 and 1');
      }
      break;

    case AgentType.LOCAL_LLM:
      const localAgent = agent as LocalLLMAgent;
      if (!localAgent.model) {
        errors.push('Local LLM agent must specify a model');
      }
      if (localAgent.temperature && (localAgent.temperature < 0 || localAgent.temperature > 1)) {
        errors.push('Temperature must be between 0 and 1');
      }
      break;

    case AgentType.HYBRID_DECISION:
      const hybridAgent = agent as HybridAgent;
      if (hybridAgent.costBudget && hybridAgent.costBudget < 0) {
        errors.push('Cost budget must be non-negative');
      }
      break;
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Gets the icon for an agent type
 */
export function getAgentTypeIcon(type: AgentType): string {
  const iconMap = {
    [AgentType.COD_DEBATE]: '🎭',
    [AgentType.LOCAL_LLM]: '🤖',
    [AgentType.HYBRID_DECISION]: '🔀',
    [AgentType.PRIVACY_GUARDIAN]: '🛡️',
    [AgentType.COST_OPTIMIZER]: '💰'
  };
  return iconMap[type] || '🤖';
}

/**
 * Gets the color scheme for an agent type
 */
export function getAgentTypeColor(type: AgentType): string {
  const colorMap = {
    [AgentType.COD_DEBATE]: '#8B5CF6', // purple
    [AgentType.LOCAL_LLM]: '#10B981', // green
    [AgentType.HYBRID_DECISION]: '#F59E0B', // amber
    [AgentType.PRIVACY_GUARDIAN]: '#3B82F6', // blue
    [AgentType.COST_OPTIMIZER]: '#EF4444' // red
  };
  return colorMap[type] || '#6B7280';
}

// =============================================================================
// EXPORT SCHEMAS FOR RUNTIME VALIDATION
// =============================================================================

export const CoDAgentSchema = z.object({
  type: z.literal(AgentType.COD_DEBATE),
  name: z.string().min(1),
  description: z.string(),
  icon: z.string(),
  debateRole: DebateRoleSchema,
  participants: z.array(LocalModelSchema).min(1),
  mode: DebateModeSchema,
  confidenceThreshold: z.number().min(0).max(1),
  maxRounds: z.number().min(1).max(10),
  consensusRequired: z.boolean(),
  maxCostPerDebate: z.number().min(0),
  privacyMode: z.boolean(),
  auditTrail: z.boolean(),
  responseTimeout: z.number().min(1),
  enableParallelProcessing: z.boolean(),
  systemPrompt: z.string(),
  roleContext: z.string()
});

export const LocalLLMAgentSchema = z.object({
  type: z.literal(AgentType.LOCAL_LLM),
  name: z.string().min(1),
  description: z.string(),
  icon: z.string(),
  model: LocalModelSchema,
  specialization: z.enum(['coding', 'analysis', 'strategy', 'rapid', 'architecture']),
  privacyMode: z.boolean(),
  offlineOnly: z.boolean(),
  sandboxed: z.boolean(),
  temperature: z.number().min(0).max(1),
  maxTokens: z.number().min(1),
  responseTimeout: z.number().min(1),
  rateLimitPerHour: z.number().min(1),
  usageTracking: z.boolean(),
  systemPrompt: z.string(),
  contextLength: z.number().min(1)
});

export type { CoDAgent, LocalLLMAgent, HybridAgent, PrivacyGuardianAgent, CostOptimizerAgent };