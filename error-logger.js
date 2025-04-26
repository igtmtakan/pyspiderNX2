const config = require('./error-config.js');
const debug = require('debug')('app:error');

function logError(error, context) {
    // デバッグモードの場合、詳細情報をログ出力
    debug('Error occurred with context: %O', context);
    debug('Error details: %O', error);

    const errorDetails = {
        name: error.name || 'Error',
        message: error.message || String(error),
        stack: config.logging.captureStack ? error.stack : undefined,
        context: context
    };

    // 設定に基づいてログ出力
    if (config.logging.format === 'json') {
        console.error(JSON.stringify(errorDetails, null, config.logging.maxErrorDepth));
    } else {
        console.error(errorDetails);
    }

    // CSAロガーの処理
    try {
        if (config.handlers.remote && typeof b !== 'undefined' && typeof b.csa === 'function') {
            debug('Attempting to use CSA logger');
            b.csa(errorDetails, {
                type: 'error',
                timestamp: new Date().toISOString()
            });
        }
    } catch (loggingError) {
        debug('CSA logging failed: %O', loggingError);
        if (config.logging.fallbackToConsole) {
            console.error('CSA logging failed:', loggingError);
            console.error('Original error:', error);
        }
    }
}

// エラーをラップするユーティリティ
function createCustomError(name, properties = {}) {
    return class CustomError extends Error {
        constructor(message) {
            super(message);
            this.name = name;
            Object.assign(this, properties);
            Error.captureStackTrace(this, this.constructor);
            debug('Created custom error: %s', name);
        }
    };
}

// カスタムエラータイプの定義
const LoggingError = createCustomError('LoggingError', {
    code: 'LOGGING_ERROR'
});

// エクスポート
module.exports = {
    logError,
    LoggingError,
    debug
};
