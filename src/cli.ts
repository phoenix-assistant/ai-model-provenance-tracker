#!/usr/bin/env node
import { Command } from 'commander';
import fs from 'fs';
import { registerModel, registerDataset, listModels, listDatasets } from './registry';
import { addLineage, getLineage } from './lineage';
import { runComplianceAudit } from './compliance';
import { toJSON, toHTML } from './reporter';

const program = new Command();
program.name('provenance').description('AI Model Provenance Tracker').version('1.0.0');

program.command('register <file>').description('Register a model or dataset from JSON file')
  .action((file: string) => {
    const data = JSON.parse(fs.readFileSync(file, 'utf-8'));
    if (data.type === 'dataset') {
      const ds = registerDataset({ name: data.name, license: data.license, source: data.source, size: data.size, metadata: data.metadata || {} });
      console.log(`✅ Dataset registered: ${ds.name} (${ds.id})`);
    } else {
      const m = registerModel({ name: data.name, version: data.version, provider: data.provider, trainingDataRefs: data.trainingDataRefs || [], metadata: data.metadata || {} });
      console.log(`✅ Model registered: ${m.name} v${m.version} (${m.id})`);
    }
  });

program.command('lineage <model>').description('Show data lineage for a model')
  .action((model: string) => {
    const lineage = getLineage(model);
    if (!lineage) { console.error('❌ Model not found'); process.exit(1); }
    console.log(`\n📊 Lineage for ${lineage.model.name} v${lineage.model.version}`);
    console.log(`Provider: ${lineage.model.provider}`);
    console.log(`\nDatasets (${lineage.datasets.length}):`);
    lineage.datasets.forEach(d => console.log(`  → ${d.name} (${d.license}) [${d.source}]`));
  });

program.command('link <datasetId> <modelId>').description('Link a dataset to a model')
  .option('-r, --relationship <type>', 'Relationship type', 'trained_on')
  .action((datasetId: string, modelId: string, opts: any) => {
    addLineage(datasetId, modelId, opts.relationship);
    console.log(`🔗 Linked dataset ${datasetId} → model ${modelId}`);
  });

program.command('audit').description('Run compliance audit')
  .requiredOption('--model <name>', 'Model name or ID')
  .option('--format <type>', 'Output format (json|html)', 'json')
  .option('-o, --output <file>', 'Output file')
  .action((opts: any) => {
    const report = runComplianceAudit(opts.model);
    if (!report) { console.error('❌ Model not found'); process.exit(1); }
    const output = opts.format === 'html' ? toHTML(report) : toJSON(report);
    if (opts.output) { fs.writeFileSync(opts.output, output); console.log(`📄 Report saved to ${opts.output}`); }
    else console.log(output);
  });

program.command('list').description('List registered models and datasets')
  .action(() => {
    console.log('\n📦 Models:');
    listModels().forEach(m => console.log(`  ${m.name} v${m.version} (${m.provider})`));
    console.log('\n📁 Datasets:');
    listDatasets().forEach(d => console.log(`  ${d.name} — ${d.license} [${d.source}]`));
  });

program.parse();
