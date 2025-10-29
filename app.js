const express = require('express');
const app = express();
const PORT = process.env.PORT || 8080;
const RELEASE_ID = process.env.RELEASE_ID || 'local-release';
const APP_POOL = process.env.APP_POOL || 'unknown';

app.use(express.json());

// Chaos simulation variables
let chaosMode = null;
let chaosStartTime = null;

// Middleware to simulate chaos
app.use((req, res, next) => {
    if (chaosMode === 'error' && req.method !== 'POST') {
        return res.status(500).json({ error: 'Chaos mode: simulated server error' });
    }
    
    if (chaosMode === 'timeout' && req.method !== 'POST') {
        // Simulate timeout by not responding
        return;
    }
    
    if (chaosMode === 'slow' && req.method !== 'POST') {
        // Simulate slow response
        setTimeout(() => next(), 3000);
        return;
    }
    
    next();
});

// GET /version - returns JSON with version info
app.get('/version', (req, res) => {
    res.set({
        'X-App-Pool': APP_POOL,
        'X-Release-Id': RELEASE_ID,
        'Content-Type': 'application/json'
    });
    
    res.json({
        pool: APP_POOL,
        release: RELEASE_ID,
        timestamp: new Date().toISOString(),
        chaos: chaosMode
    });
});

// GET /healthz - health check endpoint
app.get('/healthz', (req, res) => {
    if (chaosMode === 'error') {
        return res.status(500).json({ status: 'unhealthy', chaos: true });
    }
    
    res.set({
        'X-App-Pool': APP_POOL,
        'X-Release-Id': RELEASE_ID
    });
    
    res.json({ 
        status: 'healthy', 
        pool: APP_POOL,
        release: RELEASE_ID,
        chaos: chaosMode 
    });
});

// POST /chaos/start - start chaos simulation
app.post('/chaos/start', (req, res) => {
    const mode = req.query.mode || 'error';
    chaosMode = mode;
    chaosStartTime = new Date();
    
    res.json({
        message: `Chaos mode started: ${mode}`,
        pool: APP_POOL,
        startTime: chaosStartTime.toISOString()
    });
});

// POST /chaos/stop - stop chaos simulation
app.post('/chaos/stop', (req, res) => {
    const previousMode = chaosMode;
    chaosMode = null;
    chaosStartTime = null;
    
    res.json({
        message: 'Chaos mode stopped',
        pool: APP_POOL,
        previousMode: previousMode,
        stopTime: new Date().toISOString()
    });
});

// Root endpoint
app.get('/', (req, res) => {
    res.json({
        service: 'Blue/Green Test App',
        pool: APP_POOL,
        release: RELEASE_ID,
        endpoints: {
            version: 'GET /version',
            health: 'GET /healthz',
            chaosStart: 'POST /chaos/start?mode=error|timeout|slow',
            chaosStop: 'POST /chaos/stop'
        }
    });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`App Pool: ${APP_POOL}`);
    console.log(`Release ID: ${RELEASE_ID}`);
});