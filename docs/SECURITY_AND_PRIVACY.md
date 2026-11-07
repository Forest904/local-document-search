# Privacy, dati e distribuzione v2

**Politica approvata, implementazione futura.** [Comportamento v1](archive/v1/SECURITY_AND_PRIVACY.md), [baseline attuale](BASELINE.md).

## Dati locali

Nessun upload, telemetria, account o servizio di rete. I reader non visitano URL nei documenti. Testo estratto e indici possono restare dopo la scomparsa dei sorgenti: informare l'utente prima dell'indicizzazione. Storage v2 per account separato dalla radice v1 e dalla directory indicizzata; protezioni standard dell'account Windows. La decisione sul percorso e sul layout fisico è [V2-D04](OPEN_DECISIONS.md).

Log condivisibili senza testo estratto, query personali o percorsi assoluti; report dei job con categorie e percorsi relativi. Fixture e corpus dei test sintetici; dati personali, snapshot, database e risultati locali fuori da Git. Niente hash dei sorgenti per il diff o controllo durante la ricerca.

Pulizia esplicita: rimuove dati applicativi v2 secondo lo stato del job e protegge le letture attive; mai sorgenti o storage v1. Fallimento osservabile e riprovabile. Disinstallazione conserva per default indici e preferenze v2; il wizard offre scelta esplicita per eliminarli. Nessuna promessa di cancellazione forense.

## Distribuzione e diritti

Installer Windows 11 x64 offline, per utente e senza elevazione; include Python, Qt, plugin e ogni dipendenza runtime necessaria. Aggiornamento tramite nuovo installer completo, nessun updater che chiama un servizio. Collaudo su account standard e sistema pulito, senza Python o tool di sviluppo. La prima release pubblica può essere non firmata; registrare gli avvisi realmente osservati e non presentarla come firmata.

**Intenzione del titolare:** diritti riservati sul codice del progetto; uso gratuito personale e di studio; uso professionale soggetto ad autorizzazione. Prima della pubblicazione approvare termini completi in [V2-D08](OPEN_DECISIONS.md); questa frase non è una licenza d'uso completa. Il repository GitHub pubblico consente visualizzazione e fork nei limiti delle condizioni della piattaforma; non concede automaticamente una licenza open source di riuso del codice. [Spiegazione GitHub](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).

Il percorso scelto per Qt è usare componenti compatibili con LGPL. Prima del rilascio, verificare il payload effettivo, licenze per modulo, avvisi/testi e possibilità di sostituire le librerie secondo gli obblighi applicabili; includere solo avvisi non basta. [Obblighi Qt](https://www.qt.io/development/open-source-lgpl-obligations), [gate V2-D09](OPEN_DECISIONS.md). Ogni altra dipendenza redistribuita entra nell'inventario. I termini del progetto non limitano i diritti concessi dalle licenze delle dipendenze.
