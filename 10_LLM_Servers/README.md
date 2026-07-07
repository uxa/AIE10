<p align = "center" draggable="false" ><img src="https://github.com/AI-Maker-Space/LLM-Dev-101/assets/37101144/d1343317-fa2f-41e1-8af1-1dbb18399719"
     width="200px"
     height="auto"/>
</p>

## <h1 align="center" id="heading">Session 10: LLM Servers</h1>

| 📰 Session Sheet                                  | ⏺️ Recording                           | 🖼️ Slides                                   | 👨‍💻 Repo       | 📝 Homework                                              | 📁 Feedback                        |
| ------------------------------------------------- | -------------------------------------- | ------------------------------------------- | ------------- | -------------------------------------------------------- | ---------------------------------- |
| [Session 10: LLM Servers](https://github.com/AI-Maker-Space/The-AI-Engineering-Certification-v1.0/tree/main/00_Docs/Modules/10_LLM_Servers) |[Recording!](https://us02web.zoom.us/rec/share/zXd6__uO2RwCmJUmNyGKY01sbwYjjrkpDDNPbfK_Es0MANaqRpFOqqYX4sEVYY1d.gJwTZk1729siXnjj) <br> passcode: `^1$@$R@.`| [Session 10 Slides](https://canva.link/953giejzt5igxvw) |You are here! | [Session 10 Assignment](https://forms.gle/hKxFnEM8U16fCCnG8) | [Feedback 7/2](https://forms.gle/uj2QvYjHfHKFFQ8a6) |

**⚠️!!! PLEASE BE SURE TO SHUTDOWN YOUR DEDICATED ENDPOINT ON FIREWORKS AI WHEN YOU'RE FINISHED YOUR ASSIGNMENT !!!⚠️**

# Build 🏗️

In today's assignment, we'll be creating Fireworks AI endpoints, and then building a RAG application.

- 🤝 Breakout Room #1
  - Set-up Open Source Endpoint (Instructions [here](./ENDPOINT_SETUP.md)) ((This process may take 15-20min.))
  - Test Endpoint and Embeddings with the `endpoint_slammer.ipynb` notebook.

- 🤝 Breakout Room #2
  - Use the Open Source Endpoints to build a RAG LangGraph application

# Ship 🚢

The completed notebook and your RAG app/notebook!

### Deliverables

- A short Loom of either:
  - the notebook and the RAG application you built for the Main Homework Assignment; or
  - the notebook you created for the Advanced Build

# Share 🚀

Make a social media post about your final application!

### Deliverables

- Make a post on any social media platform about what you built!

Here's a template to get you started:

```
🚀 Exciting News! 🚀

I am thrilled to announce that I have just built and shipped a RAG application powered by open-source endpoints! 🎉🤖

🔍 Three Key Takeaways:
1️⃣
2️⃣
3️⃣

Let's continue pushing the boundaries of what's possible in the world of AI and question-answering. Here's to many more innovations! 🚀
Shout out to @AIMakerspace !

#LangChain #QuestionAnswering #RetrievalAugmented #Innovation #AI #TechMilestone

Feel free to reach out if you're curious or would like to collaborate on similar projects! 🤝🔥
```

# Submitting You Homework

## Main Homework Assignment

Follow these steps to prepare and submit your homework assignment:

1. Follow the instructions in `ENDPOINT_SETUP.md`
2. Replace both `model` values in `endpoint_slammer.ipynb` with the `gpt-oss` endpoint you created in Step 1
3. Run the code cells in `endpoint_slammer.ipynb`
4. Respond to the questions in the section below
5. Build a sample RAG
6. Record a Loom video reviewing what you have learned from this session

**⚠️!!! PLEASE BE SURE TO SHUTDOWN YOUR DEDICATED ENDPOINT ON FIREWORKS AI WHEN YOU HAVE FINISHED YOUR ASSIGNMENT !!!⚠️**

## Questions

### ❓ Question #1:

What is the difference between serverless and dedicated endpoints?

#### ✅ Answer:

A serverless endpoint (e.g. `accounts/fireworks/models/gpt-oss-20b`) is a shared, multi-tenant deployment that Fireworks already runs. You pay per token, there's no setup, and it scales automatically, but you're queued behind other tenants' traffic, so throughput and latency are variable and not guaranteed under load — this showed up in `endpoint_slammer.ipynb` where 24 concurrent requests all returned fine but at different speeds.

A dedicated endpoint (created via `firectl create deployment` or the web UI) provisions GPUs exclusively for you. You pay for the GPU-hours regardless of usage (billed hourly, e.g. ~$36/hr for the example shape), but you get predictable, guaranteed capacity and latency because no other tenant competes for it. Dedicated makes sense for production workloads with steady traffic; serverless makes sense for experimentation, low/bursty traffic, or cost-sensitive prototypes — which is why the setup guide warns to shut dedicated deployments down when not in use.

### ❓ Question #2:

Why is it important to consider token throughput and latency when choosing an LLM for user-facing applications?

#### ✅ Answer:

Throughput (tokens/sec) and latency (time to first token, total response time) directly determine how "responsive" the app feels. A user-facing chat or agent app that streams slowly, or takes seconds before the first token appears, reads as broken or laggy even if the model's answer quality is excellent — users abandon slow interfaces regardless of correctness.

They also interact with cost and scale: a model with higher throughput per GPU serves more concurrent users at the same hardware cost, and low per-request latency matters even more once you add agentic loops (tool calls, retries, multi-step reasoning like the `agent_with_helpfulness` loop) since latency compounds across each hop. Picking an LLM purely on benchmark quality while ignoring throughput/latency risks a model that's accurate but too slow or too expensive to serve at the concurrency your application actually needs.

## Activity 1: RAGAS Evaluation with Cost Analysis

Use RAGAS to evaluate your open-source Fireworks AI powered RAG app against an OpenAI `gpt-4.1-mini` powered equivalent. Compare retrieval quality, answer faithfulness, and end-to-end accuracy across both providers.

Additionally, instrument both pipelines with **LangSmith** to capture token usage and cost per query. Use LangSmith's tracing and cost dashboards to compare the total cost of running each provider at scale. Include your evaluation results, cost breakdown, and analysis in your Loom video.

**Implemented:** `app/eval/ragas_eval.py` — builds a Fireworks-backed and an OpenAI (`gpt-4.1-mini`) backed RAG pipeline over the same cat-health PDF corpus, scores both with RAGAS (`faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`), and prints an estimated cost breakdown per provider based on token usage. Both pipelines tag their LLM calls (`ragas-eval`, `provider:fireworks` / `provider:openai`) so LangSmith traces can be filtered per provider when `LANGSMITH_TRACING=true`.

```bash
uv run python -m app.eval.ragas_eval
```

**Results** (3-question eval set over the cat-health PDF corpus):

| Provider | Faithfulness | Answer Relevancy | Context Precision | Context Recall | Input/Output Tokens | Est. Cost |
|---|---|---|---|---|---|---|
| Fireworks (`gpt-oss-20b`) | 0.333 | 0.315 | 0.333 | 0.333 | 10,775 / 1,065 | $0.0024 |
| OpenAI (`gpt-4.1-mini`) | 0.667 | 0.316 | 0.333 | 0.333 | 10,961 / 153 | $0.0046 |

**Analysis:** Retrieval quality (context precision/recall) is identical between providers, as expected — both share the same chunking and are evaluated against the same retrieved contexts per question. `gpt-4.1-mini` scored 2x higher on faithfulness (its answers stuck more tightly to the retrieved context, with far fewer output tokens per answer), while answer relevancy was a near tie. Fireworks was ~2x cheaper per query on this tiny eval set, but generated ~7x more output tokens per answer for a similar relevancy score — on faithfulness specifically, the open-source model paraphrased/extrapolated more than gpt-4.1-mini did. At larger scale, whether Fireworks' lower per-token price offsets its lower faithfulness depends on how much faithfulness deviation is acceptable for the application (e.g., unacceptable for medical-adjacent content like this cat-health corpus).

## Advanced Activity: Local Models

Swap out the Fireworks AI endpoints for **locally-running open-source models** using [Ollama](https://ollama.com/) or another local inference server of your choice. Run both your embedding model and your chat model locally, and rebuild the RAG pipeline on top of them.

- Compare quality and latency between the local setup and your Fireworks AI hosted endpoint.
- Reflect: what are the trade-offs of local models vs. managed endpoints in a production setting?

Include your findings and a demo in your Loom video.

**Implemented:** `app/local_rag.py` — same retrieve-then-generate RAG graph as `app/rag.py`, but backed by `ChatOllama`/`OllamaEmbeddings` (defaults: `llama3.2` chat, `nomic-embed-text` embeddings) instead of Fireworks. Prints latency per query for easy comparison against the hosted endpoint.

```bash
brew install ollama && ollama serve   # separate terminal
ollama pull llama3.2
ollama pull nomic-embed-text
uv run python -m app.local_rag "What vaccinations do kittens need?"
```

**Findings:** Ran the same query ("What vaccinations do kittens need?") against both pipelines cold (including PDF load + embed + retrieve + generate, no caching):

| Pipeline | Chat model | Embedding model | Latency | Answer quality |
|---|---|---|---|---|
| Fireworks (hosted) | `gpt-oss-20b` | `qwen3-embedding-8b` | ~11.8s | Correct, well-structured, cited core feline vaccines (rabies, FHV-1, FCV, FPV, FeLV) |
| Local (Ollama) | `llama3.2` (3B) | `nomic-embed-text` | ~10.3s | Also correct and complete, near-identical content to the Fireworks answer |

Both cold-run latencies are dominated by rebuilding the in-memory vector store (PDF load + chunk + embed) each call rather than pure generation time — a fairer production comparison would keep the vector store warm and only measure per-query retrieve+generate latency.

**Trade-offs:**
- **Cost:** local is $0 per token/query (only your machine's compute/electricity); Fireworks bills per token, and dedicated deployments bill hourly regardless of usage.
- **Quality:** the 3B `llama3.2` matched `gpt-oss-20b`'s answer quality on this simple factual RAG query, but a much smaller local model is more likely to fall behind on harder reasoning or longer-context tasks.
- **Latency/throughput at scale:** local is single-machine bound — one request at a time on typical consumer hardware, no autoscaling. Fireworks serverless/dedicated can scale to many concurrent users.
- **Ops burden:** local requires you to manage the runtime, model updates, and hardware yourself; managed endpoints offload that but reintroduce billing/account risk (as seen firsthand with the Fireworks suspension earlier in this session).
- **Data privacy:** local keeps all data on-device — relevant for sensitive corpora that shouldn't leave your infrastructure.
