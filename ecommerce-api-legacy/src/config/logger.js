const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

function createLogger(level) {
    const threshold = LEVELS[level] || LEVELS.info;

    function log(levelName, message, meta) {
        if (LEVELS[levelName] < threshold) return;
        const line = `[${levelName.toUpperCase()}] ${message}`;
        const sink = levelName === 'error' ? console.error : console.log;
        if (meta === undefined) sink(line);
        else sink(line, meta);
    }

    return {
        debug: (message, meta) => log('debug', message, meta),
        info: (message, meta) => log('info', message, meta),
        warn: (message, meta) => log('warn', message, meta),
        error: (message, meta) => log('error', message, meta),
    };
}

module.exports = { createLogger };
