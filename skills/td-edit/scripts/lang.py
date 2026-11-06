#!/usr/bin/env python3
"""lang.py - the language layer every Trident tool shares.

Supported: en (English), cs (Czech), ru (Russian), ro (Romanian / Moldovan).
Detection is a heuristic on the script and the diacritics, and every tool lets you force it with
--lang. Lexicons are STEMS matched at the start of a token, because Czech, Russian and Romanian
inflect: "ztrat" catches ztratíš, ztratil, ztráta is a separate stem.

No dependencies. Unicode-safe tokenising, so Cyrillic and diacritics are words, not gaps.
"""
import re

LANGS = ("en", "cs", "ru", "ro")
TOKEN = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)

def tokens(text):
    return [t.lower() for t in TOKEN.findall(text or "")]

def detect(text):
    t = text or ""
    cyr = len(re.findall(r"[а-яёА-ЯЁ]", t))
    lat = len(re.findall(r"[a-zA-Z]", t))
    if cyr and cyr >= lat * 0.5:
        return "ru"
    low = t.lower()
    toks = tokens(low)
    score = {
        "cs": 3 * len(re.findall(r"[ěščřžůňťď]", low)) + len(re.findall(r"[áéíóúý]", low)),
        "ro": 3 * len(re.findall(r"[ăâîșşțţ]", low)),
        "en": 0,
    }
    marks = {
        "en": {"the", "and", "is", "are", "of", "to", "you", "your", "this", "that", "with", "was", "it", "what", "how", "why"},
        "cs": {"je", "se", "že", "jsem", "jsou", "není", "jak", "proč", "když", "ale", "to", "na", "co", "jsi", "byl", "před", "let"},
        "ro": {"și", "si", "este", "sunt", "nu", "pentru", "care", "cum", "că", "asta", "acum", "de", "ani", "au", "pe", "acest",
               "această", "cu", "din", "un", "o", "la", "mai", "ce", "iată"},
    }
    for lg, words in marks.items():
        score[lg] += 2 * sum(1 for w in toks if w in words)
    best = max(score, key=score.get)
    return best if score[best] > 0 else "en"

# ---- lexicons -----------------------------------------------------------------------------
# Each entry is a stem; a token matches when it starts with the stem. Multi-word entries are
# matched as phrases against the lowercased text instead.

LEX = {
 "en": {
  "conflict": ["sister", "brother", "mom", "mother", "dad", "father", "husband", "wife", "boyfriend", "girlfriend", "in-law", "boss", "neighbor", "neighbour", "wedding", "divorce", "cheat", "stole", "lied", "betray", "screamed", "slapped", "kicked out", "army", "war", "enemy", "hunger", "winter"],
  "you": ["you", "your", "yourself", "you're", "youre", "ya"],
  "you_exact": True,
  "stake": ["lose", "lost", "losing", "wast", "quit", "fail", "broke", "cost", "risk", "before",
            "stop", "never", "die", "dying", "dead", "ruin", "mistake", "wrong"],
  "curiosity": ["why", "how", "what", "which", "until", "but", "nobody", "almost", "except",
                "reason", "actually", "secretly", "turns out", "no one", "nobody knew"],
  "closed": ["because", "so that", "which means"],
  "vague": ["amazing", "incredible", "insane", "crazy", "huge", "massive", "gamechanger",
            "game-changer", "secret", "powerful", "ultimate", "best", "revolutionary",
            "mindblowing", "unbelievable", "epic", "perfect"],
  "filler": ["basically", "literally", "just", "really", "very", "kind of", "sort of", "like",
             "guys", "hey", "welcome", "today", "video", "subscribe", "channel"],
  "filler_only": ["um", "umm", "uh", "uhh", "er", "erm", "ah", "so", "okay", "ok", "right", "yeah",
                  "like", "anyway", "basically", "actually", "you know", "i mean", "let me see",
                  "hold on"],
  "stop": "the a an of for to in on and or is are was were be been with this that it as at by from "
          "you your i my we our they them he she but so if then than there here what which who how "
          "when where why not no yes do does did just really very like about into over out up down "
          "can could will would should have has had get got make made go going went one two",
 },
 "cs": {
  "conflict": ["sestr", "bratr", "mám", "matk", "otc", "táta", "manžel", "přítel", "tchyn", "šéf", "soused", "svatb", "rozvod", "podved", "ukradl", "lhal", "zradil", "křičel", "vyhodil", "armád", "válk", "nepřítel", "hlad", "zim"],
  # 2nd person: pronouns + the -š verb ending (děláš, víš, můžeš) handled in address()
  "you": ["ty", "tě", "tebe", "tobě", "tebou", "tvůj", "tvoj", "tvá", "tvé", "tvého", "tvým",
          "tvou", "vy", "vás", "vám", "vámi", "váš", "vaš", "jsi", "seš"],
  "you_exact": True,
  "stake": ["ztrat", "ztrác", "skonč", "vzd", "přijd", "přišel", "přišl", "prohr", "chyb", "plýtv", "vyhaz",
            "stoj", "riskuj", "rizik", "nikdy", "přestaň", "konec", "zemř", "smrt", "mrtv",
            "zniči", "zničí", "krach", "škod", "dřív než", "než začneš", "nedělej"],
  "curiosity": ["proč", "jak", "co", "který", "která", "které", "dokud", "ale", "nikdo",
                "skoro", "téměř", "kromě", "důvod", "vlastně", "ukázalo se", "nikdo neví",
                "netušil", "netušila"],
  "closed": ["protože", "takže", "což znamená", "a proto"],
  "vague": ["úžasn", "neuvěřiteln", "šílen", "obrovsk", "masivn", "tajn", "nejlepš", "mocn",
            "revoluční", "epick", "dokonal", "boží", "luxusní"],
  "filler": ["prostě", "doslova", "fakt", "jako", "teda", "ahoj", "vítej", "dneska", "dnes",
             "video", "odebír", "kanál", "lajk"],
  "filler_only": ["ehm", "eh", "hm", "hmm", "no", "takže", "jako", "prostě", "teda", "dobře",
                  "jo", "tak", "vlastně", "víš co", "počkej"],
  "stop": "a i o u v ve z ze k ke s se na do od po pro při za je jsou byl byla bylo být to ten ta "
          "tu ty tak jak co kde kdy proč že ale nebo ani už jen jsem jsi jsme jste mám máš má "
          "mít jeho její jejich náš váš můj tvůj se si mi mě ti tě on ona ono oni my vy tady tam "
          "taky také ještě než když jestli by aby",
 },
 "ru": {
  "conflict": ["сестр", "брат", "мам", "мать", "матер", "отец", "отц", "пап", "муж", "жен", "парен", "девушк", "свекров", "тёщ", "тещ", "свёкр", "начальн", "сосед", "свадьб", "свадеб", "развод", "измен", "украл", "соврал", "лгал", "предал", "кричал", "выгнал", "арми", "войн", "враг", "голод", "зим"],
  "you": ["ты", "тебя", "тебе", "тобой", "твой", "твоя", "твоё", "твое", "твои", "твоего",
          "твоей", "твоих", "вы", "вас", "вам", "вами", "ваш", "ваша", "ваше", "ваши", "вашего"],
  "you_exact": True,
  "stake": ["теря", "потер", "проигр", "ошиб", "трат", "стоит", "стоил", "риск", "никогда",
            "хватит", "перестань", "умер", "умир", "смерт", "мёртв", "мертв", "провал", "брос",
            "разор", "погиб", "убил", "уничтож", "до того как", "пока не поздно", "не делай"],
  "curiosity": ["почему", "как", "что", "какой", "какая", "какие", "пока", "но", "никто",
                "почти", "кроме", "причин", "на самом деле", "зачем", "оказалось", "никто не знал",
                "даже не", "вдруг"],
  "closed": ["потому что", "поэтому", "а значит", "так что"],
  "vague": ["потрясающ", "невероятн", "безумн", "огромн", "секрет", "лучш", "мощн", "революц",
            "эпичн", "идеальн", "крут", "шок"],
  "filler": ["просто", "короче", "типа", "буквально", "вообще", "очень", "ну", "привет", "всем",
             "сегодня", "видео", "подпиш", "канал", "лайк"],
  "filler_only": ["э", "ээ", "эм", "ммм", "ну", "короче", "типа", "вот", "так", "ладно", "значит",
                  "как бы", "в общем", "слушай"],
  "stop": "и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по только "
          "ее её мне было вот от меня еще ещё нет о из ему теперь когда даже ну вдруг ли если уже "
          "или ни быть был него до вас нибудь опять уж вам ведь там потом себя ничего ей может они "
          "тут где есть надо ней для мы тебя их чем была сам чтоб без будто чего раз тоже себе под "
          "будет ж тогда кто этот того потому этого какой совсем ним здесь этом один почти мой тем "
          "чтобы нее сейчас были куда зачем всех никогда можно при наконец два об другой хоть после "
          "над больше тот через эти нас про всего них какая много разве три эту моя впрочем хорошо "
          "свою этой перед иногда лучше чуть том нельзя такой им более всегда конечно всю между это",
 },
 "ro": {
  "conflict": ["sor", "frat", "mam", "tat", "soț", "soţ", "iubit", "soacr", "socr", "șef", "vecin", "nunt", "divorț", "înșel", "furat", "mințit", "trădat", "țipat", "dat afară", "armat", "război", "dușman", "foamet", "iarn"],
  "you": ["tu", "te", "ți", "ţi", "tine", "tău", "tau", "ta", "tăi", "tale", "voi", "vă", "vouă",
          "vostru", "voastră", "voștri", "dumneata", "dumneavoastră"],
  "you_exact": True,
  "stake": ["pierd", "pierz", "renunț", "renunţ", "greș", "greş", "risip", "costă", "cost", "risc", "niciodată",
            "oprește", "nu mai", "moar", "mort", "muri", "eșu", "eşu", "ratat", "distrus",
            "înainte să", "inainte sa", "nu face"],
  "curiosity": ["de ce", "cum", "ce", "care", "până", "dar", "nimeni", "aproape", "cu excepția",
                "motiv", "de fapt", "s-a dovedit", "nimeni nu știa", "nici măcar", "brusc"],
  "closed": ["pentru că", "pentru ca", "deci", "ceea ce înseamnă", "așa că"],
  "vague": ["uimitor", "incredibil", "nebun", "imens", "enorm", "secret", "cel mai bun", "puternic",
            "revoluționar", "epic", "perfect", "senzațional", "șocant"],
  "filler": ["practic", "literalmente", "chiar", "foarte", "salut", "bun venit", "azi", "astăzi",
             "video", "abonea", "canal", "like"],
  "filler_only": ["ăă", "ăăă", "ă", "îm", "păi", "deci", "gen", "bine", "așa", "adică", "știi",
                  "stai"],
  "stop": "și si în in la de pe cu un o a al ale ai lui ei este e sunt nu da ce care cum că ca să sa "
          "se mai din pentru pentru dar sau am ai are au fost fi eu tu el ea noi voi ei ele acest "
          "această asta acesta aici acolo când unde de ce foarte mult doar tot toate",
 },
}

def lex(lang, key):
    return LEX.get(lang, LEX["en"])[key]

def stopwords(lang):
    return set(LEX.get(lang, LEX["en"])["stop"].split())

def count(text, lang, key):
    """How many tokens / phrases in text hit the lexicon `key` for `lang`."""
    low = (text or "").lower()
    toks = tokens(low)
    n = 0
    for entry in lex(lang, key):
        if " " in entry:
            n += len(re.findall(r"(?<!\w)" + re.escape(entry) + r"(?!\w)", low))
        elif key == "you" or len(entry) <= 3:
            # short entries ("co", "но", "how") would prefix-match half the dictionary
            n += sum(1 for t in toks if t == entry)
        else:
            n += sum(1 for t in toks if t.startswith(entry))
    return n

def second_person_verbs(text, lang):
    toks = tokens(text)
    if lang == "cs":
        return sum(1 for t in toks if len(t) > 3 and re.search(r"[aeiíáě]š$", t))
    if lang == "ru":
        return sum(1 for t in toks if len(t) > 3 and re.search(r"(ешь|ишь|ёшь)$", t))
    return 0

def is_filler_only(text, lang):
    """True when a cue is nothing but filler in this language (or English, which leaks into all)."""
    toks = tokens(text)
    if not toks:
        return False
    low = " " + " ".join(toks) + " "
    for lg in {lang, "en"}:
        for p in sorted(lex(lg, "filler_only"), key=len, reverse=True):
            low = low.replace(" " + p + " ", " ")
    return low.strip() == ""

NUM = re.compile(r"\d")
CURRENCY = re.compile(r"[$€£₽]|\b(kč|czk|eur|usd|lei|ron|mdl|руб|₴)\b", re.I)

def concrete(text):
    """Numbers, money, percentages. Language-independent on purpose."""
    nums = len(re.findall(r"\d[\d\s.,]*\d|\d", text or ""))
    return nums + len(CURRENCY.findall(text or "")) + len(re.findall(r"%", text or ""))

def capitalised_names(text):
    """Capitalised words that are not sentence-initial: names, places, products."""
    words = (text or "").split()
    n, prev_end = 0, True
    for w in words:
        clean = w.strip("\"'«»„“”()[]")
        if clean[:1].isupper() and not prev_end and not clean.isupper():
            n += 1
        prev_end = clean[-1:] in ".!?:" if clean else prev_end
    return n
