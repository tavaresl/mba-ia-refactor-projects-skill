const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

function createLogger(level = 'info') {
    const threshold = LEVELS[level] || LEVELS.info;

    function write(name, message, error) {
        if (LEVELS[name] < threshold) return;
        const stream = LEVELS[name] >= LEVELS.warn ? process.stderr : process.stdout;
        const detail = error ? ` ${error.stack || error}` : '';
        stream.write(`[${name.toUpperCase()}] ${message}${detail}\n`);
    }

    return {
        debug: (message) => write('debug', message),
        info: (message) => write('info', message),
        warn: (message, error) => write('warn', message, error),
        error: (message, error) => write('error', message, error),
    };
}

module.exports = { createLogger };
