# Modulo 5 - Research Sources For Slides And Design

Data: 2026-04-23

## Uso

Questa lista non serve a gonfiare la bibliografia. Serve a sostenere le scelte del modulo 5 con fonti primarie o ufficiali, cosi le slide non sembrano opinioni isolate.

## Core Sources

### Pydantic AI

Perche serve:

1. giustifica il layer agente;
2. supporta il path `TestModel` e `Agent.override`;
3. aiuta a spiegare perche il quickstart deve funzionare senza provider reali.

Fonti:

1. Pydantic AI Agents: https://ai.pydantic.dev/agent/
2. Pydantic AI Testing: https://ai.pydantic.dev/testing/
3. Pydantic AI Dependencies: https://ai.pydantic.dev/dependencies/
4. Pydantic AI Models overview: https://ai.pydantic.dev/models/

### Langfuse

Perche serve:

1. collega osservabilita, score, tracing e dataset;
2. supporta la parte `dashboard prototype`;
3. rende concreta la distinzione tra tracing e evaluation.

Fonti:

1. Langfuse Overview: https://langfuse.com/docs
2. Langfuse Evaluation Overview: https://langfuse.com/docs/scores
3. Langfuse Scores Overview: https://langfuse.com/docs/evaluation/scores/overview
4. Langfuse Evaluation Methods overview: https://langfuse.com/docs/evaluation/evaluation-methods/overview

### OpenAI Evals

Perche serve:

1. ti aiuta a spiegare evals come disciplina;
2. ti da linguaggio pratico per dataset, graders e regression thinking.

Fonti:

1. OpenAI Evaluation best practices: https://platform.openai.com/docs/guides/evaluation-best-practices
2. OpenAI Working with evals: https://platform.openai.com/docs/guides/evals?api-mode=responses
3. OpenAI Evals API reference: https://platform.openai.com/docs/api-reference/evals/list

### Anthropic Prompt Caching

Perche serve:

1. e una fonte primaria forte per la sezione caching;
2. aiuta a spiegare quando il contesto statico va organizzato per reuse.

Fonte:

1. Anthropic Prompt caching: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching

### Ollama

Perche serve:

1. sostiene il path locale per demo e fallback;
2. aiuta a motivare un quickstart senza chiavi reali come secondo step dopo il mock.

Fonte:

1. Ollama docs: https://docs.ollama.com/

## Collaboration And Notebook Sources

### Google Colab

Perche serve:

1. supporta la scelta di notebook condivisibile;
2. chiarisce cosa viene condiviso e cosa no.

Fonte:

1. Colab FAQ: https://research.google.com/colaboratory/intl/en-GB/faq.html

### JupyterLab Real-Time Collaboration

Perche serve:

1. sostiene il path di collaborazione realtime piu controllato;
2. chiarisce i limiti dell'editing collaborativo.

Fonti:

1. JupyterLab RTC stable: https://jupyterlab.readthedocs.io/en/stable/user/rtc.html
2. JupyterLab RTC 3.x note: https://jupyterlab.readthedocs.io/en/3.1.x/user/rtc.html

### GitHub Codespaces

Perche serve:

1. e utile se vuoi raccontare un ambiente replicabile cloud-based;
2. puo connettersi bene a notebook e GitHub repo senza installazioni locali.

Fonti:

1. Codespaces features: https://docs.github.com/en/codespaces/about-codespaces/codespaces-features
2. What are Codespaces: https://docs.github.com/en/codespaces/about-codespaces/what-are-codespaces?azure-portal=true
3. Codespaces for machine learning and JupyterLab: https://docs.github.com/codespaces/developing-in-a-codespace/getting-started-with-github-codespaces-for-machine-learning

## Search Topics To Turn Into Slide Material

1. `LLM evaluation best practices regression datasets graders`
2. `prompt caching static context reuse cost reduction`
3. `agent observability trace score latency cost`
4. `local model fallback ollama workshop teaching`
5. `Jupyter real-time collaboration teaching live coding`
6. `GitHub Codespaces JupyterLab reproducible workshop`

## Slide Claims These Sources Can Support

1. Perche i test non bastano e servono evals.
2. Perche caching e context shaping sono discipline di costo e latenza, non solo di prompt.
3. Perche observability e evaluation sono correlate ma non identiche.
4. Perche un notebook condiviso aiuta la didattica ma non deve diventare l'architettura del sistema.
5. Perche un ambiente riproducibile vale piu di una demo spettacolare ma fragile.

## Regola Di Curazione

Per ogni slide importante del modulo 5, tieni al massimo:

1. una fonte primaria tecnica;
2. un esempio del repo;
3. una visualizzazione o diagramma.

Se servono piu di tre livelli per spiegare una slide, quella slide sta coprendo troppo.
