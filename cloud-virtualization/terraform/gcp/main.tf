# UltraMCP Google Cloud Platform Infrastructure
# Multi-region deployment with auto-scaling and load balancing

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  default_labels = {
    project     = "ultramcp"
    environment = var.environment
    managed-by  = "terraform"
  }
}

# Data sources
data "google_compute_zones" "available" {
  region = var.region
}

# VPC Network
resource "google_compute_network" "ultramcp_network" {
  name                    = "ultramcp-network-${var.environment}"
  auto_create_subnetworks = false
  mtu                     = 1460
}

# Subnet
resource "google_compute_subnetwork" "ultramcp_subnet" {
  name          = "ultramcp-subnet-${var.environment}"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.ultramcp_network.id

  secondary_ip_range = {
    range_name    = "ultramcp-pods"
    ip_cidr_range = var.pods_cidr
  }

  secondary_ip_range = {
    range_name    = "ultramcp-services"
    ip_cidr_range = var.services_cidr
  }
}

# Cloud Router for NAT Gateway
resource "google_compute_router" "ultramcp_router" {
  name    = "ultramcp-router-${var.environment}"
  region  = var.region
  network = google_compute_network.ultramcp_network.id
}

# NAT Gateway
resource "google_compute_router_nat" "ultramcp_nat" {
  name                               = "ultramcp-nat-${var.environment}"
  router                             = google_compute_router.ultramcp_router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Firewall Rules
resource "google_compute_firewall" "ultramcp_web_fw" {
  name    = "ultramcp-web-fw-${var.environment}"
  network = google_compute_network.ultramcp_network.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "3000", "3001"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["ultramcp-web"]

  description = "Allow HTTP/HTTPS and UltraMCP WebUI traffic"
}

resource "google_compute_firewall" "ultramcp_app_fw" {
  name    = "ultramcp-app-fw-${var.environment}"
  network = google_compute_network.ultramcp_network.name

  allow {
    protocol = "tcp"
    ports    = ["8001", "8002", "8003", "8004", "8005", "8006", "8007", "8008", "8009", "8010", "8011", "8012", "8013"]
  }

  source_tags = ["ultramcp-web"]
  target_tags = ["ultramcp-app"]

  description = "Allow UltraMCP service communication"
}

resource "google_compute_firewall" "ultramcp_ssh_fw" {
  name    = "ultramcp-ssh-fw-${var.environment}"
  network = google_compute_network.ultramcp_network.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = [var.subnet_cidr]
  target_tags   = ["ultramcp-app"]

  description = "Allow SSH access from within VPC"
}

# Instance Template
resource "google_compute_instance_template" "ultramcp_template" {
  name_prefix  = "ultramcp-template-"
  description  = "UltraMCP instance template for ${var.environment}"
  machine_type = var.machine_type
  
  tags = ["ultramcp-app"]

  disk {
    source_image = "ubuntu-os-cloud/ubuntu-2204-lts"
    auto_delete  = true
    boot         = true
    disk_size_gb = var.root_disk_size
    disk_type    = "pd-ssd"
  }

  network_interface {
    subnetwork = google_compute_subnetwork.ultramcp_subnet.id
    # No external IP for security
  }

  metadata = {
    enable-oslogin = "TRUE"
    startup-script = templatefile("${path.module}/startup.sh", {
      supabase_url           = var.supabase_url
      supabase_key          = var.supabase_anon_key
      environment           = var.environment
      node_role             = "worker"
      docker_compose_url    = var.docker_compose_url
      project_id            = var.project_id
    })
  }

  service_account {
    email  = google_service_account.ultramcp_sa.email
    scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring.write"
    ]
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Service Account
resource "google_service_account" "ultramcp_sa" {
  account_id   = "ultramcp-sa-${var.environment}"
  display_name = "UltraMCP Service Account"
  description  = "Service account for UltraMCP instances"
}

# IAM bindings for service account
resource "google_project_iam_member" "ultramcp_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.ultramcp_sa.email}"
}

resource "google_project_iam_member" "ultramcp_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.ultramcp_sa.email}"
}

# Health Check
resource "google_compute_health_check" "ultramcp_hc" {
  name                = "ultramcp-hc-${var.environment}"
  description         = "Health check for UltraMCP services"
  timeout_sec         = 10
  check_interval_sec  = 30
  healthy_threshold   = 2
  unhealthy_threshold = 3

  http_health_check {
    port               = 3000
    request_path       = "/health"
    proxy_header       = "NONE"
    response           = ""
  }
}

# Instance Group Manager
resource "google_compute_instance_group_manager" "ultramcp_igm" {
  name               = "ultramcp-igm-${var.environment}"
  zone               = data.google_compute_zones.available.names[0]
  base_instance_name = "ultramcp-instance"
  target_size        = var.initial_size

  version {
    instance_template = google_compute_instance_template.ultramcp_template.id
  }

  named_port {
    name = "http"
    port = 3000
  }

  named_port {
    name = "https"
    port = 443
  }

  auto_healing_policies {
    health_check      = google_compute_health_check.ultramcp_hc.id
    initial_delay_sec = 300
  }

  update_policy {
    type                           = "PROACTIVE"
    instance_redistribution_type   = "PROACTIVE"
    minimal_action                 = "REPLACE"
    most_disruptive_allowed_action = "REPLACE"
    max_surge_fixed                = 3
    max_unavailable_fixed          = 1
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Autoscaler
resource "google_compute_autoscaler" "ultramcp_autoscaler" {
  name   = "ultramcp-autoscaler-${var.environment}"
  zone   = data.google_compute_zones.available.names[0]
  target = google_compute_instance_group_manager.ultramcp_igm.id

  autoscaling_policy {
    max_replicas    = var.max_size
    min_replicas    = var.min_size
    cooldown_period = 300

    cpu_utilization {
      target = 0.7
    }

    load_balancing_utilization {
      target = 0.8
    }

    metric {
      name   = "compute.googleapis.com/instance/network/received_bytes_count"
      type   = "GAUGE"
      target = 1000000  # 1MB/s
    }
  }
}

# Global Load Balancer Components
resource "google_compute_global_address" "ultramcp_ip" {
  name         = "ultramcp-ip-${var.environment}"
  description  = "Global IP for UltraMCP load balancer"
  address_type = "EXTERNAL"
}

# Backend Service
resource "google_compute_backend_service" "ultramcp_backend" {
  name                  = "ultramcp-backend-${var.environment}"
  description           = "UltraMCP backend service"
  protocol              = "HTTP"
  port_name             = "http"
  timeout_sec           = 30
  enable_cdn            = true
  load_balancing_scheme = "EXTERNAL"

  backend {
    group           = google_compute_instance_group_manager.ultramcp_igm.instance_group
    balancing_mode  = "UTILIZATION"
    max_utilization = 0.8
    capacity_scaler = 1.0
  }

  health_checks = [google_compute_health_check.ultramcp_hc.id]

  cdn_policy {
    cache_mode                   = "CACHE_ALL_STATIC"
    default_ttl                  = 3600
    max_ttl                      = 86400
    negative_caching             = true
    serve_while_stale            = 86400
    signed_url_cache_max_age_sec = 7200

    cache_key_policy {
      include_host         = true
      include_protocol     = true
      include_query_string = false
    }
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

# URL Map
resource "google_compute_url_map" "ultramcp_url_map" {
  name            = "ultramcp-url-map-${var.environment}"
  description     = "URL map for UltraMCP services"
  default_service = google_compute_backend_service.ultramcp_backend.id

  host_rule {
    hosts        = [var.domain_name]
    path_matcher = "allpaths"
  }

  path_matcher {
    name            = "allpaths"
    default_service = google_compute_backend_service.ultramcp_backend.id

    path_rule {
      paths   = ["/api/*"]
      service = google_compute_backend_service.ultramcp_backend.id
    }

    path_rule {
      paths   = ["/health"]
      service = google_compute_backend_service.ultramcp_backend.id
    }
  }
}

# HTTP(S) Target Proxy
resource "google_compute_target_http_proxy" "ultramcp_http_proxy" {
  name    = "ultramcp-http-proxy-${var.environment}"
  url_map = google_compute_url_map.ultramcp_url_map.id
}

# Global Forwarding Rule
resource "google_compute_global_forwarding_rule" "ultramcp_http_forwarding_rule" {
  name                  = "ultramcp-http-forwarding-rule-${var.environment}"
  target                = google_compute_target_http_proxy.ultramcp_http_proxy.id
  port_range            = "80"
  load_balancing_scheme = "EXTERNAL"
  ip_address            = google_compute_global_address.ultramcp_ip.address
}

# SSL Certificate (optional)
resource "google_compute_managed_ssl_certificate" "ultramcp_ssl_cert" {
  count = var.enable_ssl ? 1 : 0
  name  = "ultramcp-ssl-cert-${var.environment}"

  managed {
    domains = [var.domain_name]
  }

  lifecycle {
    create_before_destroy = true
  }
}

# HTTPS Target Proxy (optional)
resource "google_compute_target_https_proxy" "ultramcp_https_proxy" {
  count           = var.enable_ssl ? 1 : 0
  name            = "ultramcp-https-proxy-${var.environment}"
  url_map         = google_compute_url_map.ultramcp_url_map.id
  ssl_certificates = [google_compute_managed_ssl_certificate.ultramcp_ssl_cert[0].id]
}

# HTTPS Forwarding Rule (optional)
resource "google_compute_global_forwarding_rule" "ultramcp_https_forwarding_rule" {
  count                 = var.enable_ssl ? 1 : 0
  name                  = "ultramcp-https-forwarding-rule-${var.environment}"
  target                = google_compute_target_https_proxy.ultramcp_https_proxy[0].id
  port_range            = "443"
  load_balancing_scheme = "EXTERNAL"
  ip_address            = google_compute_global_address.ultramcp_ip.address
}

# Cloud SQL Instance (PostgreSQL)
resource "google_sql_database_instance" "ultramcp_db" {
  count            = var.create_database ? 1 : 0
  name             = "ultramcp-db-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier                        = var.db_tier
    availability_type           = "REGIONAL"
    disk_size                   = var.db_disk_size
    disk_type                   = "PD_SSD"
    disk_autoresize            = true
    disk_autoresize_limit      = 100

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 30
      }
    }

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.ultramcp_network.id
      enable_private_path_for_google_cloud_services = true
    }

    maintenance_window {
      day          = 7
      hour         = 3
      update_track = "stable"
    }

    insights_config {
      query_insights_enabled  = true
      record_application_tags = true
      record_client_address   = true
    }
  }

  deletion_protection = var.environment == "production"

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Private Service Connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  count         = var.create_database ? 1 : 0
  name          = "ultramcp-private-ip-${var.environment}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.ultramcp_network.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  count                   = var.create_database ? 1 : 0
  network                 = google_compute_network.ultramcp_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address[0].name]
}

# Outputs
output "load_balancer_ip" {
  description = "External IP address of the load balancer"
  value       = google_compute_global_address.ultramcp_ip.address
}

output "network_id" {
  description = "ID of the VPC network"
  value       = google_compute_network.ultramcp_network.id
}

output "subnet_id" {
  description = "ID of the subnet"
  value       = google_compute_subnetwork.ultramcp_subnet.id
}

output "instance_group_manager" {
  description = "Instance group manager details"
  value = {
    name = google_compute_instance_group_manager.ultramcp_igm.name
    zone = google_compute_instance_group_manager.ultramcp_igm.zone
    size = google_compute_instance_group_manager.ultramcp_igm.target_size
  }
}

output "database_connection" {
  description = "Database connection details"
  value = var.create_database ? {
    instance_name     = google_sql_database_instance.ultramcp_db[0].name
    connection_name   = google_sql_database_instance.ultramcp_db[0].connection_name
    private_ip_address = google_sql_database_instance.ultramcp_db[0].private_ip_address
  } : null
  sensitive = true
}

output "ssl_certificate" {
  description = "SSL certificate details"
  value = var.enable_ssl ? {
    name   = google_compute_managed_ssl_certificate.ultramcp_ssl_cert[0].name
    status = google_compute_managed_ssl_certificate.ultramcp_ssl_cert[0].managed[0].status
  } : null
}