# Privacy, dati e distribuzione v2

**Politica approvata; installer V2-07 verificato localmente.** [Comportamento v1](archive/v1/SECURITY_AND_PRIVACY.md), [baseline attuale](BASELINE.md).

## Dati locali

Nessun upload, telemetria, account o servizio di rete. I reader non visitano URL nei documenti. Testo estratto e indici possono restare dopo la scomparsa dei sorgenti: informare l'utente prima dell'indicizzazione. Storage v2 per account separato dalla radice v1 e dalla directory indicizzata; protezioni standard dell'account Windows. La decisione sul percorso e sul layout fisico è [V2-D04](OPEN_DECISIONS.md).

Log condivisibili senza testo estratto, query personali o percorsi assoluti; report dei job con categorie e percorsi relativi. Fixture e corpus dei test sintetici; dati personali, snapshot, database e risultati locali fuori da Git. Niente hash dei sorgenti per il diff o controllo durante la ricerca.

Pulizia esplicita: rimuove dati applicativi v2 secondo lo stato del job e protegge le letture attive; mai sorgenti o storage v1. Fallimento osservabile e riprovabile. Disinstallazione conserva per default indici e preferenze v2; il wizard offre scelta esplicita per eliminarli. Nessuna promessa di cancellazione forense.

## Distribuzione e diritti

Installer Windows 11 x64 offline, per utente e senza elevazione; include Python, Qt, plugin e ogni dipendenza runtime necessaria. Aggiornamento tramite nuovo installer completo, nessun updater che chiama un servizio. Collaudo su account standard e sistema pulito, senza Python o tool di sviluppo. La prima release pubblica può essere non firmata; registrare gli avvisi realmente osservati e non presentarla come firmata.

L'implementazione V2-07 usa Inno Setup 6.7.3. La disinstallazione conserva i dati v2 per default anche in modalità silenziosa. La cancellazione esplicita controlla il lock e rifiuta reparse point; il fallimento lascia un errore riprovabile. [Evidenze e limiti](V2_07_INSTALLER.md).

**Termini del titolare:** Luca Foresti, Roma, Italia, lucapalocco@gmail.com. L'uso personale, di studio e interno è gratuito anche per imprese e professionisti; la vendita, l'integrazione in prodotti distribuiti e l'offerta delle funzioni come servizio a terzi richiedono autorizzazione scritta. La condivisione gratuita del pacchetto originale integro è consentita. Il testo italiano in `scripts/package/TERMS-IT.txt` è quello di riferimento; quello inglese è informativo. Il repository GitHub pubblico consente visualizzazione e fork nei limiti delle condizioni della piattaforma; non concede automaticamente una licenza open source di riuso del codice. [Spiegazione GitHub](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).

Il percorso Qt usa componenti compatibili con LGPL. La build verifica ogni file del payload, include gli archivi sorgente Qt e blocca moduli solo GPL o attribuzioni mancanti. Una DLL QtCore ricostruita da QtBase 6.12.0 ha funzionato in una copia dell'installazione per una ricerca sintetica. [Evidenze](V2_07_INSTALLER.md), [obblighi Qt](https://www.qt.io/development/open-source-lgpl-obligations), [approvazione V2-D09](OPEN_DECISIONS.md). I termini del progetto non limitano i diritti concessi dalle licenze delle dipendenze.
