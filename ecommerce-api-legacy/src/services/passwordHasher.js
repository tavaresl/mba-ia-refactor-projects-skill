const crypto = require('crypto');
const { promisify } = require('util');
const { SCRYPT } = require('../config/constants');

const scrypt = promisify(crypto.scrypt);

function createPasswordHasher() {
    return {
        async hash(password) {
            const salt = crypto.randomBytes(SCRYPT.SALT_BYTES);
            const key = await scrypt(password, salt, SCRYPT.KEY_LENGTH);
            return `${SCRYPT.PREFIX}$${salt.toString('hex')}$${key.toString('hex')}`;
        },

        async verify(password, stored) {
            const [prefix, saltHex, keyHex] = String(stored || '').split('$');
            if (prefix !== SCRYPT.PREFIX || !saltHex || !keyHex) return false;
            const expected = Buffer.from(keyHex, 'hex');
            const actual = await scrypt(password, Buffer.from(saltHex, 'hex'), expected.length);
            return crypto.timingSafeEqual(actual, expected);
        },
    };
}

module.exports = { createPasswordHasher };
