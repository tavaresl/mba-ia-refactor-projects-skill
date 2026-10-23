const crypto = require('crypto');

const SCHEME = 'scrypt';
const KEY_LENGTH = 64;
const SALT_BYTES = 16;

// Formato legado do projeto original ("badCrypto"): os 2 primeiros caracteres do
// base64 da senha repetidos até 10 caracteres.
const legacyDigest = (password) => Buffer.from(password).toString('base64').substring(0, 2).repeat(5);

const safeEqual = (a, b) => {
    const left = Buffer.from(String(a));
    const right = Buffer.from(String(b));
    return left.length === right.length && crypto.timingSafeEqual(left, right);
};

class PasswordHasher {
    hash(password) {
        const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
        const derived = crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex');
        return `${SCHEME}$${salt}$${derived}`;
    }

    // Retorna { valid, needsRehash }. Aceita o formato novo e os legados
    // (texto puro e badCrypto); quem chamar deve regravar com hash() quando needsRehash.
    verify(password, stored) {
        if (typeof stored === 'string' && stored.startsWith(`${SCHEME}$`)) {
            const [, salt, expected] = stored.split('$');
            const derived = crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex');
            return { valid: safeEqual(derived, expected), needsRehash: false };
        }
        const valid = safeEqual(stored, password) || safeEqual(stored, legacyDigest(password));
        return { valid, needsRehash: valid };
    }
}

module.exports = PasswordHasher;
