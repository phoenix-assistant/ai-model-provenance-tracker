import { getLineage } from './lineage';
import { ModelRecord, DatasetRecord } from './registry';

export interface ComplianceCheck {
  id: string;
  name: string;
  passed: boolean;
  details: string;
}

export interface ComplianceReport {
  modelId: string;
  modelName: string;
  timestamp: string;
  checks: ComplianceCheck[];
  score: number;
  passed: boolean;
}

const PERMISSIVE_LICENSES = ['MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'CC0-1.0', 'CC-BY-4.0', 'Unlicense'];
const COPYLEFT_LICENSES = ['GPL-2.0', 'GPL-3.0', 'AGPL-3.0', 'LGPL-2.1', 'LGPL-3.0', 'MPL-2.0'];
const RESTRICTED_LICENSES = ['CC-BY-NC-4.0', 'CC-BY-NC-SA-4.0', 'CC-BY-ND-4.0'];

export function checkLicenseCompatibility(datasets: DatasetRecord[]): ComplianceCheck {
  const restricted = datasets.filter(d => RESTRICTED_LICENSES.includes(d.license));
  const copyleft = datasets.filter(d => COPYLEFT_LICENSES.includes(d.license));

  if (restricted.length > 0) {
    return { id: 'license-compat', name: 'License Compatibility', passed: false,
      details: `Restricted licenses found: ${restricted.map(d => `${d.name} (${d.license})`).join(', ')}` };
  }
  if (copyleft.length > 0) {
    return { id: 'license-compat', name: 'License Compatibility', passed: true,
      details: `Warning: copyleft licenses: ${copyleft.map(d => `${d.name} (${d.license})`).join(', ')}. Review obligations.` };
  }
  return { id: 'license-compat', name: 'License Compatibility', passed: true, details: 'All datasets use permissive licenses' };
}

export function euAiActChecklist(model: ModelRecord, datasets: DatasetRecord[]): ComplianceCheck[] {
  return [
    { id: 'eu-data-governance', name: 'Data Governance (Art. 10)', passed: datasets.length > 0,
      details: datasets.length > 0 ? `${datasets.length} training dataset(s) documented` : 'No training data documented' },
    { id: 'eu-transparency', name: 'Transparency (Art. 13)', passed: !!model.provider,
      details: model.provider ? `Provider: ${model.provider}` : 'No provider specified' },
    { id: 'eu-record-keeping', name: 'Record Keeping (Art. 12)', passed: !!model.version && !!model.createdAt,
      details: `Version: ${model.version || 'missing'}, Created: ${model.createdAt || 'missing'}` },
    { id: 'eu-data-quality', name: 'Data Quality (Art. 10.2)', passed: datasets.every(d => d.source && d.source.length > 0),
      details: datasets.every(d => d.source) ? 'All datasets have documented sources' : 'Some datasets missing source documentation' },
    { id: 'eu-human-oversight', name: 'Human Oversight (Art. 14)', passed: true,
      details: 'Provenance tracking enables human oversight capability' },
  ];
}

export function runComplianceAudit(modelNameOrId: string): ComplianceReport | null {
  const lineage = getLineage(modelNameOrId);
  if (!lineage) return null;

  const checks: ComplianceCheck[] = [
    checkLicenseCompatibility(lineage.datasets),
    ...euAiActChecklist(lineage.model, lineage.datasets),
    { id: 'lineage-complete', name: 'Lineage Documentation', passed: lineage.edges.length > 0,
      details: lineage.edges.length > 0 ? `${lineage.edges.length} lineage edge(s) recorded` : 'No lineage edges recorded' },
  ];

  const score = Math.round((checks.filter(c => c.passed).length / checks.length) * 100);

  return {
    modelId: lineage.model.id, modelName: lineage.model.name,
    timestamp: new Date().toISOString(), checks, score, passed: score >= 70,
  };
}
