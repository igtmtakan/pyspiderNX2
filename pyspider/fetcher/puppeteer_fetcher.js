const express = require('express');
const bodyParser = require('body-parser');
const puppeteer = require('puppeteer');
const app = express();

// Get port from environment variable or use default
// コマンドライン引数からポートを取得（デフォルトは22223）
const port = process.argv[2] || process.env.PUPPETEER_FETCHER_PORT || 22223;

// Configure Express
app.use(bodyParser.json({ limit: '50mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '50mb' }));

// Browser instance
let browser;

// Initialize browser
async function initBrowser() {
    try {
        const options = {
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920x1080',
            ],
            ignoreHTTPSErrors: true
        };

        browser = await puppeteer.launch(options);
        console.log('Browser initialized successfully');

        // Handle browser disconnection
        browser.on('disconnected', async () => {
            console.log('Browser disconnected, reinitializing...');
            await initBrowser();
        });
    } catch (error) {
        console.error('Failed to initialize browser:', error);
        process.exit(1);
    }
}

// Fetch handler
app.post('/', async (req, res) => {
    const startTime = Date.now();
    const task = req.body;

    console.log(`Received task for URL: ${task.url}`);

    if (!browser) {
        return res.status(500).json({
            status_code: 500,
            error: 'Browser not initialized',
            content: '',
            time: (Date.now() - startTime) / 1000,
            orig_url: task.url,
            url: task.url
        });
    }

    let page;
    try {
        // Create a new page
        page = await browser.newPage();

        // Set viewport
        await page.setViewport({ width: 1920, height: 1080 });

        // Set user agent
        if (task.headers && task.headers['User-Agent']) {
            await page.setUserAgent(task.headers['User-Agent']);
        }

        // Set extra HTTP headers
        if (task.headers) {
            await page.setExtraHTTPHeaders(task.headers);
        }

        // Set cookies
        if (task.cookies) {
            const cookies = Object.entries(task.cookies).map(([name, value]) => ({
                name,
                value,
                domain: new URL(task.url).hostname,
                path: '/',
            }));
            await page.setCookie(...cookies);
        }

        // Set request timeout
        const timeout = task.request_timeout || 60000;

        // Navigate to URL with optimized timeout settings
        const response = await page.goto(task.url, {
            waitUntil: 'domcontentloaded',  // 'networkidle2'から変更して高速化
            timeout: task.request_timeout || 30000  // デフォルトタイムアウトを30秒に短縮
        });

        // Get page content
        const content = await page.content();

        // Get cookies
        const cookies = await page.cookies();
        const cookieDict = {};
        cookies.forEach(cookie => {
            cookieDict[cookie.name] = cookie.value;
        });

        // Get headers
        const headers = response.headers();

        // Create result
        const result = {
            orig_url: task.url,
            content: content,
            headers: headers,
            status_code: response.status(),
            url: response.url(),
            time: (Date.now() - startTime) / 1000,
            cookies: cookieDict,
            save: task.save
        };

        console.log(`Completed task for URL: ${task.url} with status: ${result.status_code} in ${result.time}s`);
        res.json(result);
    } catch (error) {
        console.error(`Error fetching ${task.url}:`, error);
        res.json({
            orig_url: task.url,
            content: error.toString(),
            headers: {},
            status_code: 599,
            url: task.url,
            time: (Date.now() - startTime) / 1000,
            cookies: {},
            save: task.save,
            error: error.toString()
        });
    } finally {
        if (page) {
            await page.close();
        }
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).send('OK');
});

// Initialize browser and start server
initBrowser().then(() => {
    app.listen(port, () => {
        console.log(`Server started on port ${port}`);
    }).on('error', (err) => {
        console.error('Failed to start server:', err);
        process.exit(1);
    });
});

// Handle process termination
process.on('SIGINT', async () => {
    console.log('Received SIGINT, closing browser and exiting...');
    if (browser) await browser.close();
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('Received SIGTERM, closing browser and exiting...');
    if (browser) await browser.close();
    process.exit(0);
});
