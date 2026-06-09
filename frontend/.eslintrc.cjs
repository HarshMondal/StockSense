/* Minimal config. The build does NOT depend on eslint; typescript-eslint
   plugins are intentionally omitted because they are not installed. */
module.exports = {
  root: true,
  env: { browser: true, es2021: true },
  extends: ['eslint:recommended'],
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  ignorePatterns: ['dist', 'node_modules', '*.config.js', '*.config.ts'],
};
