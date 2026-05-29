# Internals LLM — Materiali di Riferimento

> Questo non è materiale presentato live. È il substrato teorico che rende solide le scelte operative del corso.

I blocchi 5 e 6 della sessione parlano di costi, routing, caching e memoria. Ogni decisione pratica lì — perché output costa di più, perché un token cambiato invalida la cache, perché la quantizzazione accelera l'inferenza locale — ha una spiegazione meccanica precisa. Questi documenti la forniscono.

Puoi leggerli in qualsiasi ordine, ma il filo logico naturale è bottom-up:

| Doc                                                                  | Contenuto                                                                                                                                            |
| -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`01-fondamenti.md`](01-fondamenti.md)                               | Tokenizzazione, embedding, pesi, attention Q/K/V. Le fondamenta.                                                                                     |
| [`02-prefill-decode-kvcache.md`](02-prefill-decode-kvcache.md)       | Prefill vs decode, compute vs memory-bound, TTFT/TPOT, matematica KV cache, GQA. Il doc più operativo — collega direttamente alla Parte Economica.   |
| [`03-quantization-moe-hardware.md`](03-quantization-moe-hardware.md) | Quantizzazione fp16→int4, denso vs MoE, hardware (VRAM/HBM/Metal/offloading). Perché i modelli locali si comportano così.                            |
| [`04-prompt-caching-internals.md`](04-prompt-caching-internals.md)   | Meccanica del caching provider: hashing su token ID, dove vive la cache, invalidazione su edit, Claude Code cache breakpoints, steering multi-turno. |

## Il filo che lega tutto

Token → embedding (matrice) → forward pass = pile di matmul che usano i pesi → l'attention costruisce Q/K/V per relazionare i token → il prefill processa tutto il prompt in parallelo (compute-bound, limitato dai FLOPS) → il decode genera un token alla volta riusando la KV cache (memory-bound, limitato dalla banda VRAM) → il caching salta il prefill del prefix statico riusando la KV cache già calcolata → la quantizzazione attacca il collo di bottiglia del decode riducendo i byte da leggere → l'hardware (GPU/VRAM/HBM vs memoria unificata) determina se il modello ci sta e quanti token/s ottieni.

Ogni scelta economica del corso è una conseguenza di questo filo.

## Perche questa serie esiste

Il content brief del corso aveva già anticipato una directory `docs/theory/` come materiale di background. Questo è quel materiale, costruito a partire da sessioni di studio approfondito sulle architetture Transformer e sui pattern di inferenza LLM.
