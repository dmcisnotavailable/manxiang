import { readFileSync } from "node:fs";
import { Agent, type AgentEvent } from "@earendil-works/pi-agent-core";
import { configuredModel } from "./llm.js";
import { systemPrompt, runPrompt } from "./prompts.js";
import { manxiangTools } from "./tools.js";
import type { BridgeRunInput } from "./types.js";

const input = JSON.parse(readFileSync(0, "utf8")) as BridgeRunInput;
const { models, model, modelName } = configuredModel();
const events: unknown[] = [];
const toolCalls: string[] = [];

const agent = new Agent({
  streamFn: models.streamSimple.bind(models),
  toolExecution: "sequential",
  initialState: {
    systemPrompt: systemPrompt(input),
    model,
    thinkingLevel: "medium",
    tools: manxiangTools(),
  },
});

agent.subscribe((event: AgentEvent) => {
  if (event.type === "tool_execution_start") {
    toolCalls.push(event.toolName);
    events.push({ type: "tool.started", tool_name: event.toolName, payload: event.args });
  }
  if (event.type === "tool_execution_end") {
    events.push({
      type: "tool.completed",
      tool_name: event.toolName,
      payload: event.result.details,
    });
  }
});

await agent.prompt(runPrompt);

process.stdout.write(JSON.stringify({ model_name: modelName, tool_calls: toolCalls, events }) + "\n");
