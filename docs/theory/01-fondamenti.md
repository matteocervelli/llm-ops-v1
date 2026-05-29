# Fondamenti — Tokenizzazione, Embedding, Attention

> Le tre operazioni che trasformano testo in predizione.

Capire come un LLM elabora il testo non richiede di padroneggiare la matematica del training. Richiede di capire tre operazioni che si susseguono ad ogni forward pass: come il testo diventa numeri (tokenizzazione), come quei numeri acquistano significato (embedding), e come i token si relazionano l'uno all'altro (attention).

## Tokenizzazione — da testo a interi

Un LLM non vede testo. Vede sequenze di interi. La tokenizzazione è il passaggio che trasforma la stringa in input in una lista di indici numerici.

Un token non è una parola e non è un carattere: è un'unità intermedia. Algoritmi come BPE (Byte-Pair Encoding) costruiscono un vocabolario di 30.000–130.000 frammenti guardando quali sequenze di caratteri ricorrono spesso nel corpus di training. Le parole comuni diventano un token singolo; quelle rare si spezzano in frammenti. Il risultato concreto: ogni token è un indice in una tabella.

Regola spannometrica: ~1 token ogni 4 caratteri in italiano e inglese. Questo è il motivo per cui le API si pagano a token e i context window si misurano in token.

La dimensione del vocabolario e le regole di segmentazione sono fisse a seguito del training — non cambiano durante l'inferenza. La stessa parola produce sempre gli stessi token sullo stesso modello.

## Embedding — da indice a vettore

Il problema dell'indice: il numero 4827 non ha alcun significato numerico. Non è "più vicino" a 4828 di quanto lo sia a 12. Serve una rappresentazione in cui la posizione nello spazio catturi il significato.

La soluzione è la tabella di embedding: una matrice di dimensione `[vocabolario × hidden_dim]`. `hidden_dim` (anche detta `d_model`) è la larghezza interna del modello — quante coordinate usa per rappresentare un concetto. Per un modello da 7B di parametri è tipicamente 4096.

Ogni riga di questa tabella è un vettore di 4096 numeri float che rappresenta un token. Tokenizzazione → indice → lookup nella tabella → vettore di 4096 numeri. Quel vettore è il token come lo capisce il modello.

Il punto non banale: questi numeri non sono fissati a mano. Emergono dal training. Il training dispone i vettori nello spazio in modo che la posizione codifichi il significato: token usati in contesti simili finiscono vicini, e le direzioni nello spazio acquistano semantica stabile. La famosa aritmetica "re − uomo + donna ≈ regina" è la conseguenza di questa proprietà geometrica: esiste una direzione nello spazio che codifica "genere femminile", e il training l'ha costruita senza che nessuno la programmasse esplicitamente. Il significato è distribuito su molte dimensioni insieme — non c'è una "colonna del genere" — ma le relazioni geometriche (vicinanza, direzione) sono interpretabili e robuste.

Un prompt da N token diventa una matrice `[N × 4096]`: ogni riga un token, ogni colonna una dimensione semantica. Questa matrice è l'input che attraversa tutti i layer del Transformer.

## Pesi e forward pass

I pesi sono i numeri imparati dal modello durante il training. "Modello da 7B di parametri" significa 7 × 10⁹ numeri. Sono la conoscenza del modello: cambiarli significa cambiare cosa il modello sa.

Il forward pass è il calcolo che trasforma la matrice di input in una predizione. L'operazione elementare, ripetuta ovunque, è la moltiplicazione matrice × matrice (matmul): prendi la matrice degli input, moltiplicala per una matrice di pesi, ottieni una nuova matrice. Questa è il 90% del lavoro di un LLM. Il FLOP (Floating Point Operation) è l'unità di misura di questo lavoro: una moltiplicazione o una somma tra numeri in virgola mobile. La GPU è l'hardware giusto per questo compito perché le matmul sono massivamente parallelizzabili — ogni elemento del risultato è indipendente dagli altri — e la GPU ha migliaia di core progettati per questo.

Regola pratica: un forward pass su un token richiede circa 2 × (numero di parametri) FLOP. Su un modello da 7B: ~14 miliardi di operazioni per token.

## Attention — come i token si relazionano

La self-attention è il meccanismo che permette a ogni token di "guardare" tutti gli altri token della sequenza e decidere quali sono rilevanti per sé.

Per ogni token, il modello calcola tre vettori moltiplicando l'embedding per tre matrici di pesi distinte apprese durante il training:

- **Query (Q)** — cosa sto cercando. La domanda che questo token pone agli altri.
- **Key (K)** — cosa sono / cosa offro. L'etichetta con cui ogni token si fa trovare.
- **Value (V)** — l'informazione che porto. Il contenuto che verrà passato avanti se questo token risulta rilevante.

Il punteggio di attention tra due token è il prodotto scalare tra la Query di uno e la Key dell'altro. Il prodotto scalare misura quanto due vettori puntano nella stessa direzione: alto se allineati, basso se ortogonali. Il training ha imparato le matrici W_Q, W_K, W_V in modo che vettori Q e K si allineino quando i due token sono semanticamente rilevanti l'uno per l'altro.

I punteggi grezzi vengono trasformati via softmax in pesi positivi che sommano a 1 — una distribuzione di probabilità. Il token riceve poi una media pesata dei Value usando quei pesi: assorbe informazione dai token che gli importano, in proporzione a quanto gli importano.

Un LLM è uno stack di decine di questi blocchi (layer). Un modello da 7B ne ha tipicamente 32. Ogni layer fa attention + una rete feed-forward, e passa il risultato al layer successivo. Il vettore di output dell'ultimo layer per l'ultimo token viene usato per predire il token successivo.

## Perché la self-attention ha sostituito le RNN

Prima dei Transformer si usavano reti ricorrenti (RNN/LSTM): leggevano la frase un token alla volta, mantenendo uno "stato nascosto" che riassumeva tutto il passato in un singolo vettore. Due problemi strutturali: il calcolo era intrinsecamente sequenziale (impossibile parallelizzare sul training), e l'informazione lontana sbiadiva attraverso molti passi. La self-attention rompe entrambe le cose: ogni token guarda direttamente ogni altro con un prodotto scalare, la distanza è irrilevante, e tutti i confronti si fanno in parallelo come una matmul. È questo parallelismo che ha reso possibile addestrare modelli alla scala attuale.

## Addestramento in una riga

Il training è un ciclo: predici il token successivo → misura l'errore (cross-entropy loss) → propaga l'errore all'indietro attraverso tutti i layer (backpropagation) → aggiusta ogni peso di un piccolo passo nella direzione che riduce l'errore (gradient descent). Ripetuto su trilioni di token, produce i miliardi di pesi che costituiscono un LLM moderno.

## Per approfondire

- [`02-prefill-decode-kvcache.md`](02-prefill-decode-kvcache.md) — il doc operativo: come questi meccanismi determinano costo e latenza
- [Karpathy — "What is a GPT"](../resources/reading_list.md) — video introduttivo consigliato
