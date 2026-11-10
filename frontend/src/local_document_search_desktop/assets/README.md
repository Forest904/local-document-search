# Asset Luma

Grafica originale di Local Document Search, senza asset Google/ChatGPT o font
scaricati. Simbolo documento/luce, marchio Segoe UI e icone di interfaccia
nelle varianti chiara/scura. SVG sorgenti, PNG a 16/24/32/48/64/128/256 pixel,
ICO Windows con tutte le risoluzioni. Il marchio usa il font di sistema Windows.

`luma-desktop-original.png` è l'icona fornita dall'utente: viene mostrata nel
marchio interno e genera l'ICO per finestra, eseguibile e installer. Gli altri
mockup allegati guidano colori e composizione. Non vengono inseriti direttamente
nelle schermate perché includono uno sfondo chiaro e slogan italiani rasterizzati,
che sarebbero poco leggibili nel tema scuro e non traducibili in inglese.

Rigenerare dalla root con l'ambiente di sviluppo:

```powershell
backend/.venv/Scripts/python.exe scripts/dev/generate_luma_assets.py
```

Il generatore usa QtSvg e QImage offline. I PNG `logo-*` derivano dagli SVG;
i PNG `luma-desktop-*` e l'ICO derivano dall'icona fornita dall'utente. Le icone
dei controlli usano gli SVG appropriati al tema.

Le icone `zoom-in`, `zoom-out`, `fit` ed `external` del viewer sono SVG
originali mantenuti a mano: non sono prodotti dal generatore. Le icone
`back`, `search`, `next`, `close` e `folder` sono riutilizzate nel viewer.
