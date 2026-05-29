# Quantizzazione, MoE e Hardware

> Perché i modelli locali si comportano così, e come le scelte architetturali cambiano il profilo hardware.

Questo doc risponde a tre domande pratiche: cosa succede alla qualità quando quantizzo un modello, perché un MoE da 284B costa come un denso da 13B in inferenza, e perché il profilo hardware che conta non è il numero di core ma la banda di memoria.

## Quantizzazione — meno bit, stesso modello

I pesi di un modello vengono salvati durante il training in fp32 o fp16. La quantizzazione riduce la precisione: rappresenta gli stessi pesi con meno bit. Il risultato più comune è int8 (1 byte/peso) o int4 (4 bit/peso).

### Cosa succede matematicamente in int4

Un peso in fp16 ha ~3-4 cifre significative e range ±65504. Int4 ha 4 bit = 16 valori possibili. Non è possibile rappresentare un float arbitrario con 16 livelli senza perdita significativa — quindi la quantizzazione non arrotonda semplicemente ogni peso. Usa la **quantizzazione affine a blocchi**:

1. Prendi un gruppo di pesi (es. 32–64 contigui). Trova il loro minimo e massimo.
2. Calcola la scala: `scala = (max − min) / 15` (15 livelli, da 0 a 15).
3. Ogni peso viene mappato sull'intero a 4 bit più vicino: `q = round((peso − min) / scala)`.
4. Salva gli interi `q` (4 bit compatti) + scala e min del blocco in fp16.

A runtime si ricostruisce il valore approssimato: `peso ≈ scala × q + min`. Un "modello int4" occupa ~4,5 bit/peso netti (i 4 bit + l'overhead delle scale per blocco).

Il vero nemico sono gli **outlier**: un singolo peso molto grande dilata il range del blocco e rende grossolana la rappresentazione di tutti gli altri. Per questo le tecniche avanzate (GPTQ, AWQ) aggiustano i pesi rimanenti per compensare l'errore, o tengono in alta precisione i canali più importanti.

### Cosa si guadagna e cosa si perde

Il guadagno principale: la memoria. Un modello da 7B in fp16 = ~14 GB. In int4 = ~3,5–4 GB. Il modello che prima non entrava in VRAM ora ci sta, e il decode accelera perché si leggono meno byte dalla memoria a ogni step.

Il degrade della qualità è quasi trascurabile per int8, accettabile per int4 con tecniche buone (GPTQ/AWQ/k-quants GGUF), e significativo sotto i 4 bit. Per inferenza locale int8 è praticamente gratuito; int4 è il punto di equilibrio standard.

Il guadagno è sproporzionato sul decode perché il decode è memory-bound: la velocità di generazione è proporzionale a `banda_memoria / byte_per_peso`. Dimezzare i byte ≈ raddoppiare i token/s. Sul prefill l'effetto è minore perché lì sei compute-bound.

### Quantizzazione mista

I modelli recenti usano quantizzazione differenziata: non tutta la stessa precisione. DeepSeek V4 Flash usa FP4 per gli esperti MoE (la massa dei pesi, dove l'errore si media attraverso molte attivazioni) e FP8 per attention, router e normalizzazioni (le parti sensibili dove la precisione conta). È quantizzazione chirurgica, non un colpo di accetta uniforme.

## Denso vs MoE — attivi vs totali

Un **modello denso** attiva tutti i parametri per ogni token. Un 30B denso richiede ~60 GFLOPs/token e legge ~60 GB dalla memoria a ogni step del decode.

Un **MoE** (Mixture of Experts) divide i layer feed-forward in molti "esperti" (sottoreti separate) e usa un piccolo router per decidere, token per token, quali attivare — tipicamente 2–8 esperti su decine o centinaia disponibili. DeepSeek V4 Flash ha 284B parametri totali ma solo 13B attivi per forward pass.

Il risultato: paghi il compute di un 13B (veloce, bassa domanda di banda per token) ma hai la capacità di un 284B. I parametri totali enormi immagazzinano conoscenza; i parametri attivi pochi rendono l'inferenza economica. È questo che spiega perché modelli MoE come DeepSeek appaiono nel pricing di OpenRouter a $0,14/M token nonostante le dimensioni nominali.

### Il caveat hardware dei MoE

Tutti i 284B devono stare in memoria anche se ne usi 13B per token. Il router sceglie esperti diversi a ogni token — non puoi sapere in anticipo quali serviranno. Se il modello non entra in VRAM, gli esperti che non ci stanno devono essere caricati dalla RAM di sistema via PCIe a ogni richiesta. Il bus PCIe (~30–60 GB/s) è 15–30× più lento della VRAM (~1 TB/s). Su un MoE grande, l'offloading è il collo di bottiglia principale.

Conseguenza pratica: per un MoE da 160 GB, una macchina con memoria unificata da 128 GB (es. Mac Studio M3 Ultra) può essere preferibile a una workstation con 48 GB di VRAM + 256 GB di RAM. Nel primo caso tutti i pesi sono accessibili alla GPU senza attraversare il bus PCIe; nel secondo la maggior parte degli esperti vive in RAM e viene trasferita su richiesta.

## Hardware — dove conta davvero la banda

La VRAM è la memoria della GPU. I pesi e la KV cache devono stare qui durante l'inferenza. La capacità (GB) determina se il modello ci sta; la banda (GB/s) determina quanto velocemente si generano token.

### Perché la banda conta più dei FLOPS in decode

In decode, ogni step processa un solo token. Le GPU moderne hanno enormi capacità di calcolo (centinaia di TFLOPS) ma quel calcolo è inutile se aspetta la memoria. La velocità di generazione è approssimabile come:

```
token/s ≈ banda_VRAM_GB_s / dimensione_modello_GB
```

Con 14 GB di pesi e ~1 TB/s di banda teorica: ~70 token/s teorico. Raddoppiare la banda di memoria raddoppia i token/s; raddoppiare i FLOPS non cambia nulla finché sei memory-bound.

Le GPU datacenter usano **HBM** (High Bandwidth Memory) — un tipo di VRAM con banda molto più alta delle GPU consumer. Un A100 ha ~2 TB/s; una H100 SXM ~3,35 TB/s. Le GPU consumer come la RTX serie 40 stanno su ~1 TB/s.

### Metal e memoria unificata (Apple Silicon)

Metal è l'API con cui i framework parlano alla GPU nei chip Apple. La particolarità dei Mac con Apple Silicon è la **memoria unificata**: CPU e GPU condividono lo stesso pool di RAM. Un M3 Ultra con 96 GB ha tutti i 96 GB accessibili alla GPU senza che i dati passino da un bus separato.

Il vantaggio: puoi caricare modelli enormi che non entrerebbero nella VRAM di una GPU discreta (dove sei limitato a 24–80 GB). Lo svantaggio: la banda della memoria unificata (~800 GB/s sull'M3 Ultra) è inferiore a una GPU HBM da datacenter, ma è molto meglio del path PCIe-offload di una workstation con poca VRAM.

### Offloading VRAM → RAM — il costo nascosto

Quando un modello non entra in VRAM, si splittano i layer: alcuni in VRAM, il resto in RAM di sistema. Il forward pass li attraversa in ordine: arrivato a un layer in RAM, il sistema trasferisce quei pesi via PCIe su VRAM (o li calcola su CPU). In decode questo avviene per ogni singolo token generato. Anche un solo layer fuori dalla VRAM può dimezzare i token/s.

## Per approfondire

- [`02-prefill-decode-kvcache.md`](02-prefill-decode-kvcache.md) — prefill/decode e KV cache
- [`../01-cost-and-routing.md`](../01-cost-and-routing.md) — costo e routing: dove MoE appare come voce di prezzo
