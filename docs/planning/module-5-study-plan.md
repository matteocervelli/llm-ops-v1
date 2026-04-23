# Module 5 Study Plan And Homelab Experiments

Data: 2026-04-23

## Goal

Usare il mese prima della live per aumentare la tua competenza dove serve davvero, senza disperderti.

## Priority Learning Tracks

### 1. Evals And LLM-as-a-Judge

Perche:

e la parte dove e piu facile sembrare superficiali se non distingui bene:

1. test;
2. eval;
3. judge reliability;
4. monitoring in produzione.

Studia:

1. affidabilita dei judge;
2. design delle rubriche;
3. limiti del multilingual judging;
4. come legare score a trace e run.

### 2. Cost, Routing And Caching

Perche:

e il cuore del discorso operativo.

Studia:

1. prompt caching;
2. cost per request;
3. routing per costo/latency;
4. differenza hosted vs local/open weight.

### 3. Memory And Context

Perche:

e facile raccontarla male o venderla come magia.

Studia:

1. memory taxonomy;
2. evaluation della memoria;
3. write path governance;
4. costi e latenza indotti dalla memoria.

### 4. Dashboard And Observability

Perche:

devi saper spiegare bene la differenza tra:

1. log;
2. trace;
3. score;
4. metriche di business e operative.

## Recent Reading Queue

### Evals / Judge Reliability

1. `Are We on the Right Way to Assessing LLM-as-a-Judge?` - arXiv, 2025-12-17
   Link: https://arxiv.org/abs/2512.16041
   Perche conta: mostra che anche modelli forti restano incoerenti come judge in casi difficili.

2. `LLMs Cannot Reliably Judge (Yet?): A Comprehensive Assessment on the Robustness of LLM-as-a-Judge` - arXiv, 2025-06-11
   Link: https://arxiv.org/abs/2506.09443
   Perche conta: utile per spiegare che `LLM-as-a-Judge` non va venduto come verita assoluta.

3. `An Empirical Study of LLM-as-a-Judge: How Design Choices Impact Evaluation Reliability` - arXiv, 2025-06-16
   Link: https://arxiv.org/abs/2506.13639
   Perche conta: ti aiuta a parlare di rubriche, template e design choices.

4. `How Reliable is Multilingual LLM-as-a-Judge?` - arXiv, 2025-05-18
   Link: https://arxiv.org/abs/2505.12201
   Perche conta: rilevante se vuoi evitare claim troppo forti su audience o output multilingue.

### Caching / Cost / Routing

1. `Auditing Prompt Caching in Language Model APIs` - arXiv, 2025-02-11
   Link: https://arxiv.org/abs/2502.07776
   Perche conta: aggiunge un punto serio su privacy e cache sharing.

2. `Prompt caching` - Anthropic docs
   Link: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
   Perche conta: fonte primaria pratica per la lezione.

3. `Runtime Burden Allocation for Structured LLM Routing in Agentic Expert Systems` - arXiv, 2026-03-26
   Link: https://arxiv.org/abs/2604.01235
   Perche conta: utile per parlare di routing come problema di stack e non solo di prompt.

4. `Dynamic Quality-Latency Aware Routing for LLM Inference in Wireless Edge-Device Networks` - arXiv, 2025-08-15
   Link: https://arxiv.org/abs/2508.11291
   Perche conta: materiale buono per ragionare su qualita-latency tradeoff.

### Memory

1. `Memory in the Age of AI Agents` - arXiv, 2025-12-15
   Link: https://arxiv.org/abs/2512.13564
   Perche conta: chiarisce tassonomie e confusione terminologica.

2. `Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers` - arXiv, 2026-03-10 circa
   Link: https://arxiv.org/abs/2603.07670
   Perche conta: molto utile per costruire una posizione seria e non hype-driven sulla memoria.

### Observability / Tooling

1. Langfuse overview docs
   Link: https://langfuse.com/docs
   Perche conta: ti aiuta a collegare tracing, sessions e scores.

2. Langfuse scores overview
   Link: https://langfuse.com/docs/evaluation/scores/overview
   Perche conta: buono per costruire la mini dashboard o per collegare dashboard e tracing.

## Homelab Experiment Loop

### Experiment 1 - Cost Baseline

Obiettivo:

confrontare hosted vs local su un dataset piccolo.

Misura:

1. latency;
2. costo stimato;
3. output quality score minimo.

### Experiment 2 - Prompt Caching

Obiettivo:

misurare il delta quando sposti contenuto statico in prefissi riusabili.

Misura:

1. token cached;
2. costo;
3. latency;
4. hit rate.

### Experiment 3 - Memory Shapes

Obiettivo:

confrontare:

1. no memory;
2. session state only;
3. session + episodic summary.

Misura:

1. quality;
2. token growth;
3. latency.

### Experiment 4 - Judge Reliability

Obiettivo:

provare la stessa eval con:

1. un judge forte;
2. un judge piu economico;
3. rubriche diverse.

Misura:

1. stabilita;
2. coerenza;
3. costo.

### Experiment 5 - Dashboard MVP

Obiettivo:

costruire una vista locale che mostri:

1. run;
2. costi;
3. scores;
4. latency;
5. escalation.

## Weekly Cadence

### Week 1

1. reference scenario;
2. zero-key runtime;
3. primo notebook companion.

### Week 2

1. costi;
2. routing;
3. caching;
4. homelab experiment 1 e 2.

### Week 3

1. memory;
2. evals;
3. judge reliability;
4. homelab experiment 3 e 4.

### Week 4

1. dashboard;
2. deploy story;
3. dry run;
4. homelab experiment 5.
