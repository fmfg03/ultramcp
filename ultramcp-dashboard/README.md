# UltraMCP Custom Dashboard

A modern, responsive dashboard for the UltraMCP AI Platform built with React, TypeScript, and shadcn/ui components.

## 🎨 Features

### **Modern UI Components**
- **shadcn/ui**: Complete component library with Radix UI primitives
- **Tailwind CSS**: Utility-first styling with custom UltraMCP theme
- **TypeScript**: Full type safety and excellent developer experience
- **Responsive Design**: Works on desktop, tablet, and mobile

### **Real-time Monitoring**
- **Service Health**: Live status monitoring for all 12 UltraMCP services
- **Performance Metrics**: Response times, uptime, and request counts
- **System Overview**: Visual health indicators and progress bars
- **Interactive Cards**: Hover effects and detailed service information

### **Custom UltraMCP Theming**
- **Brand Colors**: Custom color palette for UltraMCP services
  - Chain-of-Debate: Purple (`#8b5cf6`)
  - Agent Factory: Cyan (`#06b6d4`) 
  - Security: Red (`#ef4444`)
  - Memory: Green (`#10b981`)
- **Dark/Light Mode**: Automatic theme switching with `next-themes`
- **Gradient Effects**: Beautiful gradients and animations
- **Service-Specific Badges**: Color-coded status indicators

### **Dashboard Sections**
- **Services Overview**: Grid of all UltraMCP services with health status
- **Analytics**: Performance charts and metrics (expandable)
- **Logs**: Real-time log streaming (expandable)
- **Settings**: Configuration and preferences (expandable)

## 🚀 Quick Start

### **Option 1: Development Mode**
```bash
# Install dependencies
make dashboard-install

# Start development server
make dashboard-start

# Access dashboard
open http://localhost:3001
```

### **Option 2: With Full UltraMCP Stack**
```bash
# Start complete integration (includes dashboard)
make supabase-start

# Access points:
# - Open WebUI: http://localhost:3000
# - Custom Dashboard: http://localhost:3001
# - Supabase API: http://localhost:8000
```

### **Option 3: Production Build**
```bash
# Build for production
make dashboard-build

# Deploy with Docker
docker-compose -f docker-compose.supabase-webui.yml up ultramcp-dashboard
```

## 🏗️ Architecture

### **Technology Stack**
- **React 18**: Latest React with hooks and concurrent features
- **TypeScript**: Full type safety
- **Vite**: Fast build tool and dev server
- **Tailwind CSS 3**: Utility-first CSS framework
- **shadcn/ui**: Modern component library
- **Radix UI**: Accessible UI primitives
- **Lucide Icons**: Beautiful SVG icons
- **Framer Motion**: Smooth animations

### **Project Structure**
```
ultramcp-dashboard/
├── src/
│   ├── components/
│   │   ├── ui/           # shadcn/ui components
│   │   └── UltraMCPDashboard.tsx  # Main dashboard
│   ├── lib/
│   │   └── utils.ts      # Utility functions
│   ├── styles/
│   │   └── globals.css   # Custom UltraMCP theme
│   ├── App.tsx           # React app with routing
│   └── main.tsx          # Entry point
├── Dockerfile            # Production build
├── nginx.conf           # Reverse proxy config
└── tailwind.config.js   # Custom theme config
```

### **API Integration**
The dashboard connects to UltraMCP services via:
- **Proxy Routes**: Nginx proxies to internal services
- **WebSocket**: Real-time updates from Control Tower
- **REST APIs**: Service health and metrics endpoints

## 🎯 Component Showcase

### **Service Status Cards**
```tsx
// Real-time service monitoring
<Card className="ultramcp-service-card group">
  <CardHeader>
    <div className="ultramcp-flex-between">
      <service.icon className="w-5 h-5 text-ultramcp-primary" />
      <Badge variant={service.status === 'healthy' ? 'default' : 'destructive'}>
        {service.status}
      </Badge>
    </div>
  </CardHeader>
  <CardContent>
    <p className="text-sm">{service.description}</p>
    <div className="space-y-2">
      <div className="ultramcp-flex-between text-xs">
        <span>Response Time</span>
        <span>{service.responseTime}ms</span>
      </div>
    </div>
  </CardContent>
</Card>
```

### **System Health Progress**
```tsx
// Visual health indicator
<Progress value={systemHealth} className="w-full h-3" />
<Badge variant={systemHealth >= 90 ? 'default' : 'destructive'}>
  {systemHealth.toFixed(1)}% Healthy
</Badge>
```

### **Custom Theme Classes**
```css
/* UltraMCP-specific components */
.ultramcp-card {
  @apply bg-gradient-to-br from-white to-slate-50 dark:from-slate-900 dark:to-slate-800;
}

.ultramcp-gradient-text {
  @apply bg-gradient-to-r from-ultramcp-primary to-ultramcp-secondary bg-clip-text text-transparent;
}

.ultramcp-status-healthy {
  @apply bg-ultramcp-success animate-pulse-slow;
}
```

## 🔧 Configuration

### **Environment Variables**
```bash
# API endpoints (automatically configured via nginx proxy)
VITE_ULTRAMCP_API_URL=/api/ultramcp
VITE_SUPABASE_API_URL=/api/supabase
VITE_MEMORY_API_URL=/api/memory
```

### **Tailwind Theme Customization**
```js
// tailwind.config.js
theme: {
  extend: {
    colors: {
      ultramcp: {
        primary: "#6366f1",    // Indigo
        secondary: "#8b5cf6",  // Violet  
        accent: "#06b6d4",     // Cyan
        success: "#10b981",    // Emerald
        warning: "#f59e0b",    // Amber
        error: "#ef4444",      // Red
      }
    }
  }
}
```

## 📊 Monitoring Features

### **Real-time Metrics**
- **Total Requests**: Aggregated across all services
- **Active Services**: Count of healthy/total services
- **Average Response Time**: Weighted average performance
- **System Uptime**: Overall platform availability

### **Service Details**
- **Health Status**: Color-coded indicators (green/red/yellow)
- **Response Time**: Individual service performance
- **Uptime Percentage**: Service reliability metrics
- **Request Count**: Traffic volume per service
- **Last Check**: Freshness of health data

### **Interactive Elements**
- **Hover Effects**: Additional details on card hover
- **Status Animations**: Pulsing for healthy, bouncing for errors
- **Progress Bars**: Visual representation of system health
- **Responsive Grid**: Adapts to screen size

## 🚀 Deployment

### **Development**
```bash
npm run dev    # Start dev server on port 3001
```

### **Production**
```bash
npm run build  # Build optimized bundle
npm run preview # Preview production build
```

### **Docker**
```bash
docker build -t ultramcp-dashboard .
docker run -p 3001:3001 ultramcp-dashboard
```

## 🔮 Future Enhancements

### **Planned Features**
- **Real-time Charts**: Recharts integration for performance visualization
- **Log Streaming**: Live log viewer with filtering and search
- **Alert System**: Configurable notifications for service issues
- **User Management**: Integration with Supabase Auth
- **Theme Builder**: Dynamic theme customization
- **Export Features**: Download reports and metrics

### **Expandable Sections**
- **Analytics Tab**: Performance charts and trends
- **Logs Tab**: Real-time log streaming with WebSocket
- **Settings Tab**: Dashboard configuration and preferences

The dashboard provides a modern, professional interface for monitoring and managing the complete UltraMCP AI platform with beautiful shadcn/ui components and custom theming.