#!/usr/bin/env python3
"""
check-wording.py -- fail on British spellings anywhere in the theme, and on breadcrumb
Customizer labels that are not in Title Case.

Why this exists
---------------
Both are Aaron's rulings from the breadcrumbs review on TTT staging, 2026-09-26:

* "We are in the United States of America, in Cleveland, Ohio, and there is no 'u' in
  'color'." The Breadcrumbs section had shipped to staging saying "Link colour",
  "Background colour" and "Text colour", and 80 British spellings sat across seven theme
  files (colour, centred, grey, recognisable, labelled, cancelling, normalises).
* "It would be great if the descriptions were title-cased ... 'Link color on hover' ...
  would have the first letter of every word capitalized except for 'on'."

A written rule is only hoped for; this makes the next "colour" fail a required check.

What it does
------------
1. Reads every text file under theme/braillewright (PHP, JS, CSS, SCSS, TXT, JSON) and
   fails on any word in BRITISH. Skipped: lib/ (the third-party Plugin Update Checker),
   node_modules/, minified files (built from sources that are checked), and
   features/assets/fonts.json, whose font names ("La Belle Aurore") are not prose.
2. Reads the files in LABEL_FILES (inc/breadcrumbs.php, and since 2026-09-27
   inc/header-menu.php) and checks every Customizer label, section title and choice
   name in them for Title Case: every word capitalized except the SMALL words, which stay
   lower case unless they are the first or last word.
3. --self-test feeds known-bad and known-good text through both checks and fails unless
   each is judged correctly, so the check is proven able to say no.

BRITISH is also the American-spelling list of Aaron's newsletter tools, which read it as
data with ast.literal_eval: keep it a plain dict literal (BRITISH = {...}).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME = os.path.join(ROOT, "theme", "braillewright")
BREADCRUMBS = os.path.join(THEME, "inc", "breadcrumbs.php")
# Files whose Customizer labels are held to Title Case, with the fewest labels each must yield
# (a count far below that means the extractor stopped matching the file, not that it is clean).
# inc/header-menu.php joined on 2026-09-27 with the logo spacing and menu options.
LABEL_FILES = [
    (os.path.join("inc", "breadcrumbs.php"), 15),
    (os.path.join("inc", "header-menu.php"), 4),
    (os.path.join("inc", "dropdown-menu.php"), 13),
]

BRITISH = {
    "colour": "color", "colours": "colors", "coloured": "colored", "colouring": "coloring",
    "centre": "center", "centred": "centered", "centres": "centers", "grey": "gray",
    "greys": "grays", "behaviour": "behavior", "favourite": "favorite", "honour": "honor",
    "labour": "labor", "neighbour": "neighbor", "licence": "license", "catalogue": "catalog",
    "labelled": "labeled", "labelling": "labeling", "cancelled": "canceled",
    "cancelling": "canceling", "travelled": "traveled", "modelled": "modeled",
    "recognise": "recognize", "recognised": "recognized", "recognisable": "recognizable",
    "organise": "organize", "organised": "organized", "organisation": "organization",
    "customise": "customize", "customised": "customized", "optimise": "optimize",
    "optimised": "optimized", "summarise": "summarize", "prioritise": "prioritize",
    "normalise": "normalize", "normalises": "normalizes", "normalised": "normalized",
    "minimise": "minimize", "maximise": "maximize", "realise": "realize", "analyse": "analyze",
    "utilise": "utilize", "visualise": "visualize", "categorise": "categorize",
    "standardise": "standardize", "authorise": "authorize", "initialise": "initialize",
    # Added 2026-10-14 from the newsletters' own list (Aaron, round 2026-10-14-spelling-readers-A,
    # "Yes, move them into Braillewright's list"): one list for the theme and his newsletter tools.
    # This check matches these exact words; the newsletter tools also derive their other forms.
    # found in Aaron's newsletters, or named when their check was built
    "maths": "math", "programme": "program", "programmes": "programs", "ageing": "aging",
    "judgement": "judgment", "judgements": "judgments",
    "aluminium": "aluminum", "artefact": "artifact", "artefacts": "artifacts",
    "cheque": "check", "cheques": "checks", "jewellery": "jewelry", "kerb": "curb",
    "kerbs": "curbs", "tyre": "tire", "tyres": "tires", "storey": "story", "storeys": "stories",
    "greyed": "grayed", "greying": "graying", "greyish": "grayish", "greyer": "grayer",
    "greyest": "grayest", "greyness": "grayness", "greyscale": "grayscale",
    "mould": "mold", "moulds": "molds", "moulded": "molded", "moulding": "molding",
    "mouldy": "moldy", "sceptic": "skeptic", "sceptics": "skeptics", "sceptical": "skeptical",
    "sceptically": "skeptically", "scepticism": "skepticism", "enrol": "enroll",
    "enrols": "enrolls", "enrolment": "enrollment", "enrolments": "enrollments",
    "fulfil": "fulfill", "fulfils": "fulfills", "fulfilment": "fulfillment",
    "instalment": "installment", "instalments": "installments", "skilful": "skillful",
    "skilfully": "skillfully", "wilful": "willful", "wilfully": "willfully",
    "practise": "practice", "practised": "practiced", "practises": "practices",
    "practising": "practicing", "manoeuvre": "maneuver", "manoeuvres": "maneuvers",
    "manoeuvred": "maneuvered", "manoeuvring": "maneuvering", "manoeuvrable": "maneuverable",
    "licences": "licenses", "licenced": "licensed", "defence": "defense",
    "defences": "defenses", "offence": "offense", "offences": "offenses",
    "pretence": "pretense", "analogue": "analog", "counsellor": "counselor",
    "counsellors": "counselors",
    # -re
    "theatre": "theater", "metre": "meter", "kilometre": "kilometer",
    "centimetre": "centimeter", "millimetre": "millimeter", "litre": "liter",
    "fibre": "fiber", "calibre": "caliber", "spectre": "specter", "datacentre": "datacenter",
    # medicine
    "paediatric": "pediatric", "paediatrics": "pediatrics", "paediatrician": "pediatrician",
    "paediatricians": "pediatricians", "orthopaedic": "orthopedic", "orthopaedics": "orthopedics",
    "anaemia": "anemia", "anaemic": "anemic", "anaesthesia": "anesthesia",
    "anaesthetic": "anesthetic", "anaesthetics": "anesthetics", "haemorrhage": "hemorrhage",
    "haemophilia": "hemophilia", "haemoglobin": "hemoglobin", "leukaemia": "leukemia",
    "oesophagus": "esophagus", "oesophageal": "esophageal", "oestrogen": "estrogen",
    "foetus": "fetus", "foetal": "fetal", "diarrhoea": "diarrhea", "gynaecology": "gynecology",
    "gynaecologist": "gynecologist", "oedema": "edema", "encyclopaedia": "encyclopedia",
    "encyclopaedic": "encyclopedic",
    # -our
    "favour": "favor", "flavour": "flavor", "harbour": "harbor", "humour": "humor",
    "odour": "odor", "rumour": "rumor", "savour": "savor", "tumour": "tumor",
    "vapour": "vapor", "vigour": "vigor", "rigour": "rigor", "armour": "armor",
    "endeavour": "endeavor", "parlour": "parlor", "candour": "candor", "clamour": "clamor",
    "splendour": "splendor", "valour": "valor", "fervour": "fervor", "ardour": "ardor",
    "saviour": "savior",
    # -yse
    "paralyse": "paralyze", "catalyse": "catalyze",
    # doubled l; -ing, -er and -ers are derived
    "trialled": "trialed", "dialled": "dialed", "spiralled": "spiraled", "levelled": "leveled",
    "signalled": "signaled", "fuelled": "fueled", "counselled": "counseled",
    "channelled": "channeled", "marvelled": "marveled", "totalled": "totaled",
    "tunnelled": "tunneled", "quarrelled": "quarreled", "rivalled": "rivaled",
    "equalled": "equaled",
    # -ise verbs
    "accessorise": "accessorize", "agonise": "agonize", "anonymise": "anonymize",
    "antagonise": "antagonize", "apologise": "apologize", "capitalise": "capitalize",
    "centralise": "centralize", "characterise": "characterize", "colonise": "colonize",
    "commercialise": "commercialize", "conceptualise": "conceptualize",
    "contextualise": "contextualize", "criminalise": "criminalize", "criticise": "criticize",
    "democratise": "democratize", "demonise": "demonize", "digitalise": "digitalize",
    "digitise": "digitize", "dramatise": "dramatize", "economise": "economize",
    "emphasise": "emphasize", "empathise": "empathize", "energise": "energize",
    "epitomise": "epitomize", "evangelise": "evangelize", "externalise": "externalize",
    "familiarise": "familiarize", "fantasise": "fantasize", "fertilise": "fertilize",
    "finalise": "finalize", "formalise": "formalize", "galvanise": "galvanize",
    "generalise": "generalize", "glamorise": "glamorize", "globalise": "globalize",
    "harmonise": "harmonize", "hospitalise": "hospitalize", "humanise": "humanize",
    "hypothesise": "hypothesize", "idealise": "idealize", "immunise": "immunize",
    "incentivise": "incentivize", "individualise": "individualize",
    "industrialise": "industrialize", "institutionalise": "institutionalize",
    "internalise": "internalize", "internationalise": "internationalize",
    "italicise": "italicize", "itemise": "itemize", "jeopardise": "jeopardize",
    "legalise": "legalize", "legitimise": "legitimize", "liberalise": "liberalize",
    "localise": "localize", "marginalise": "marginalize", "materialise": "materialize",
    "memorialise": "memorialize", "memorise": "memorize", "metabolise": "metabolize",
    "mobilise": "mobilize", "modernise": "modernize", "monetise": "monetize",
    "monopolise": "monopolize", "moralise": "moralize", "motorise": "motorize",
    "nationalise": "nationalize", "neutralise": "neutralize",
    "operationalise": "operationalize", "ostracise": "ostracize", "patronise": "patronize",
    "penalise": "penalize", "personalise": "personalize", "plagiarise": "plagiarize",
    "polarise": "polarize", "popularise": "popularize", "pressurise": "pressurize",
    "privatise": "privatize", "publicise": "publicize", "radicalise": "radicalize",
    "randomise": "randomize", "rationalise": "rationalize", "revitalise": "revitalize",
    "revolutionise": "revolutionize", "romanticise": "romanticize", "sanitise": "sanitize",
    "scrutinise": "scrutinize", "sensationalise": "sensationalize", "sensitise": "sensitize",
    "serialise": "serialize", "sexualise": "sexualize", "socialise": "socialize",
    "specialise": "specialize", "stabilise": "stabilize", "sterilise": "sterilize",
    "stigmatise": "stigmatize", "strategise": "strategize", "subsidise": "subsidize",
    "symbolise": "symbolize", "sympathise": "sympathize", "synchronise": "synchronize",
    "synthesise": "synthesize", "systematise": "systematize", "terrorise": "terrorize",
    "theorise": "theorize", "tokenise": "tokenize", "traumatise": "traumatize",
    "trivialise": "trivialize", "unionise": "unionize", "urbanise": "urbanize",
    "vandalise": "vandalize", "vaporise": "vaporize", "verbalise": "verbalize",
    "victimise": "victimize", "virtualise": "virtualize", "vocalise": "vocalize",
    "weaponise": "weaponize", "westernise": "westernize",
}
BRITISH_RE = re.compile(r"\b(" + "|".join(sorted(BRITISH, key=len, reverse=True)) + r")\b", re.IGNORECASE)
EXTENSIONS = (".php", ".js", ".css", ".scss", ".txt", ".json")
SKIP_DIRS = ("lib", "node_modules")
SKIP_FILES = (os.path.join("features", "assets", "fonts.json"),)

# Lower case inside a Title Case label: articles, short conjunctions and prepositions of three
# letters or fewer. "Out", "Up" and "Off" are left out on purpose: in "Leave Emoji Out of the
# Breadcrumbs?" they belong to the verb and are capitalized.
SMALL = {"a", "an", "the", "and", "but", "or", "nor", "for", "so", "yet", "as", "at", "by",
         "in", "of", "on", "per", "to", "via", "vs"}

LABEL_RE = re.compile(r"'(?:label|title)'\s*=>\s*(?:esc_html__|__|_x)\(\s*'((?:[^'\\]|\\.)*)'")
COLOR_ROW_RE = re.compile(r"=>\s*array\(\s*__\(\s*'((?:[^'\\]|\\.)*)'")


def british_findings(text):
    """Every (line number, word, American form) for a British spelling in text."""
    out = []
    for number, line in enumerate(text.splitlines(), 1):
        for m in BRITISH_RE.finditer(line):
            out.append((number, m.group(0), BRITISH[m.group(0).lower()]))
    return out


def title_case_problem(label):
    """'' when label is Title Case, otherwise the word that breaks it."""
    words = label.split()
    for i, word in enumerate(words):
        core = re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", word)
        if not core:
            continue
        edge = i == 0 or i == len(words) - 1
        if core.lower() in SMALL and not edge:
            if core != core.lower():
                return f'"{core}" should be lower case'
        elif not core[0].isupper():
            return f'"{core}" should start with a capital'
    return ""


def breadcrumb_labels(php):
    """Every label, section title and choice name in inc/breadcrumbs.php."""
    labels = [m.group(1) for m in LABEL_RE.finditer(php)]
    labels += [m.group(1) for m in COLOR_ROW_RE.finditer(php)]
    body = re.search(r"function braillewright_breadcrumbs_backgrounds\(\)\s*\{(.*?)\n\t\}", php, re.S)
    if body:
        labels += re.findall(r"=>\s*__\(\s*'((?:[^'\\]|\\.)*)'", body.group(1))
    return [label.replace("\\'", "'") for label in labels]


def check_repo():
    failures = []
    files = 0
    for root, dirs, names in os.walk(THEME):
        rel_root = os.path.relpath(root, THEME)
        if rel_root.split(os.sep)[0] in SKIP_DIRS:
            dirs[:] = []
            continue
        for name in names:
            rel = os.path.normpath(os.path.join(rel_root, name))
            if not name.endswith(EXTENSIONS) or ".min." in name or rel in SKIP_FILES:
                continue
            files += 1
            with open(os.path.join(root, name), encoding="utf-8", errors="replace") as handle:
                for number, word, us in british_findings(handle.read()):
                    failures.append(f"{rel}:{number}: British spelling \"{word}\" -- use \"{us}\"")

    total = 0
    for rel, minimum in LABEL_FILES:
        with open(os.path.join(THEME, rel), encoding="utf-8") as handle:
            labels = breadcrumb_labels(handle.read())
        total += len(labels)
        if len(labels) < minimum:
            failures.append(f"{rel}: found only {len(labels)} labels, expected at least {minimum}; the extractor no longer matches the file")
        for label in labels:
            problem = title_case_problem(label)
            if problem:
                failures.append(f"{rel}: label \"{label}\" is not Title Case: {problem}")

    print(f"checked {files} theme files for British spelling and {total} labels for Title Case")
    return failures


def self_test():
    cases = [
        (british_findings("$label = 'Link colour';"), True, "catches colour"),
        (british_findings("Colours left empty"), True, "catches Colours, any case"),
        (british_findings("a centred line on the grey page"), True, "catches centred and grey"),
        (british_findings("Link color, the gray page, a centered line"), False, "passes American spelling"),
        (british_findings("labelleaurore"), False, "does not match inside another word"),
        (british_findings("accessible maths for all"), True, "catches maths, from the newsletters' words"),
        (title_case_problem("Link colour on hover"), True, "catches lower-case words"),
        (title_case_problem("Link Color On Hover"), True, "catches a capitalized small word"),
        (title_case_problem("Link Color on Hover"), False, "passes Link Color on Hover"),
        (title_case_problem("Show the Current Page's Title at the End?"), False, "passes a question with an apostrophe"),
        (title_case_problem("Leave Emoji Out of the Breadcrumbs?"), False, "keeps Out capitalized"),
        (title_case_problem("the Background"), True, "capitalizes a small first word"),
        (title_case_problem("Chevron ›"), False, "ignores a symbol word"),
        (breadcrumb_labels("'label' => __( 'A', 'x' ), 'title' => __( 'B', 'x' ), 'k' => array( __( 'C', 'x' ), __( 'd', 'x' ), 40 )"),
         ["A", "B", "C"], "extracts labels, titles and the first string of a color row"),
    ]
    bad = 0
    for result, expected, name in cases:
        ok = (result == expected) if isinstance(expected, list) else (bool(result) == expected)
        bad += not ok
        print(("ok      " if ok else "WRONG   ") + name + ("" if ok else f" -> {result!r}"))
    print(f"self-test: {len(cases) - bad} of {len(cases)} judged correctly")
    return bad


def main():
    if "--self-test" in sys.argv:
        sys.exit(1 if self_test() else 0)
    failures = check_repo()
    for failure in failures:
        print("FAIL  " + failure)
    print("RESULT: " + ("FAIL" if failures else "PASS"))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
