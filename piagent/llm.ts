import { builtinModels } from "@earendil-works/pi-ai/providers/all";

export function configuredModel() {
  const provider = process.env.MANXIANG_LLM_PROVIDER;
  const modelName = process.env.MANXIANG_LLM_MODEL;
  if (!provider || !modelName) {
    throw new Error("MANXIANG_LLM_PROVIDER and MANXIANG_LLM_MODEL are required");
  }
  const models = builtinModels();
  const model = models.getModel(provider, modelName);
  if (!model) {
    throw new Error(`Model not found: ${provider}/${modelName}`);
  }
  return { models, model, modelName };
}
