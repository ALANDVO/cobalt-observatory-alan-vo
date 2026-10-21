import { expect, vi } from 'vitest';
import '@testing-library/jest-dom';

// Mock window.confirm
window.confirm = vi.fn(() => true);
