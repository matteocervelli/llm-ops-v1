# Serverless vs VPS vs cluster

## Quando usare Fly.io

Usalo quando vuoi fare demo veloci, deploy frequenti e pagare poco all'inizio. È adatto per agenti stateless, job schedulati piccoli e servizi HTTP con carico intermittente.

## Quando usare VPS + systemd

Usalo quando vuoi controllo completo, costi prevedibili e poca complessità operativa. È la scelta più sensata per un primo agente in produzione, soprattutto se hai code semplici, cron job e pochi servizi di supporto.

## Quando ha senso il cluster

Kubernetes o ECS iniziano ad avere senso quando hai più servizi, più ambienti, rollout frequenti, requisiti di alta disponibilità e qualcuno che se ne occupi davvero. Per il corso, resta fuori scope.
