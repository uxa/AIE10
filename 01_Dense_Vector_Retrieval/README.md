<p align = "center" draggable="false" ><img src="https://github.com/AI-Maker-Space/LLM-Dev-101/assets/37101144/d1343317-fa2f-41e1-8af1-1dbb18399719"
     width="200px"
     height="auto"/>
</p>

<h1 align="center" id="heading">Session 1: Dense Vector Retrieval</h1>

### [Quicklinks]()

| 📰 Module Sheet                                                                 | ⏺️ Recording | 🖼️ Slides | 👨‍💻 Repo       | 📝 Homework | 📁 Feedback |
| :------------------------------------------------------------------------------- | :----------- | :-------- | :------------ | :---------- | :---------- |
| [Dense Vector Retrieval](../00_Docs/Modules/01_Dense_Vector_Retrieval/README.md) |[Recording!](https://us02web.zoom.us/rec/share/sHWvo0Nd1aI0SEhKecOLEX9kFGVJJAdYfsKiuTmm8t85W48Z2lnjpnzTy8jAd8R5.PwuqibGwAZhvDd8c) <br> passcode: `C62n^@Q!`| [Session 1 Slides](https://canva.link/htfqf8i39yejyhn) | You are here! | [Session 1 Assignment](https://forms.gle/Z9qskfVaAvPjn6gz8) | [Feedback 6/2](https://forms.gle/21a2uoL9DVZPwgJP6) |


## 🏗️ How AIM Does Assignments

> 📅 **Assignments will always be released to students as live class begins.** We will never release assignments early.

Each assignment will have a few of the following categories of exercises:

- ❓ **Questions** - these will be questions that you will be expected to gather the answer to. These can appear as general questions, or questions meant to spark a discussion in your breakout rooms.

- 🏗️ **Activities** - these will be work or coding activities meant to reinforce specific concepts or theory components.

- 🚧 **Advanced Builds (optional)** - Take on a challenge. These builds require you to create something with minimal guidance outside of the documentation.

## Main Assignment

In this assignment, you will build a vector RAG application using LangChain v1, OpenAI embeddings, and Qdrant.

The main notebook is:

```text
01_Cat_Health_Vector_RAG_LangChain_Qdrant.ipynb
```

The notebook uses the bundled cat health guideline PDF in `data/cat_health_guidelines.pdf`.

### Setup

From this folder, install the environment with uv:

```bash
uv sync
```

Then open the notebook in Cursor or VS Code and select the Python/Jupyter environment created by uv.

You will also need an OpenAI API key available when running the notebook.

---

## 🏗️ Activity #1: Embedding Similarity

Run the embedding similarity primer in the notebook.

You will compare embeddings for terms like:

- `king`
- `queen`
- `banana`
- `cat`
- `veterinarian`
- `cat health guidelines`

#### ❓Question #1

Why is cosine similarity useful for dense vector retrieval?

##### ✅ Answer:

Cosine similarity is useful for dense vector retrieval because it measures the cosine of the angle between two vectors, which indicates how similar their directions are regardless of their magnitude. This is particularly useful in information retrieval because it focuses on the orientation of the vectors rather than their absolute values, making it effective for comparing documents or queries in high-dimensional spaces.

## 🏗️ Activity #2: Build the Vector RAG Pipeline

Run the notebook sections that:

1. Load the PDF into LangChain `Document` objects
2. Split the document into chunks
3. Embed the chunks
4. Store the chunk embeddings in in-memory Qdrant
5. Retrieve relevant chunks with similarity scores
6. Generate an answer grounded in retrieved context

#### ❓Question #2

Why is metadata important for a RAG application?

##### ✅ Answer:

Metadata is important for a RAG application because it provides additional context about the retrieved chunks, which can help in filtering and ranking the results. It can also be used to provide more detailed information about the source of the retrieved chunks, which can be useful for the user.

#### ❓Question #3

What tradeoff do we make when choosing chunk size and chunk overlap?

##### ✅ Answer:

When choosing chunk size and chunk overlap, we make a tradeoff between retrieval quality and computational efficiency. Larger chunks can capture more context but may include irrelevant information, while smaller chunks may miss important context. Overlap helps maintain context continuity but increases storage and retrieval costs.

#### ❓Question #4

What does a similarity score help you understand, and what does it not prove by itself?

##### ✅ Answer:

The similarity score helps you understand how closely the retrieved chunk matches the query in terms of vector space distance. It provides a quantitative measure of relevance, allowing you to rank and filter results. However, it does not prove the factual accuracy or completeness of the retrieved information, nor does it guarantee that the context is sufficient for generating a correct answer. It is a heuristic measure that should be used in conjunction with other evaluation methods to assess retrieval quality.


## 🏗️ Activity #3: Vibe Check Retrieval Quality

Run the notebook's vibe check queries and inspect both:

- The retrieved context
- The generated answer

#### ❓Question #5

For the vibe check queries, did the retrieved context seem relevant before generation? Why or why not?

##### ✅ Answer:

Yes, the retrieved context seemed relevant before generation because the similarity scores were high and the chunks contained information related to the queries. However, the context was not always sufficient to generate a complete and accurate answer, as some queries required more specific information that was not present in the retrieved chunks.


## 🏗️ Activity #4: Tune Retrieval

Improve retrieval quality by changing one or more of:

- Chunk size
- Chunk overlap
- Retrieval `k`
- Query wording

Document what changed and whether retrieval improved.

##### Settings Changed:

- Replaced the `RecursiveCharacterTextSplitter` with `NLTKTextSplitter`
- Reduced chunk size from 1000 to 500
- Increased chunk overlap from 200 to 100
- Increased retrieval `k` from 4 to 6

##### Results:

| Config | Splitter | Chunk | Overlap | k | Chunks | Avg Score | Spread | Noisy |
|--------|----------|-------|---------|---|--------|-----------|--------|-------|
| Baseline | `recursive` | 1000 | 200 | 4 | 135 | 0.568 | 0.031 | 0/4 |
| Run 2 | `nltk` | 1000 | 200 | 4 | 135 | 0.586 | 0.026 | 0/4 |
| Run 3 | `nltk` | 500 | 100 | 6 | 271 | 0.569 | 0.024 | 0/6 |

1. **Switching to `NLTKTextSplitter` at the same chunk size (1000) improved avg similarity from 0.568 → 0.586** and tightened the score spread from 0.031 → 0.026. NLTK's sentence-aware boundaries kept semantically complete sentences together, producing more focused chunks that matched the query more consistently.

2. **Reducing chunk size to 500 with k=6 brought avg score back down to 0.569** — smaller chunks are more granular but each one covers less topic area, so individual match quality dropped slightly. The benefit was broader coverage: 6 sources from more pages of the PDF gave the LLM more angles to synthesize the answer from.

3. **All 3 runs had 0 noisy chunks (all scores above 0.45)**, confirming the query was a strong match for this document regardless of configuration. The best overall retrieval quality was Run 2 (NLTK, chunk=1000, k=4): highest avg score, lowest spread, and fewer API calls than k=6.

---

## Optional Deep Dive: RAG From Scratch

If you want to look underneath the library abstractions, run the optional reference notebook:

```text
02_Cat_Health_Vector_RAG_From_Scratch.ipynb
```

It builds the same retrieval pipeline again with only:

- `pypdf` for extracting text from the PDF
- Python standard-library HTTP requests for calling OpenAI
- Handcrafted document, chunking, embedding, similarity-search, vector-store, and generation primitives

This notebook is a reference walkthrough, not an additional assignment. Its purpose is to make the responsibilities hidden by LangChain, Qdrant, and provider SDKs visible.

---

## Submitting Your Homework

### Main Assignment

Follow these steps to prepare and submit your homework:

1. Pull the latest updates from upstream into the main branch of your AIE9 repo:

```bash
git checkout main
git pull upstream main
git push origin main
```

2. Start Cursor from the `01_Dense_Vector_Retrieval` folder.
3. Complete the notebook.
4. Answer the questions in this `README.md`.
5. Add, commit, and push your modified work to your origin repository.

When submitting your homework, provide the GitHub URL to your AIE9 repo.
