module.exports = {
    logging: {
        level: process.env.LOG_LEVEL || 'error',
        format: 'json',
        fallbackToConsole: true,
        captureStack: true,
        maxErrorDepth: 3
    },
    handlers: {
        console: true,
        file: false,
        remote: false
    }
};