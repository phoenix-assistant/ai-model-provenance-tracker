import { ComplianceReport } from './compliance';

export function toJSON(report: ComplianceReport): string {
  return JSON.stringify(report, null, 2);
}

export function toHTML(report: ComplianceReport): string {
  const rows = report.checks.map(c => `
    <tr class="${c.passed ? 'pass' : 'fail'}">
      <td>${c.passed ? '✅' : '❌'}</td>
      <td>${c.name}</td>
      <td>${c.details}</td>
    </tr>`).join('');

  return `<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Audit Report — ${report.modelName}</title>
<style>
  body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#1a1a2e}
  h1{color:#16213e}table{width:100%;border-collapse:collapse;margin:1rem 0}
  th,td{padding:.75rem;border:1px solid #ddd;text-align:left}th{background:#16213e;color:#fff}
  .pass{background:#e8f5e9}.fail{background:#ffebee}
  .score{font-size:2rem;font-weight:700;color:${report.passed ? '#2e7d32' : '#c62828'}}
  .badge{display:inline-block;padding:.25rem .75rem;border-radius:4px;color:#fff;
    background:${report.passed ? '#2e7d32' : '#c62828'}}
</style></head><body>
<h1>🔍 AI Model Provenance Audit</h1>
<p><strong>Model:</strong> ${report.modelName} | <strong>ID:</strong> ${report.modelId}</p>
<p><strong>Generated:</strong> ${report.timestamp}</p>
<p class="score">${report.score}% <span class="badge">${report.passed ? 'PASSED' : 'FAILED'}</span></p>
<table><thead><tr><th>Status</th><th>Check</th><th>Details</th></tr></thead><tbody>${rows}</tbody></table>
</body></html>`;
}
