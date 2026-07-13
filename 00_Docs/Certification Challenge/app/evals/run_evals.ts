import { readFile, mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { ChatOpenAI } from "@langchain/openai";
import { HumanMessage } from "@langchain/core/messages";
import { z } from "zod";
import { buildAgent, type RetrieverMode } from "../lib/agent";

type EvalItem = { question: string; ground_truth: string };

const judgeSchema = z.object({
  correctness: z
    .number()
    .min(1)
    .max(5)
    .describe("1-5 how well the answer matches the ground truth"),
  grounded: z
    .boolean()
    .describe("true if the answer is factually supported, not hallucinated"),
  reasoning: z.string().describe("one short sentence of justification"),
});

const judge = new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0 }).withStructuredOutput(
  judgeSchema,
);

async function answer(mode: RetrieverMode, question: string): Promise<string> {
  const agent = await buildAgent(mode);
  const res = await agent.invoke(
    { messages: [new HumanMessage(question)] },
    { configurable: { thread_id: `eval_${Math.random()}` } },
  );
  const last = res.messages[res.messages.length - 1];
  return typeof last.content === "string" ? last.content : JSON.stringify(last.content);
}

async function scoreMode(mode: RetrieverMode, data: EvalItem[]) {
  let totalCorrect = 0;
  let grounded = 0;
  const start = Date.now();

  for (const item of data) {
    const a = await answer(mode, item.question);
    const verdict = await judge.invoke([
      new HumanMessage(
        `You are grading a documentation assistant.\n\nQUESTION: ${item.question}\n\nGROUND TRUTH: ${item.ground_truth}\n\nASSISTANT ANSWER: ${a}\n\nGrade correctness (1-5) and whether it is grounded.`,
      ),
    ]);
    totalCorrect += verdict.correctness;
    if (verdict.grounded) grounded += 1;
    console.log(
      `  [${mode}] ${verdict.correctness}/5 grounded=${verdict.grounded} :: ${item.question.slice(0, 60)}`,
    );
  }

  const n = data.length;
  return {
    mode,
    avgCorrectness: +(totalCorrect / n).toFixed(2),
    groundedRate: +((grounded / n) * 100).toFixed(1),
    avgLatencyMs: Math.round((Date.now() - start) / n),
    n,
  };
}

async function main() {
  if (!process.env.OPENAI_API_KEY) {
    throw new Error("OPENAI_API_KEY is required to run evals.");
  }
  const dataPath = path.join(process.cwd(), "evals", "dataset.json");
  const data: EvalItem[] = JSON.parse(await readFile(dataPath, "utf-8"));

  console.log(`Running evals over ${data.length} questions...\n`);
  const results = [];
  for (const mode of ["naive", "multiquery"] as RetrieverMode[]) {
    console.log(`== Retriever mode: ${mode} ==`);
    results.push(await scoreMode(mode, data));
    console.log("");
  }

  const table = [
    "| Retriever | Avg Correctness (1-5) | Grounded Rate (%) | Avg Latency (ms) | N |",
    "| --- | --- | --- | --- | --- |",
    ...results.map(
      (r) =>
        `| ${r.mode} | ${r.avgCorrectness} | ${r.groundedRate} | ${r.avgLatencyMs} | ${r.n} |`,
    ),
  ].join("\n");

  console.log("\n" + table + "\n");

  const outDir = path.join(process.cwd(), "evals", "results");
  await mkdir(outDir, { recursive: true });
  await writeFile(
    path.join(outDir, `results_${Date.now()}.json`),
    JSON.stringify({ results, table }, null, 2),
  );
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
