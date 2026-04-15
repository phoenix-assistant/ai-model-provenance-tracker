import { load, save } from './storage';
import { getModel, getDataset, ModelRecord, DatasetRecord } from './registry';

export interface LineageEdge {
  datasetId: string;
  modelId: string;
  relationship: string;
}

export interface LineageGraph {
  model: ModelRecord;
  datasets: DatasetRecord[];
  edges: LineageEdge[];
}

export function addLineage(datasetId: string, modelId: string, relationship = 'trained_on'): LineageEdge {
  const data = load();
  const edge: LineageEdge = { datasetId, modelId, relationship };
  data.lineage.push(edge);
  save(data);
  return edge;
}

export function getLineage(modelNameOrId: string): LineageGraph | null {
  const model = getModel(modelNameOrId);
  if (!model) return null;

  const data = load();
  const edges = data.lineage.filter((e: LineageEdge) => e.modelId === model.id);
  const datasets = edges
    .map((e: LineageEdge) => getDataset(e.datasetId))
    .filter(Boolean) as DatasetRecord[];

  return { model, datasets, edges };
}

export function getUpstreamModels(datasetNameOrId: string): ModelRecord[] {
  const dataset = getDataset(datasetNameOrId);
  if (!dataset) return [];
  const data = load();
  const modelIds = data.lineage
    .filter((e: LineageEdge) => e.datasetId === dataset.id)
    .map((e: LineageEdge) => e.modelId);
  return modelIds.map((id: string) => getModel(id)).filter(Boolean) as ModelRecord[];
}
