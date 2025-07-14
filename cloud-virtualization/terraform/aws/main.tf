# UltraMCP AWS Infrastructure
# Multi-region deployment with auto-scaling and load balancing

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "UltraMCP"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# VPC and Networking
resource "aws_vpc" "ultramcp_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "ultramcp-vpc-${var.environment}"
  }
}

resource "aws_internet_gateway" "ultramcp_igw" {
  vpc_id = aws_vpc.ultramcp_vpc.id

  tags = {
    Name = "ultramcp-igw-${var.environment}"
  }
}

resource "aws_subnet" "ultramcp_public_subnets" {
  count = length(var.public_subnet_cidrs)

  vpc_id                  = aws_vpc.ultramcp_vpc.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "ultramcp-public-subnet-${count.index + 1}-${var.environment}"
    Type = "Public"
  }
}

resource "aws_subnet" "ultramcp_private_subnets" {
  count = length(var.private_subnet_cidrs)

  vpc_id            = aws_vpc.ultramcp_vpc.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "ultramcp-private-subnet-${count.index + 1}-${var.environment}"
    Type = "Private"
  }
}

# Route Tables
resource "aws_route_table" "ultramcp_public_rt" {
  vpc_id = aws_vpc.ultramcp_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.ultramcp_igw.id
  }

  tags = {
    Name = "ultramcp-public-rt-${var.environment}"
  }
}

resource "aws_route_table_association" "ultramcp_public_rta" {
  count = length(aws_subnet.ultramcp_public_subnets)

  subnet_id      = aws_subnet.ultramcp_public_subnets[count.index].id
  route_table_id = aws_route_table.ultramcp_public_rt.id
}

# Security Groups
resource "aws_security_group" "ultramcp_web_sg" {
  name_prefix = "ultramcp-web-sg-"
  vpc_id      = aws_vpc.ultramcp_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3000
    to_port     = 3001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "UltraMCP WebUI and Dashboard"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ultramcp-web-sg-${var.environment}"
  }
}

resource "aws_security_group" "ultramcp_app_sg" {
  name_prefix = "ultramcp-app-sg-"
  vpc_id      = aws_vpc.ultramcp_vpc.id

  ingress {
    from_port       = 8001
    to_port         = 8013
    protocol        = "tcp"
    security_groups = [aws_security_group.ultramcp_web_sg.id]
    description     = "UltraMCP Services"
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "SSH access from VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ultramcp-app-sg-${var.environment}"
  }
}

# Launch Template
resource "aws_launch_template" "ultramcp_lt" {
  name_prefix   = "ultramcp-lt-"
  image_id      = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name      = aws_key_pair.ultramcp_key.key_name

  vpc_security_group_ids = [aws_security_group.ultramcp_app_sg.id]

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    supabase_url     = var.supabase_url
    supabase_key     = var.supabase_anon_key
    environment      = var.environment
    node_role        = "worker"
    docker_compose_url = var.docker_compose_url
  }))

  block_device_mappings {
    device_name = "/dev/sda1"
    ebs {
      volume_size = var.root_volume_size
      volume_type = "gp3"
      encrypted   = true
      iops        = 3000
      throughput  = 125
    }
  }

  monitoring {
    enabled = true
  }

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "ultramcp-instance-${var.environment}"
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Auto Scaling Group
resource "aws_autoscaling_group" "ultramcp_asg" {
  name                = "ultramcp-asg-${var.environment}"
  vpc_zone_identifier = aws_subnet.ultramcp_private_subnets[*].id
  target_group_arns   = [aws_lb_target_group.ultramcp_tg.arn]
  health_check_type   = "ELB"
  health_check_grace_period = 300

  min_size         = var.min_size
  max_size         = var.max_size
  desired_capacity = var.desired_capacity

  launch_template {
    id      = aws_launch_template.ultramcp_lt.id
    version = "$Latest"
  }

  # Auto Scaling Policies
  enabled_metrics = [
    "GroupMinSize",
    "GroupMaxSize",
    "GroupDesiredCapacity",
    "GroupInServiceInstances",
    "GroupTotalInstances"
  ]

  tag {
    key                 = "Name"
    value               = "ultramcp-asg-instance-${var.environment}"
    propagate_at_launch = true
  }

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Application Load Balancer
resource "aws_lb" "ultramcp_alb" {
  name               = "ultramcp-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.ultramcp_web_sg.id]
  subnets            = aws_subnet.ultramcp_public_subnets[*].id

  enable_deletion_protection = false

  tags = {
    Name = "ultramcp-alb-${var.environment}"
  }
}

resource "aws_lb_target_group" "ultramcp_tg" {
  name     = "ultramcp-tg-${var.environment}"
  port     = 3000
  protocol = "HTTP"
  vpc_id   = aws_vpc.ultramcp_vpc.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "ultramcp-tg-${var.environment}"
  }
}

resource "aws_lb_listener" "ultramcp_listener" {
  load_balancer_arn = aws_lb.ultramcp_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ultramcp_tg.arn
  }
}

# Auto Scaling Policies
resource "aws_autoscaling_policy" "ultramcp_scale_up" {
  name                   = "ultramcp-scale-up-${var.environment}"
  scaling_adjustment     = 2
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.ultramcp_asg.name

  policy_type = "SimpleScaling"
}

resource "aws_autoscaling_policy" "ultramcp_scale_down" {
  name                   = "ultramcp-scale-down-${var.environment}"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.ultramcp_asg.name

  policy_type = "SimpleScaling"
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "ultramcp_cpu_high" {
  alarm_name          = "ultramcp-cpu-high-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "75"
  alarm_description   = "This metric monitors ec2 cpu utilization"

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.ultramcp_asg.name
  }

  alarm_actions = [aws_autoscaling_policy.ultramcp_scale_up.arn]
}

resource "aws_cloudwatch_metric_alarm" "ultramcp_cpu_low" {
  alarm_name          = "ultramcp-cpu-low-${var.environment}"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "25"
  alarm_description   = "This metric monitors ec2 cpu utilization"

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.ultramcp_asg.name
  }

  alarm_actions = [aws_autoscaling_policy.ultramcp_scale_down.arn]
}

# Key Pair
resource "aws_key_pair" "ultramcp_key" {
  key_name   = "ultramcp-key-${var.environment}"
  public_key = var.public_key
}

# RDS Subnet Group (for Supabase-compatible PostgreSQL)
resource "aws_db_subnet_group" "ultramcp_db_subnet_group" {
  name       = "ultramcp-db-subnet-group-${var.environment}"
  subnet_ids = aws_subnet.ultramcp_private_subnets[*].id

  tags = {
    Name = "ultramcp-db-subnet-group-${var.environment}"
  }
}

# Outputs
output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = aws_lb.ultramcp_alb.dns_name
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.ultramcp_vpc.id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.ultramcp_private_subnets[*].id
}

output "security_group_ids" {
  description = "Security group IDs"
  value = {
    web = aws_security_group.ultramcp_web_sg.id
    app = aws_security_group.ultramcp_app_sg.id
  }
}