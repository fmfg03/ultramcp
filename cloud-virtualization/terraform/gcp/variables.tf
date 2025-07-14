# UltraMCP GCP Infrastructure Variables

variable "project_id" {
  description = "The GCP project ID"
  type        = string
  validation {
    condition     = length(var.project_id) > 0
    error_message = "Project ID must be provided."
  }
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "europe-west1"
  validation {
    condition = can(regex("^[a-z]+-[a-z]+[0-9]$", var.region))
    error_message = "Region must be a valid GCP region format."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# Network Configuration
variable "subnet_cidr" {
  description = "CIDR block for the subnet"
  type        = string
  default     = "10.1.0.0/24"
  validation {
    condition     = can(cidrhost(var.subnet_cidr, 0))
    error_message = "Subnet CIDR must be a valid IPv4 CIDR block."
  }
}

variable "pods_cidr" {
  description = "CIDR block for Kubernetes pods (secondary range)"
  type        = string
  default     = "10.2.0.0/16"
}

variable "services_cidr" {
  description = "CIDR block for Kubernetes services (secondary range)"
  type        = string
  default     = "10.3.0.0/16"
}

# Compute Configuration
variable "machine_type" {
  description = "Machine type for instances"
  type        = string
  default     = "e2-standard-2"
  validation {
    condition = can(regex("^[a-z0-9]+-[a-z0-9]+-[0-9]+$", var.machine_type))
    error_message = "Machine type must be a valid GCP machine type."
  }
}

variable "root_disk_size" {
  description = "Root disk size in GB"
  type        = number
  default     = 50
  validation {
    condition     = var.root_disk_size >= 20 && var.root_disk_size <= 2000
    error_message = "Root disk size must be between 20 and 2000 GB."
  }
}

# Auto-scaling Configuration
variable "min_size" {
  description = "Minimum number of instances in the instance group"
  type        = number
  default     = 1
  validation {
    condition     = var.min_size >= 1 && var.min_size <= 100
    error_message = "Minimum size must be between 1 and 100."
  }
}

variable "max_size" {
  description = "Maximum number of instances in the instance group"
  type        = number
  default     = 10
  validation {
    condition     = var.max_size >= 1 && var.max_size <= 1000
    error_message = "Maximum size must be between 1 and 1000."
  }
}

variable "initial_size" {
  description = "Initial number of instances in the instance group"
  type        = number
  default     = 2
  validation {
    condition     = var.initial_size >= 1
    error_message = "Initial size must be at least 1."
  }
}

# UltraMCP Configuration
variable "supabase_url" {
  description = "Supabase URL for UltraMCP services"
  type        = string
  validation {
    condition     = can(regex("^https://.*\\.supabase\\.co$", var.supabase_url))
    error_message = "Supabase URL must be a valid Supabase URL."
  }
}

variable "supabase_anon_key" {
  description = "Supabase anonymous key"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.supabase_anon_key) > 50
    error_message = "Supabase anonymous key must be provided."
  }
}

variable "docker_compose_url" {
  description = "URL to the docker-compose configuration"
  type        = string
  default     = "https://raw.githubusercontent.com/your-org/ultramcp/main/docker-compose.hybrid.yml"
  validation {
    condition     = can(regex("^https://", var.docker_compose_url))
    error_message = "Docker compose URL must be a valid HTTPS URL."
  }
}

# SSL Configuration
variable "enable_ssl" {
  description = "Enable SSL certificate and HTTPS load balancer"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Domain name for the SSL certificate and load balancer"
  type        = string
  default     = "ultramcp.example.com"
  validation {
    condition     = can(regex("^[a-z0-9.-]+\\.[a-z]{2,}$", var.domain_name))
    error_message = "Domain name must be a valid domain."
  }
}

# Database Configuration
variable "create_database" {
  description = "Whether to create a Cloud SQL PostgreSQL instance"
  type        = bool
  default     = false
}

variable "db_tier" {
  description = "Database tier for Cloud SQL instance"
  type        = string
  default     = "db-f1-micro"
  validation {
    condition = contains([
      "db-f1-micro", "db-g1-small", "db-custom-1-3840", 
      "db-custom-2-7680", "db-custom-4-15360"
    ], var.db_tier)
    error_message = "Database tier must be a valid Cloud SQL tier."
  }
}

variable "db_disk_size" {
  description = "Database disk size in GB"
  type        = number
  default     = 20
  validation {
    condition     = var.db_disk_size >= 10 && var.db_disk_size <= 10000
    error_message = "Database disk size must be between 10 and 10000 GB."
  }
}

# Labels and Tags
variable "labels" {
  description = "Additional labels to apply to resources"
  type        = map(string)
  default     = {}
  validation {
    condition = length(var.labels) <= 64
    error_message = "Maximum of 64 labels allowed."
  }
}

# Cost Management
variable "enable_preemptible" {
  description = "Use preemptible instances for cost savings"
  type        = bool
  default     = false
}

variable "enable_spot" {
  description = "Use spot instances for cost savings"
  type        = bool
  default     = false
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Enable enhanced monitoring and logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 30
  validation {
    condition     = var.log_retention_days >= 1 && var.log_retention_days <= 365
    error_message = "Log retention must be between 1 and 365 days."
  }
}