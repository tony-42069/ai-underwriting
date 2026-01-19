export default [
  {
    ignores: ['dist', '.eslintrc.cjs'],
  },
  {
    files: ['**/*.{ts,mts,tsx,jsx}'],
    rules: {
      'react-refresh/only-export-components': 'off',
    },
  },
]
