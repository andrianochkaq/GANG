/* eslint-env node */

// Naming rules follow docs/conventions.md (TypeScript / React section).
const BOOLEAN_PREFIXES = ['is', 'has', 'should', 'can'];
// No one-letter names, except `_` and `t` from react-i18next.
const SHORT_NAME_PATTERN = '^(_|t|.{2,})$';

module.exports = {
  root: true,
  env: { browser: true, es2022: true },
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
    // Type information is needed to tell which variables are booleans.
    project: './tsconfig.json',
    tsconfigRootDir: __dirname,
  },
  settings: { react: { version: 'detect' } },
  plugins: ['@typescript-eslint', 'react', 'react-hooks'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime',
    'plugin:react-hooks/recommended',
    // Last: switches off the rules that Prettier already handles.
    'prettier',
  ],
  ignorePatterns: ['dist', 'coverage', 'node_modules'],
  rules: {
    // Props are checked by TypeScript.
    'react/prop-types': 'off',
    'react/jsx-pascal-case': 'error',
    'react/self-closing-comp': 'error',
    '@typescript-eslint/naming-convention': [
      'error',
      {
        selector: 'variable',
        format: ['camelCase', 'UPPER_CASE'],
        custom: { regex: SHORT_NAME_PATTERN, match: true },
      },
      // Components are PascalCase, hooks and helpers are camelCase.
      { selector: 'variable', types: ['function'], format: ['camelCase', 'PascalCase'] },
      {
        selector: 'variable',
        types: ['boolean'],
        format: ['PascalCase'],
        prefix: BOOLEAN_PREFIXES,
        // Constants such as DEBUG_MODE stay SCREAMING_SNAKE_CASE.
        filter: { regex: '^[A-Z0-9_]+$', match: false },
      },
      {
        selector: 'function',
        format: ['camelCase', 'PascalCase'],
        custom: { regex: SHORT_NAME_PATTERN, match: true },
      },
      {
        selector: 'parameter',
        format: ['camelCase'],
        leadingUnderscore: 'allow',
        custom: { regex: SHORT_NAME_PATTERN, match: true },
      },
      { selector: 'typeLike', format: ['PascalCase'] },
      // Interfaces have no I prefix: ProductCardProps, not IProductCardProps.
      {
        selector: 'interface',
        format: ['PascalCase'],
        custom: { regex: '^I[A-Z]', match: false },
      },
    ],
  },
};
