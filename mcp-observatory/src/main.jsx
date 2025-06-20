// MCP Observatory Main Module
console.log('🔭 Observatory Main.jsx loaded successfully');
console.log('✅ MIME type working correctly');

// Simple React-like functionality without dependencies
class Observatory {
    constructor() {
        this.init();
    }
    
    init() {
        console.log('🚀 Observatory initialized');
        this.addSystemInfo();
        this.startMonitoring();
    }
    
    addSystemInfo() {
        const container = document.querySelector('.container');
        if (container) {
            const systemDiv = document.createElement('div');
            systemDiv.className = 'status';
            systemDiv.innerHTML = `
                <h3>🔧 JavaScript Module Status:</h3>
                <p class="working">✅ main.jsx loaded as ES6 module</p>
                <p class="working">✅ MIME type: application/javascript</p>
                <p class="working">✅ No more octet-stream error</p>
            `;
            container.appendChild(systemDiv);
        }
    }
    
    startMonitoring() {
        setInterval(() => {
            console.log('🔭 Observatory monitoring active:', new Date().toISOString());
        }, 30000);
    }
}

// Initialize Observatory
const observatory = new Observatory();

// Export for module compatibility
export default observatory;
