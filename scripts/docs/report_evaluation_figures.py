"""Figure scientifiche del report dai soli aggregati pubblici (nessun corpus privato)."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/homework-3/figures"
BLUE, ORANGE, INK = "#176583", "#b45c24", "#183d50"


def save(fig, name):
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / f"{name}.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def diagram(name, height, boxes, arrows):
    fig, ax = plt.subplots(figsize=(10, height))
    ax.set(xlim=(0, 10), ylim=(-.08, height))
    ax.axis("off")
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.6))
    for x, y, w, h, title, body in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                   facecolor="#f0f5f7", edgecolor="#b8ccd5"))
        ax.text(x + .15, y + h - .20, title, fontsize=12, weight="bold", color=INK, va="top")
        ax.text(x + .15, y + h - .60, body, fontsize=10.5, color=INK, va="top", linespacing=1.35)
    save(fig, name)


def main():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.labelcolor": INK, "text.color": INK})
    diagram("sintetici", 3.3, [
        (.1, 1.7, 3, 1.4, "1. Proprietà", "Seed + ID del documento\nMateria, lingua, struttura\nFamiglia e lunghezza obiettivo"),
        (3.5, 1.7, 3, 1.4, "2. Composizione", "Sezioni e paragrafi variabili\nTermini comuni e rari\nNumeri, ripetizioni, Unicode"),
        (6.9, 1.7, 3, 1.4, "3. Controllo", "TXT + registro di identità\nRigenerazione e integrità\nCasi positivi e negativi"),
        (.1, .1, 9.8, 1.1, "Profili annidati: 100 ⊂ 1.000 ⊂ 10.000 documenti", "Gli ID condivisi producono gli stessi nomi e byte: cresce il corpus, non cambia il testo già presente."),
    ], [((3.16,2.4),(3.44,2.4)), ((6.56,2.4),(6.84,2.4)), ((5,1.64),(5,1.26))])
    diagram("corpus-reale", 3.3, [
        (.1,1.9,3,1.2,"427 candidati", "TXT, Markdown, PDF\nMateriali selezionati"),
        (3.6,1.9,6.3,1.2,"392 TXT ricercabili · zero errori", "346 da PDF + 30 da TXT + 16 da Markdown\nUn sorgente = un documento; nessun OCR"),
        (.1,.1,4.7,1.2,"30 esclusioni di estrazione", "PDF senza testo non-whitespace\ncon il reader e la versione utilizzati"),
        (5.2,.1,4.7,1.2,"5 esclusioni didattiche", "Materiali operativi o di dipendenze\nSeparati dagli errori di lettura"),
    ], [((3.16,2.5),(3.54,2.5)), ((1.5,1.84),(1.5,1.36)), ((3,1.84),(6,1.36))])
    diagram("validazione", 3.3, [
        (.1,1.9,4.6,1.2,"Correttezza lessicale", "TXT + query congelate\nScansione con regole documentate"),
        (5.3,1.9,4.6,1.2,"Rilevanza tematica", "Originali + dieci bisogni informativi\n600 giudizi revisionati e congelati"),
        (.1,.1,4.6,1.2,"Attesi lessicali ↔ risultati", "Insiemi completi sui quattro corpus\nTP, FP, FN e uguaglianza esatta"),
        (5.3,.1,4.6,1.2,"Pertinenti ↔ recuperati", "Indice dei soli 60 documenti giudicati\nPrecision, recall, F1 micro e macro"),
    ], [((2.4,1.84),(2.4,1.36)), ((7.6,1.84),(7.6,1.36))])
    diagram("luma-flusso", 4, [
        (.1,2.65,4.6,1.1,"Console", "TXT, indice volatile, ordine per percorso"),
        (5.3,2.65,4.6,1.1,"Luma desktop", "Formati, persistenza, lettura e modifica"),
        (.1,1.25,9.8,1.05,"Motore condiviso", "Analyzer coerenti · due indici posizionali · query sullo snapshot attivo"),
        (.1,.05,3, .85,"Versione attiva", "Le ricerche continuano"),
        (3.5,.05,3,.85,"Nuovo candidato", "Preparazione + validazione"),
        (6.9,.05,3,.85,"Commit atomico", "Nuova versione completa"),
    ], [((2.4,2.59),(2.4,2.36)), ((7.6,2.59),(7.6,2.36)),
        ((1.5,1.19),(1.5,.96)), ((5,1.19),(5,.96)), ((6.56,.48),(6.84,.48))])

    data = json.loads((ROOT / "experiments/homework3_results.json").read_text(encoding="utf-8"))
    rows = next(r["rows"] for r in data["results"] if r["kind"] == "relevance_report")
    fig, ax = plt.subplots(figsize=(10, 2.25))
    x = np.arange(len(rows))
    for offset, metric, label, color, marker in [(-.11,"precision","Precision",BLUE,"o"),
                                               (.11,"recall","Recall",ORANGE,"s")]:
        values = [r["metrics"][metric] for r in rows]
        valid = [(i,v) for i,v in enumerate(values) if v is not None]
        ax.scatter([i+offset for i,v in valid], [v for i,v in valid], color=color,
                   marker=marker, s=45, label=label, zorder=3)
        for i,v in enumerate(values):
            if v is None:
                ax.annotate("P: N/A", (i, .18), ha="center", fontsize=9, color=BLUE)
    ax.set(xticks=x, xticklabels=[r["id"] for r in rows], ylim=(-.07,1.09), yticks=[0,.25,.5,.75,1])
    ax.grid(axis="y", color="#dce4e8", zorder=0)
    ax.legend(loc="lower left", bbox_to_anchor=(0,1.03), ncol=2, frameon=False)
    fig.tight_layout()
    save(fig,"rilevanza")

    data = json.loads((ROOT / "experiments/homework3_performance_results.json").read_text(encoding="utf-8"))
    fig, axes = plt.subplots(1,3,figsize=(10,7.5),sharex=True,
                             gridspec_kw={"wspace":.28})
    for ax,field,label in zip(axes,["filename","content","both"],["Nome · 10 query","Contenuto · 15 query","Entrambi · 5 query"]):
        queries = [q for q in data["queries"] if q["field"] == field]
        for method,color,offset,marker in [("index",BLUE,-.14,"o"),("scan",ORANGE,.14,"s")]:
            med=np.array([q[method]["median"]*1000 for q in queries])
            lo=np.array([q[method]["min"]*1000 for q in queries])
            hi=np.array([q[method]["max"]*1000 for q in queries])
            ax.errorbar(med,np.arange(len(queries))+offset,xerr=[med-lo,hi-med],fmt=marker,
                        color=color,capsize=3,markersize=4,elinewidth=1.3,
                        label="Indice" if method=="index" else "Scansione")
        ax.set(xscale="log",xlim=(.1,10000),ylim=(14.7,-.7),yticks=range(len(queries)),
               yticklabels=[q["id"] for q in queries],xlabel="Tempo (ms, scala log)")
        ax.set_title(label,fontsize=11,weight="bold",pad=15)
        ax.set_xticks([.1,1,10,100,1000,10000], ["0,1","1","10","100","1k","10k"])
        ax.tick_params(axis="x",labelsize=9)
        ax.grid(axis="x",color="#dce4e8")
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="lower center",ncol=2,frameon=False)
    fig.subplots_adjust(bottom=.11,top=.92)
    save(fig,"prestazioni")
    print("Sei figure di metodo e valutazione generate dagli aggregati pubblici.")


if __name__ == "__main__":
    main()
