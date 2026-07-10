import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import ProductHeader from './ProductHeader.jsx';


describe('ProductHeader', () => {
  it('keeps the validation boundary visible beside primary navigation', () => {
    render(<ProductHeader mode="overview" onNavigate={vi.fn()} pathForMode={(mode) => `/${mode}`} />);

    expect(screen.getByRole('heading', { name: 'Barcode-to-GBIF Evidence Compiler' })).toBeInTheDocument();
    expect(screen.getByText('EcoGenesis V2 · Evidence-bounded release · GBIF Challenge 2026')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'V2 source release' })).toHaveAttribute('href', expect.stringContaining('v2-evidence-bounded'));
    expect(screen.getByLabelText('Product validation scope')).toHaveTextContent('not an independently validated taxonomic identifier');
    expect(screen.getByLabelText('Product validation scope')).toHaveTextContent('Outputs remain validation candidates');
    expect(screen.getByRole('link', { name: 'Run Compiler' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'GBIF Repair Pack' })).toBeInTheDocument();
    expect(screen.getByText('Advanced')).toBeInTheDocument();
  });
});
