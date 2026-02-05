/**
 * Generate JWT client assertion for OAuth2 authentication
 *
 * @param {object} bru - Bruno runtime object
 * @param {object} req - Request object
 * @param {string} audienceUrl - The audience URL for the token
 * @param {string} kid - The key ID for the JWT header
 */
function generateAuthToken(bru, req, audienceUrl, kid) {
  const jwt = require("jsonwebtoken");
  const fs = require("fs");
  const crypto = require("crypto");

  const secret = bru.getEnvVar("JWT_SECRET");
  const privateKeyPath = bru.getEnvVar("PRIVATE_KEY_PATH");

  if (!secret) {
    throw new Error("JWT_SECRET environment variable is missing.");
  }
  if (!privateKeyPath) {
    throw new Error("PRIVATE_KEY_PATH environment variable is missing.");
  }

  const privateKey = fs.readFileSync(privateKeyPath);

  const payload = {
    sub: secret,
    iss: secret,
    jti: crypto.randomUUID(),
    aud: audienceUrl,
    exp: (Date.now() / 1000) + 300
  };

  const options = {
    algorithm: 'RS512',
    header: { kid: kid }
  };

  const token = jwt.sign(payload, privateKey, options);

  let new_body = req.getBody();
  new_body.push({ name: "client_assertion", value: token });

  req.setBody(new_body);
}

module.exports = { generateAuthToken };
