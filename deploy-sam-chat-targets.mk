# =============================================================================
# UltraMCP sam.chat Production Deployment Targets
# Makefile include for sam.chat specific operations
# =============================================================================

# ==============================================
# SAM.CHAT PRODUCTION DEPLOYMENT
# ==============================================

deploy-sam-chat: ## Deploy complete UltraMCP to sam.chat (no ports)
	@echo "🚀 Deploying UltraMCP to sam.chat..."
	@./start-sam-chat.sh

deploy-sam-chat-simple: ## Deploy UltraMCP to sam.chat (simple mode, no Docker)
	@echo "🚀 Deploying UltraMCP to sam.chat (Simple Mode)..."
	@./start-sam-chat-simple.sh

sam-chat-start: ## Start sam.chat production environment
	@echo "🌐 Starting sam.chat production environment..."
	@docker compose -f docker-compose.sam.chat.yml up -d
	@echo "✅ sam.chat services started"
	@$(MAKE) sam-chat-status

sam-chat-stop: ## Stop sam.chat services
	@echo "🛑 Stopping sam.chat services..."
	@docker compose -f docker-compose.sam.chat.yml down
	@echo "✅ sam.chat services stopped"

sam-chat-status: ## Check sam.chat services status
	@echo "📊 sam.chat Services Status:"
	@echo "=============================="
	@docker compose -f docker-compose.sam.chat.yml ps
	@echo ""
	@echo "🌐 Service URLs:"
	@echo "  Frontend:    https://sam.chat"
	@echo "  API:         https://api.sam.chat"
	@echo "  Studio:      https://studio.sam.chat"
	@echo "  Observatory: https://observatory.sam.chat"

sam-chat-logs: ## View sam.chat services logs
	@docker compose -f docker-compose.sam.chat.yml logs -f --tail=100

test-sam-chat: ## Test sam.chat deployment
	@echo "🧪 Testing sam.chat deployment..."
	@echo "Testing frontend..."
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/health | grep -q "200" && echo "✅ Frontend OK" || echo "❌ Frontend Failed"
	@echo "Testing API..."
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/health | grep -q "200" && echo "✅ API OK" || echo "❌ API Failed"
	@echo "Testing microservices..."
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8001 | grep -q "200" && echo "✅ CoD Service OK" || echo "❌ CoD Service Failed"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8013 | grep -q "200" && echo "✅ Claudia Service OK" || echo "❌ Claudia Service Failed"

setup-cloudflare-ssl: ## Configure Nginx for Cloudflare Flexible SSL
	@echo "☁️  Configuring Nginx for Cloudflare Flexible SSL..."
	@echo "✅ Using Cloudflare SSL certificates (no local certs needed)"
	@echo "🔄 Updating Nginx configuration..."
	@sudo cp nginx-sam-chat-production.conf /etc/nginx/sites-available/sam.chat
	@sudo ln -sf /etc/nginx/sites-available/sam.chat /etc/nginx/sites-enabled/sam.chat
	@sudo rm -f /etc/nginx/sites-enabled/default
	@sudo nginx -t && sudo systemctl reload nginx
	@echo "✅ Nginx configured for Cloudflare Flexible SSL"

sam-chat-health: ## Comprehensive health check for sam.chat
	@echo "🏥 sam.chat Health Check"
	@echo "========================"
	@echo "Testing all service endpoints..."
	@for port in 5173 3001 8001 8002 8003 8004 8005 8006 8007 8013; do \
		echo -n "Port $$port: "; \
		curl -s -o /dev/null -w "%{http_code}" http://localhost:$$port 2>/dev/null && echo "✅" || echo "❌"; \
	done
	@echo ""
	@echo "Testing domain resolution..."
	@ping -c 1 sam.chat >/dev/null 2>&1 && echo "✅ sam.chat resolves" || echo "❌ sam.chat DNS issue"

sam-chat-logs-search: ## Search sam.chat logs
	@if [ -z "$(QUERY)" ]; then \
		echo "Usage: make sam-chat-logs-search QUERY='error'"; \
	else \
		docker-compose -f docker-compose.sam.chat.yml logs | grep -i "$(QUERY)" | tail -20; \
	fi

sam-chat-backup: ## Backup sam.chat data
	@echo "💾 Backing up sam.chat data..."
	@mkdir -p backups/sam-chat/$(shell date +%Y%m%d_%H%M%S)
	@docker-compose -f docker-compose.sam.chat.yml exec -T ultramcp-redis redis-cli --rdb /data/dump.rdb
	@docker cp $$(docker-compose -f docker-compose.sam.chat.yml ps -q ultramcp-redis):/data/dump.rdb backups/sam-chat/$(shell date +%Y%m%d_%H%M%S)/
	@tar -czf backups/sam-chat/$(shell date +%Y%m%d_%H%M%S)/data-backup.tar.gz data/
	@echo "✅ Backup completed"

sam-chat-restore: ## Restore sam.chat data
	@if [ -z "$(BACKUP_DATE)" ]; then \
		echo "Usage: make sam-chat-restore BACKUP_DATE='20250708_120000'"; \
	else \
		echo "🔄 Restoring sam.chat data from $(BACKUP_DATE)..."; \
		tar -xzf backups/sam-chat/$(BACKUP_DATE)/data-backup.tar.gz; \
		docker cp backups/sam-chat/$(BACKUP_DATE)/dump.rdb $$(docker-compose -f docker-compose.sam.chat.yml ps -q ultramcp-redis):/data/; \
		docker-compose -f docker-compose.sam.chat.yml restart ultramcp-redis; \
		echo "✅ Restore completed"; \
	fi

sam-chat-update: ## Update sam.chat deployment
	@echo "🔄 Updating sam.chat deployment..."
	@git pull origin main
	@docker-compose -f docker-compose.sam.chat.yml down
	@docker-compose -f docker-compose.sam.chat.yml build --no-cache
	@docker-compose -f docker-compose.sam.chat.yml up -d
	@echo "✅ sam.chat updated and restarted"