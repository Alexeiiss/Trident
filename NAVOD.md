# Trident – návod česky

20 skillů pro Claude na YouTube, TikTok a Instagram. Umí češtinu, ruštinu, rumunštinu a angličtinu.
Nic nepublikují – napíšou text, ty ho vložíš a zveřejníš.

## Instalace

**Aplikace Claude (web / desktop):** stáhni zipy z
[`downloads/`](downloads/) (všech 14 najednou: [`trident-claude-ai-skills.zip`](downloads/trident-claude-ai-skills.zip?raw=1)) a nahraj je v
Nastavení → Capabilities → Skills. Každý skill je samostatný zip i se svými nástroji.

**Claude Code:** `/plugin marketplace add Alexeiiss/trident` a pak `/plugin install trident`,
nebo zkopíruj složky `skills/td-*` do `~/.claude/skills/`.

## První krok: profil účtu

Napiš `/td-profile` a odpověz na pár otázek – zvlášť pro každý účet (např. ruský storytime TikTok,
rumunský @istorieascunsa, anglický YouTube). Výsledný soubor si ulož a přikládej ho do chatu, nebo
ho dej do Projektu – v aplikaci Claude se soubory mezi chaty neuchovávají.

## Co který skill dělá

| příkaz | k čemu |
| --- | --- |
| `/td-profile` | profil účtu: jazyk, formát, publikum, styl, pravidla |
| `/td-script` | scénář z nápadu – 5 hooků s hodnocením, pak celý text s popisem obrazu |
| `/td-package` | název + thumbnail (YT), cover + první řádek popisku (TikTok, IG) |
| `/td-caption` | popisek, hashtagy (IG max 5!), alt text, SEO pro jednu platformu |
| `/td-crosspost` | jedno video → hotové texty pro YouTube, TikTok i Instagram najednou |
| `/td-series` | rozdělení příběhu na díly s cliffhangerem; proč díly ztrácí diváky |
| `/td-clips` | najde v dlouhém videu krátká videa a napíše jim nový začátek |
| `/td-edit` | seznam střihů z titulků: ticho, vatová slova, opakované začátky |
| `/td-retention` | kde diváci odcházejí (YT export, nebo body z grafu TikTok / IG) |
| `/td-chapters` | kapitoly pro YouTube, které opravdu fungují |
| `/td-plan` | plán na týden přes všechny platformy a účty |
| `/td-trends` | co v nice funguje, měřeno proti mediánu každého kanálu |
| `/td-comment` | odpovědi na komentáře, co připnout |
| `/td-audit` | rozbor účtu, končí JEDNOU hlavní opravou |
| `/td-reel` | **nové:** ze scénáře hotové video 9:16 – hlas, titulky po slovech, pozadí, hudba |
| `/td-subtitles` | **nové:** titulky po slovech jako v CapCutu (.ass nebo rovnou ve videu) |
| `/td-cover` | **nové:** covery a thumbnaily, jednotná šablona pro celou sérii |
| `/td-studio` | **nové:** střižna jako CapCut – stříhání, 25 přechodů, zpomalení, 9:16 s rozmazaným pozadím, text, titulky, obraz v obraze, green screen, filtry, hlasové efekty, hudba, střih do rytmu, export |
| `/td-generate` | **nové:** obrázky, videa, české/ruské/rumunské hlasy, hudba a efekty přes ElevenLabs (stojí kredity) |
| `/td-stats` | **nové:** týdenní přehled z exportů – roste účet, nebo padá? |

## Hlas ve videích (`/td-reel`)

Offline hlas (Kokoro) umí jen anglicky. Pro češtinu, ruštinu a rumunštinu použij hlas z ElevenLabs
(`/td-generate`), nebo nahraj věty na telefon (01.m4a, 02.m4a… jedna věta = jeden soubor) a dej je do složky – Trident je
použije místo syntetického hlasu.

## Příklady

- „/td-reel udělej z dílu 1 video, pozadí slime.mp4, moje nahrávky jsou ve složce dil1/“
- „/td-stats tady je export z YouTube Studia – jak se mi daří?“

- „/td-series rozděl tenhle příběh o Dácích na 3 díly pro TikTok“ (přilož titulky nebo text)
- „/td-series díl 1 měl 52 000 zhlédnutí, díl 2 14 000, díl 3 9 800 – proč?“
- „/td-crosspost připrav tohle video pro anglický Instagram, anglický YouTube a rumunský TikTok“
- „/td-script storytime v ruštině: tchyně se nastěhuje bez ptaní“

## Prodej a licence

Licence MIT: můžeš balík upravovat i prodávat. Jen musí zůstat soubor `LICENSE` s původní poznámkou
o autorovi, ze kterého balík vychází (Jake Schincariol).
