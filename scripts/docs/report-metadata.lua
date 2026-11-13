-- Il contatto entra solo dalla configurazione locale opzionale della build.
function Meta(meta)
  if meta["contact-email"] then
    meta.author = pandoc.MetaInlines({
      pandoc.Str(pandoc.utils.stringify(meta.author)),
      pandoc.LineBreak(),
      pandoc.Str(pandoc.utils.stringify(meta["contact-email"]))
    })
  end
  return meta
end

-- Larghezze leggibili per conteggi e metriche; somma esatta dopo il rounding LaTeX.
function Table(tbl)
  local widths
  if #tbl.colspecs == 7 then
    widths = {0.16, 0.08, 0.08, 0.08, 0.20, 0.20, 0.20}
  elseif #tbl.colspecs == 4 and pandoc.utils.stringify(tbl.caption.long):match("^Statistiche") then
    widths = {0.14, 0.16, 0.35, 0.35}
  end
  if widths then
    for i, width in ipairs(widths) do
      tbl.colspecs[i][2] = width
    end
  end
  return tbl
end
