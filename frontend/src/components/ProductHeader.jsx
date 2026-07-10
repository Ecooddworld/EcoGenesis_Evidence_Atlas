const primaryModes = {
  overview: 'Overview',
  workbench: 'Run Compiler',
  evidencePack: 'GBIF Repair Pack',
};

const advancedModes = {
  observatory: 'Evidence Map',
  fragmentGraph: 'Fragment Graph',
  research: 'Regression & Audits',
  formulas: 'Methods & Audits',
  lecture: 'Workflow',
};

export const projectRepositoryUrl = 'https://github.com/Ecooddworld/EcoGenesis_Evidence_Atlas';
export const releaseTagUrl = `${projectRepositoryUrl}/tree/v2-evidence-bounded`;

export default function ProductHeader({ mode, onNavigate, pathForMode }) {
  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">EcoGenesis V2 · Evidence-bounded release · GBIF Challenge 2026</p>
          <h1>Barcode-to-GBIF Evidence Compiler</h1>
          <p className="topbar-subtitle">
            EcoGenesis converts DNA barcode, metabarcoding, Sequence ID and BLAST-like outputs into bounded
            taxonomic rank decisions, publication-readiness checks, repair actions and downloadable Evidence Packs.
          </p>
          <div className="topbar-links" aria-label="Project links">
            <a href={projectRepositoryUrl} target="_blank" rel="noreferrer">Source repository</a>
            <a href={releaseTagUrl} target="_blank" rel="noreferrer">V2 source release</a>
          </div>
        </div>
        <nav className="mode-switch" aria-label="View mode">
          {Object.entries(primaryModes).map(([id, label]) => (
            <a
              key={id}
              className={mode === id ? 'active' : ''}
              href={pathForMode(id)}
              onClick={(event) => {
                event.preventDefault();
                onNavigate(id);
              }}
            >
              {label}
            </a>
          ))}
          <details className="advanced-nav">
            <summary>Advanced</summary>
            <div>
              {Object.entries(advancedModes).map(([id, label]) => (
                <a
                  key={id}
                  className={mode === id ? 'active' : ''}
                  href={pathForMode(id)}
                  onClick={(event) => {
                    event.preventDefault();
                    onNavigate(id);
                  }}
                >
                  {label}
                </a>
              ))}
            </div>
          </details>
          <a href="/submission-video/">Video Presentation</a>
        </nav>
      </header>
      <aside className="product-scope-notice" aria-label="Product validation scope">
        <strong>V2 prototype scope</strong>
        <span>
          Rule-based evidence compiler—not an independently validated taxonomic identifier or a GBIF publisher.
          Outputs remain validation candidates and need external reference, dataset and expert review.
        </span>
      </aside>
    </>
  );
}
