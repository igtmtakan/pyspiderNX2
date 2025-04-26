const express = require('express');
const { chromium } = require('playwright');
const bodyParser = require('body-parser');

const app = express();
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({extended: false}));

let browser = null;

app.use(async (req, res, next) => {
    if (!browser) {
        const options = req.body;
        const browserOptions = {
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--ignore-certificate-errors',  // SSL証明書エラーを無視
                '--ignore-ssl-errors'          // SSLエラーを無視
            ]
        };
        
        // プロキシ設定
        if (options.proxy) {
            const proxyUrl = options.proxy.includes('://') ? options.proxy : `http://${options.proxy}`;
            browserOptions.proxy = { server: proxyUrl };
        }
        
        // ヘッドレスモード設定
        browserOptions.headless = options.headless !== "false";

        try {
            browser = await chromium.launch(browserOptions);
            console.log("Browser initialized successfully");
        } catch (error) {
            console.error("Browser initialization failed:", error);
            return res.status(500).json({
                error: error.toString(),
                status_code: 599
            });
        }
    }
    next();
});

async function fetch(options) {
    const contextOptions = {
        ignoreHTTPSErrors: true,  // HTTPSエラーを無視
    };

    const context = await browser.newContext(contextOptions);
    const page = await context.newPage();
    options.startTime = Date.now();

    try {
        await _fetch(page, options);
        const result = await makeResult(page, options);
        await context.close();
        return result;
    } catch (error) {
        console.error('Error during fetch:', error);
        const result = await makeResult(page, options, error);
        await context.close();
        return result;
    }
}

async function _fetch(page, options) {
    // Set viewport
    await page.setViewportSize({
        width: options.js_viewport_width || 1024,
        height: options.js_viewport_height || 768 * 3
    });

    // Set headers
    if (options.headers) {
        if (options.headers['User-Agent']) {
            await page.setExtraHTTPHeaders(options.headers);
        }
    }

    // Handle console messages
    page.on('console', msg => console.log('Page console:', msg.text()));

    // Configure request interception
    await page.route('**/*', async (route) => {
        if (options.load_images === "false" && route.request().resourceType() === 'image') {
            await route.abort();
        } else {
            await route.continue();
        }
    });

    // Navigate to page
    const response = await page.goto(options.url, {
        timeout: options.timeout ? options.timeout * 1000 : 20000,
        waitUntil: 'networkidle'
    });

    // Execute custom JavaScript
    if (options.js_script) {
        console.log('Executing custom JavaScript');
        options.scriptResult = await page.evaluate(options.js_script);
    }

    // Take screenshot if requested
    if (options.screenshot_path) {
        await page.screenshot({ path: options.screenshot_path });
    }

    options.response = response;
}

async function makeResult(page, options, error = null) {
    const response = options.response;
    
    // Get cookies
    const cookies = {};
    const rawCookies = await page.context().cookies();
    rawCookies.forEach(cookie => {
        cookies[cookie.name] = cookie.value;
    });

    // Prepare result
    const result = {
        orig_url: options.url,
        status_code: error ? 599 : (response ? response.status() : 599),
        error: error ? error.toString() : null,
        content: error ? null : await page.content(),
        headers: response ? await response.allHeaders() : {},
        url: error ? options.url : page.url(),
        cookies: cookies,
        time: (Date.now() - options.startTime) / 1000,
        js_script_result: options.scriptResult,
        save: options.save
    };

    return result;
}

app.post("/", async (req, res) => {
    try {
        const result = await fetch(req.body);
        res.json(result);
    } catch (error) {
        res.status(500).json({
            error: error.toString(),
            status_code: 599
        });
    }
});

const port = process.argv[2] || 22223;
app.listen(port, () => {
    console.log(`Playwright fetcher running on port ${port}`);
});
