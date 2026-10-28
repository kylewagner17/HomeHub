module.exports = {
  preset: '@react-native/jest-preset',
  setupFiles: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@homehub/shared$': '<rootDir>/../../packages/shared/src/index.ts',
  },
};
