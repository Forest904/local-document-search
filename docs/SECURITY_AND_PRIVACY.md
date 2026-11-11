# Privacy, dati e distribuzione

Politica corrente; [stato e collaudo della release](README.md#stato-implementato).

## Dati locali

Nessun upload, telemetria, account o servizio di rete. I reader non visitano URL nei documenti. Testo estratto e indici possono restare dopo la scomparsa dei sorgenti: informare l'utente prima dell'indicizzazione. Storage per account in `%LOCALAPPDATA%/LocalDocumentSearch/Data`, separato dai dati precedenti e dalla directory indicizzata; protezioni standard dell’account Windows, senza cifratura applicativa aggiuntiva. Per backend/test non Windows iniettare uno storage esplicito esterno a sorgenti e repository; trattare i documenti come input non fidati e verificare file corrotti/risorse insufficienti. La decisione sul percorso e sul layout fisico è [V2-D04](adr/README.md#decisioni-aperte).

Log condivisibili senza testo estratto, query personali o percorsi assoluti; report dei job con categorie e percorsi relativi. Fixture e corpus dei test sintetici; dati personali, snapshot, database e risultati locali fuori da Git. Niente hash dei sorgenti per il diff o controllo durante la ricerca.

Pulizia esplicita: rimuove dati applicativi correnti secondo lo stato del job e protegge le letture attive; mai sorgenti o dati delle installazioni precedenti. Fallimento osservabile e riprovabile. Disinstallazione conserva per default indici e preferenze; il wizard offre scelta esplicita per eliminarli. Nessuna promessa di cancellazione forense.

## Distribuzione e diritti

V2-13 modifica il sorgente TXT/MD soltanto dopo il comando esplicito Salva. La scrittura usa un temporaneo nella stessa cartella, verifica identità e metadati e sostituisce il file; non invia testo alla rete. Anteprima Markdown: HTML incorporato non eseguibile, immagini rese come testo alternativo, link senza navigazione automatica. La bozza può essere copiata negli appunti su richiesta dell'utente. Il confronto dei metadati non rileva modifiche esterne che li preservano e non elimina la breve gara prima della sostituzione.

Il viewer V2-11 usa Qt PDF, che incorpora PDFium. Payload, avvisi e archivi sorgente pertinenti richiedono un audit aggiornato prima della distribuzione; le evidenze della release 0.2.0 non coprono il nuovo componente.

«Trova nel PDF» analizza localmente il file aperto tramite Qt PDF, senza inviare query o testo alla rete. Il componente QML Qt PDF adattato nel frontend conserva l'intestazione LGPL/GPL originale ed è elencato negli avvisi del pacchetto; l'archivio del sorgente originale accompagna il payload.

Installer Windows 11 x64 offline, per utente e senza elevazione; include Python, Qt, plugin e ogni dipendenza runtime necessaria. Aggiornamento tramite nuovo installer completo, nessun updater che chiama un servizio. Collaudo su account standard e sistema pulito, senza Python o tool di sviluppo. La prima release pubblica può essere non firmata; registrare gli avvisi realmente osservati e non presentarla come firmata.

L'implementazione V2-07 usa Inno Setup 6.7.3. La disinstallazione conserva i dati per default anche in modalità silenziosa. La cancellazione esplicita controlla il lock e rifiuta reparse point; il fallimento lascia un errore riprovabile. [Evidenze e limiti](V2_07_INSTALLER.md).

**Termini del titolare:** Luca Foresti, Roma, Italia, lucapalocco@gmail.com. L'uso personale, di studio e interno è gratuito anche per imprese e professionisti; la vendita, l'integrazione in prodotti distribuiti e l'offerta delle funzioni come servizio a terzi richiedono autorizzazione scritta. La condivisione gratuita del pacchetto originale integro è consentita. Il testo italiano in `scripts/package/TERMS-IT.txt` è quello di riferimento; quello inglese è informativo. Il repository GitHub pubblico consente visualizzazione e fork nei limiti delle condizioni della piattaforma; non concede automaticamente una licenza open source di riuso del codice. [Spiegazione GitHub](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).

Il percorso Qt usa componenti compatibili con LGPL. La build verifica ogni file del payload, include gli archivi sorgente Qt e blocca moduli solo GPL o attribuzioni mancanti. Una DLL QtCore ricostruita da QtBase 6.12.0 ha funzionato in una copia dell'installazione per una ricerca sintetica. [Evidenze](V2_07_INSTALLER.md), [obblighi Qt](https://www.qt.io/development/open-source-lgpl-obligations), [approvazione V2-D09](adr/README.md#decisioni-aperte). I termini del progetto non limitano i diritti concessi dalle licenze delle dipendenze.
