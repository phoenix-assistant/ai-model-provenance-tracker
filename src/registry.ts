import { v4 as uuid } from 'uuid';
import { load, save } from './storage';

export interface ModelRecord {
  id: string;
  name: string;
  version: string;
  provider: string;
  trainingDataRefs: string[];
  createdAt: string;
  metadata: Record<string, any>;
}

export interface DatasetRecord {
  id: string;
  name: string;
  license: string;
  source: string;
  size?: string;
  metadata: Record<string, any>;
}

export function registerModel(input: Omit<ModelRecord, 'id' | 'createdAt'>): ModelRecord {
  const data = load();
  const model: ModelRecord = { id: uuid(), createdAt: new Date().toISOString(), ...input };
  data.models[model.id] = model;
  save(data);
  return model;
}

export function registerDataset(input: Omit<DatasetRecord, 'id'>): DatasetRecord {
  const data = load();
  const dataset: DatasetRecord = { id: uuid(), ...input };
  data.datasets[dataset.id] = dataset;
  save(data);
  return dataset;
}

export function getModel(nameOrId: string): ModelRecord | undefined {
  const data = load();
  return Object.values(data.models).find(
    (m: any) => m.id === nameOrId || m.name === nameOrId
  ) as ModelRecord | undefined;
}

export function getDataset(nameOrId: string): DatasetRecord | undefined {
  const data = load();
  return Object.values(data.datasets).find(
    (d: any) => d.id === nameOrId || d.name === nameOrId
  ) as DatasetRecord | undefined;
}

export function listModels(): ModelRecord[] {
  return Object.values(load().models);
}

export function listDatasets(): DatasetRecord[] {
  return Object.values(load().datasets);
}
