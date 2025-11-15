import React from 'react';
import { render } from '@testing-library/react';
import App from './App';

test('renders without crashing', () => {
  const { container } = render(<App />);
  // Basic test to ensure the app renders
  expect(container).toBeTruthy();
});
