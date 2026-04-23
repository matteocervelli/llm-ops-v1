# Modulo 5 Brief - LLMOps e Operativita

Data: 2026-04-23

## Source Of Truth

Questo brief sostituisce le assunzioni incomplete fatte prima della trascrizione del messaggio WhatsApp.

Fonti usate:

1. Slide del modulo 5: [Image #1] gia allegata in chat.
2. Audio WhatsApp: [WhatsApp Audio 2026-04-23 at 13.54.21.opus](/data/dev/demo/llm-ops-v1/tmp/WhatsApp%20Audio%202026-04-23%20at%2013.54.21.opus)
3. Trascrizione verificata via Fabrica il 2026-04-23.

Sintesi del recap audio:

1. Lezione online il 29 maggio 2026.
2. Durata: 3 ore.
3. Target: sviluppatori e ingegneri digitali orientati alla costruzione di agenti.
4. Tema reale: `LLM Ops e scalabilita del servizio`.
5. Argomenti non negoziabili: costi, prompt, contesto e memoria, caching, scalabilita sotto carico, evals, `LLM-as-a-Judge`, monitoraggio continuo, prototipo di dashboard.

## Obiettivo Reale Del Modulo

Il quinto modulo non deve insegnare "tutto quello che esiste in LLMOps". Deve chiudere il cerchio del corso mostrando come un agente passi da artefatto dimostrativo a servizio operabile, misurabile e governabile.

La domanda corretta del modulo e:

`come tengo un agente sotto controllo nel tempo, al crescere del carico e dei costi, senza perderne qualita e sostenibilita operativa?`

## Vincoli Didattici Fissi

1. La sessione e breve: 3 ore.
2. E online, quindi il ritmo e piu importante della completezza.
3. Il pubblico e tecnico, ma non deve essere trattato come team platform gia senior.
4. Il modulo deve restare coerente con il progetto individuale finale.
5. Il materiale deve essere condivisibile senza spiegazioni aggiuntive o retromarce architetturali.

## Cosa Deve Uscire Dalla Lezione

Gli studenti devono portarsi a casa queste competenze operative:

1. Stimare e leggere i costi di un agente per request, scenario e volume.
2. Capire quando usare prompt engineering, context shaping, memory shaping e caching.
3. Separare prestazioni, qualita e costo invece di trattarli come un unico numero.
4. Costruire una pipeline di evals minima ma ripetibile.
5. Capire il ruolo pratico di `LLM-as-a-Judge` nel monitoraggio continuo.
6. Vedere un prototipo di dashboard o score view che trasformi output in segnali operativi.
7. Capire cosa serve per mettere un agente dietro un runtime eseguibile e non solo in notebook.
8. Sapere cosa documentare in un runbook essenziale.

## Implicazioni Per Il Repo

Il repo non deve essere solo "pubblico e credibile". Deve anche essere insegnabile in tempo reale.

Quindi il repo deve supportare quattro cose contemporaneamente:

1. Un percorso `clone -> run -> capire`.
2. Una demo live con progressive reveal.
3. Un progetto individuale che possa essere forkato e adattato.
4. Una presentazione che faccia riferimento a file reali, non solo a slide.

## Formato Consigliato Della Lezione

### Recommended Delivery Stack

1. `GitHub repository` come source of truth.
2. `Notebook` come companion didattico, non come sistema di riferimento.
3. `CLI` come prova di maturita operativa.
4. `Dashboard prototype` come chiusura visiva della parte evals/monitoring.

### Scelta Pragmatica

Il compromesso migliore non e `repo oppure notebook`.

Il compromesso migliore e:

1. repo canonico con struttura pulita;
2. uno o due notebook companion per la live;
3. notebook che richiamano codice del repo, non logica duplicata;
4. alcuni comandi CLI mostrati dentro il notebook o in terminale, ma sempre riconducibili al repo.

### Real-Time Collaboration

Per la componente collaborativa, la raccomandazione non e trasformare l'intero corso in notebook-only.

La raccomandazione e:

1. tenere il repository come base;
2. usare un notebook condivisibile per walkthrough e piccoli esperimenti;
3. usare Colab o Jupyter solo come superficie didattica;
4. evitare che la logica del sistema viva solo nelle celle.

## Cosa Deve Essere Visibile Live

1. Un agente o servizio di riferimento piccolo ma reale.
2. Calcolo costi e tradeoff tra provider o modalita di esecuzione.
3. Un esempio di ottimizzazione del contesto o della memoria.
4. Un esempio concreto di caching.
5. Una mini suite di evals.
6. Una forma minima di monitoraggio con score o dashboard.
7. Un runtime eseguibile da terminale.
8. Un repo che mostra chiaramente dove stanno codice, test, materiale del corso e infrastruttura.

## Cosa Non Va Messo Nel Critical Path

1. Integrazioni esterne fragili non necessarie alla tesi della lezione.
2. Provider reali obbligatori per il quickstart.
3. Headless agents come prerequisito per capire il modulo.
4. Serverless o deploy secondari nel percorso principale.
5. Architetture distribuite inutili per un corso di 3 ore.

## Deliverable Da Sostenere

La slide fissa tre output per il progetto individuale:

1. progetto di un agente;
2. repository GitHub con il codice;
3. mini report e presentazione finale dei risultati.

Il modulo 5 deve quindi lasciare agli studenti template e criteri minimi per tutti e tre:

1. cosa deve esserci nel repo;
2. quali metriche o evidenze mostrare;
3. come raccontare qualita, costi, limiti e piano operativo.

## Decisioni Gia Raccomandate

1. Tenere `repo-first`, ma con notebook companion ufficiale.
2. Fare del `reference agent` l'unico caso guida.
3. Usare `mock/test model` nel quickstart e provider reali solo come estensione.
4. Tenere `Langfuse` opzionale per il primo path, ma presente nel design del modulo.
5. Fare della dashboard un prototipo credibile, non una piattaforma completa.
6. Usare `VPS + systemd` come storia deploy primaria; `Compose` per dev/demo.

## Conseguenza Sulla Documentazione

Tutti i documenti di design e planning del repo devono ora essere valutati contro questa checklist:

1. aiuta a insegnare il modulo 5 reale?
2. aiuta a far partire un progetto individuale?
3. evita scope creep inutile?
4. e allineato a una live online di 3 ore?

Se la risposta e no, va tagliato, spostato o declassato a estensione.
