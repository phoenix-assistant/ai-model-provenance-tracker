import express from 'express';
import { listModels, listDatasets, getModel } from './registry';
import { getLineage } from './lineage';
import { runComplianceAudit } from './compliance';
import { toHTML } from './reporter';

export function createApp() {
  const app = express();
  app.use(express.json());

  app.get('/', (_req, res) => {
    const models = listModels();
    const datasets = listDatasets();
    const rows = models.map(m => `<tr><td><a href="/models/${m.name}">${m.name}</a></td><td>${m.version}</td><td>${m.provider}</td><td><a href="/audit/${m.name}">Audit</a></td></tr>`).join('');
    res.send(`<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Provenance Dashboard</title>
<style>body{font-family:system-ui;max-width:960px;margin:2rem auto;padding:0 1rem}table{width:100%;border-collapse:collapse}th,td{padding:.5rem;border:1px solid #ddd;text-align:left}th{background:#16213e;color:#fff}a{color:#1565c0}</style></head><body>
<h1>📊 AI Model Provenance Dashboard</h1>
<h2>Models (${models.length})</h2>
<table><thead><tr><th>Name</th><th>Version</th><th>Provider</th><th>Actions</th></tr></thead><tbody>${rows}</tbody></table>
<h2>Datasets (${datasets.length})</h2>
<p>${datasets.map(d => `${d.name} (${d.license})`).join(', ') || 'None registered'}</p>
</body></html>`);
  });

  app.get('/models/:name', (req, res) => {
    const lineage = getLineage(req.params.name);
    if (!lineage) return res.status(404).send('Model not found');
    res.json(lineage);
  });

  app.get('/audit/:name', (req, res) => {
    const report = runComplianceAudit(req.params.name);
    if (!report) return res.status(404).send('Model not found');
    if (req.query.format === 'json') return res.json(report);
    res.send(toHTML(report));
  });

  app.get('/api/models', (_req, res) => res.json(listModels()));
  app.get('/api/datasets', (_req, res) => res.json(listDatasets()));

  return app;
}

if (require.main === module) {
  const port = parseInt(process.env.PORT || '3000');
  createApp().listen(port, () => console.log(`Provenance dashboard running on http://localhost:${port}`));
}
