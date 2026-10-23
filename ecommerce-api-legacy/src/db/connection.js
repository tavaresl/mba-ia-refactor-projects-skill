const sqlite3 = require('sqlite3').verbose();

// Envolve o driver sqlite3 em Promises e oferece transações serializadas.
// Uma única conexão é compartilhada de propósito: o banco ':memory:' só existe nela.
function createDatabase(filename) {
    const driver = new sqlite3.Database(filename);

    const run = (sql, params = []) => new Promise((resolve, reject) => {
        driver.run(sql, params, function onDone(err) {
            if (err) return reject(err);
            return resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
    const get = (sql, params = []) => new Promise((resolve, reject) => {
        driver.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
    const all = (sql, params = []) => new Promise((resolve, reject) => {
        driver.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });

    const executor = { run, get, all };

    let queue = Promise.resolve();
    function transaction(work) {
        const result = queue.then(async () => {
            await run('BEGIN');
            try {
                const value = await work(executor);
                await run('COMMIT');
                return value;
            } catch (err) {
                await run('ROLLBACK').catch(() => {});
                throw err;
            }
        });
        queue = result.catch(() => {});
        return result;
    }

    return { ...executor, transaction, close: () => driver.close() };
}

module.exports = { createDatabase };
