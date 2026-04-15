import fs from 'fs';
import path from 'path';

export interface StorageData {
  models: Record<string, any>;
  datasets: Record<string, any>;
  lineage: Array<{ datasetId: string; modelId: string; relationship: string }>;
}

const DEFAULT_PATH = path.join(process.cwd(), '.provenance-data.json');

function defaultData(): StorageData {
  return { models: {}, datasets: {}, lineage: [] };
}

export function load(filePath = DEFAULT_PATH): StorageData {
  if (!fs.existsSync(filePath)) return defaultData();
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  } catch {
    return defaultData();
  }
}

export function save(data: StorageData, filePath = DEFAULT_PATH): void {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}
