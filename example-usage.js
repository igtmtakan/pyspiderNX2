const { logError, debug } = require('./error-logger');

// デバッグ出力を有効化する場合は環境変数を設定
// process.env.DEBUG = 'app:error';

try {
    debug('Executing risky operation');
    throw new Error('Something went wrong');
} catch (error) {
    logError(error, {
        component: 'ExampleComponent',
        operation: 'exampleOperation',
        timestamp: new Date().toISOString()
    });
}

// または直接使用する場合
try {
    b.csa(a, d);
} catch (error) {
    logError(error, {
        method: 'csa',
        arguments: { a, d }
    });
}
