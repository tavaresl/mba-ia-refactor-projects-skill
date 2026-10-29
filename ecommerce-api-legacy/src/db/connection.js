const sqlite3 = require('sqlite3');

function createDatabase(filename = ':memory:') {
    const raw = new sqlite3.Database(filename);

    const run = (sql, params = []) => new Promise((resolve, reject) => {
        raw.run(sql, params, function onRun(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
    const get = (sql, params = []) => new Promise((resolve, reject) => {
        raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
    const all = (sql, params = []) => new Promise((resolve, reject) => {
        raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });

    // A conexão é única: todas as operações passam por uma fila, e uma transação
    // segura a fila até o COMMIT/ROLLBACK para não misturar requisições.
    let tail = Promise.resolve();
    const enqueue = (task) => {
        const result = tail.then(task);
        tail = result.catch(() => {});
        return result;
    };

    const direct = { run, get, all };

    return {
        run: (sql, params) => enqueue(() => run(sql, params)),
        get: (sql, params) => enqueue(() => get(sql, params)),
        all: (sql, params) => enqueue(() => all(sql, params)),
        transaction: (work) => enqueue(async () => {
            await run('BEGIN');
            try {
                const result = await work(direct);
                await run('COMMIT');
                return result;
            } catch (err) {
                await run('ROLLBACK').catch(() => {});
                throw err;
            }
        }),
        close: () => enqueue(() => new Promise((resolve, reject) => {
            raw.close((err) => (err ? reject(err) : resolve()));
        })),
    };
}

module.exports = { createDatabase };
