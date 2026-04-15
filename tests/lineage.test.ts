import fs from 'fs';
import path from 'path';
import { registerModel, registerDataset, listModels, listDatasets } from '../src/registry';
import { addLineage, getLineage } from '../src/lineage';
import { runComplianceAudit } from '../src/compliance';
import { toJSON, toHTML } from '../src/reporter';

const TEST_STORE = path.join(__dirname, '.test-provenance.json');

beforeEach(() => {
  // Point storage to test file
  process.chdir(__dirname);
  if (fs.existsSync(TEST_STORE)) fs.unlinkSync(TEST_STORE);
  const storePath = path.join(__dirname, '.provenance-data.json');
  if (fs.existsSync(storePath)) fs.unlinkSync(storePath);
});

afterAll(() => {
  const storePath = path.join(__dirname, '.provenance-data.json');
  if (fs.existsSync(storePath)) fs.unlinkSync(storePath);
});

test('register model and dataset', () => {
  const ds = registerDataset({ name: 'CommonCrawl', license: 'CC0-1.0', source: 'commoncrawl.org', metadata: {} });
  const model = registerModel({ name: 'test-model', version: '1.0', provider: 'TestCorp', trainingDataRefs: [ds.id], metadata: {} });
  expect(model.name).toBe('test-model');
  expect(ds.name).toBe('CommonCrawl');
  expect(listModels()).toHaveLength(1);
  expect(listDatasets()).toHaveLength(1);
});

test('lineage graph', () => {
  const ds = registerDataset({ name: 'WikiText', license: 'MIT', source: 'huggingface', metadata: {} });
  const model = registerModel({ name: 'lineage-model', version: '2.0', provider: 'AI Inc', trainingDataRefs: [], metadata: {} });
  addLineage(ds.id, model.id, 'trained_on');
  const graph = getLineage('lineage-model');
  expect(graph).not.toBeNull();
  expect(graph!.datasets).toHaveLength(1);
  expect(graph!.edges[0].relationship).toBe('trained_on');
});

test('compliance audit', () => {
  const ds = registerDataset({ name: 'OpenData', license: 'Apache-2.0', source: 'github.com/open', metadata: {} });
  const model = registerModel({ name: 'audit-model', version: '1.0', provider: 'AuditCorp', trainingDataRefs: [], metadata: {} });
  addLineage(ds.id, model.id);
  const report = runComplianceAudit('audit-model');
  expect(report).not.toBeNull();
  expect(report!.score).toBeGreaterThanOrEqual(70);
  expect(report!.passed).toBe(true);
});

test('report generation', () => {
  const ds = registerDataset({ name: 'TestDS', license: 'MIT', source: 'test', metadata: {} });
  const model = registerModel({ name: 'report-model', version: '1.0', provider: 'RC', trainingDataRefs: [], metadata: {} });
  addLineage(ds.id, model.id);
  const report = runComplianceAudit('report-model')!;
  expect(JSON.parse(toJSON(report)).modelName).toBe('report-model');
  expect(toHTML(report)).toContain('report-model');
});
