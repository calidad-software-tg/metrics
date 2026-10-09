"""
Genera bots_clasificados.csv: login, tipo_cuenta
tipo_cuenta ∈ {humano, bot, agente_ia, desconocido}

Criterios (en orden de prioridad):
  1. desconocido : placeholder de cuentas eliminadas ("desconocido", "ghost")
  2. agente_ia   : herramienta de IA que escribe código
  3. bot         : type=Bot en la API, o BOTS_CONOCIDOS de base_metric.py,
                   o sufijo [bot] (GitHub Apps)
  4. humano      : cualquier otro caso. El nombre por sí solo NO decide.
                   Regla práctica: cuentas con ≤12 filas → humano salvo type=Bot
                   o evidencia clara de automatización en sus mensajes.

Excepciones manuales documentadas (verificadas con GET /users/{login} +
actividad en vercel/next.js el 2026-10-03):
"""
import csv
from pathlib import Path

# ── constantes ───────────────────────────────────────────────────────────────

DESCONOCIDOS = {"desconocido", "ghost"}

AGENTES_IA = {
    "Copilot",                      # agente IA de GitHub
    "copilot-swe-agent",            # agente IA de GitHub
    "devin-ai-integration",         # Devin AI (login sin sufijo [bot] en GraphQL)
    "devin-ai-integration[bot]",    # Devin AI (login con sufijo [bot] en REST)
    "cursor[bot]",                  # Cursor AI (GitHub App)
}

# BOTS_CONOCIDOS de base_metric.py de Luz (origin/luz/nextjs)
BOTS_CONOCIDOS = {
    "vercel-release-bot",       # bump automático de React interno de next.js
    "Vercel Release Bot",       # nombre git del mismo bot (run_versiones_local)
    "nextjs-bot",               # ~600 commits de release, email it+nextjs-bot@vercel.com
    "next-js-bot",              # GitHub App sin sufijo [bot] en GraphQL
    "next-js-bot[bot]",         # mismo con sufijo [bot] en REST
    "skia-flutter-autoroll",    # autoroll de Skia (flutter)
    "engine-flutter-autoroll",  # autoroll del motor Flutter
    "CLAassistant",             # bot de firma de CLA (tldr)
    "tldr-bot",                 # bot de bienvenida/lint (tldr)
    "github-actions",           # GitHub Actions sin sufijo [bot] (cierra issues auto)
    "dependabot",               # Dependabot sin sufijo [bot]
    "dependabot[bot]",          # Dependabot con sufijo [bot]
    "greenkeeperio-bot",        # bot de actualización de dependencias
    "codetriage-readme-bot",    # bot de CodeTriage
    "diffray-bot",              # bot de diff
    "askdevai-bot",             # bot de IA para preguntas
}

# ── excepciones manuales verificadas ─────────────────────────────────────────
# Todas verificadas con GET /users/{login} + actividad en vercel/next.js (2026-10-03).
# Logins que contienen "bot" pero son personas reales:

HUMANOS_VERIFICADOS = {
    # Tesis: explicitados como humanos
    "Ben Botvinick",        # git name de botv (ver abajo)
    "Thibaut SABOT",        # git name; SABOT = apellido francés
    "thibautsabot",         # login GitHub de Thibaut SABOT
    "cristianbote",         # login GitHub de Cristian Bote
    "Cristian Bote",        # git name; Bote = apellido rumano
    "ionut-botizan",        # login GitHub de Ionuț Botizan
    "Ionuț Botizan",        # git name (con tilde rumana)
    "Ionut Botizan",        # variante sin tilde
    "mitchell-abbott",      # login; Abbott = apellido anglosajón
    "Mitchell Abbott",      # git name
    "Adam Sobotka",         # git name; Sobotka = apellido checo
    "simon-abbott",         # Abbott = apellido
    "nbottarini",           # Bottarini = apellido italiano
    "alexcibotari",         # Botari = apellido
    "abotsi",               # Abotsi = apellido ghanés
    "Isaac Abotsi",         # git name
    "William Mbotta",       # git name; Mbotta = apellido africano
    "dimitribarbot",        # Barbot = apellido francés

    # REVISAR → verificados como humano (GET /users + actividad 2026-10-03)
    "botv",                 # Ben Botvinick: mismo individuo que "Ben Botvinick" (git name).
                            #   PR reales (#21145, #14947, #14705), 57 repos, 92 followers, @hyper
    "ishaqibrahimbot",      # Ishaq Ibrahim: full-stack engineer en Teamo Inc.
                            #   Fix real #42158, bio descriptiva, 36 repos, 31 followers
    "aaronbrown-vercel",    # Aaron Brown: empleado Vercel (docs de seguridad, #84156, #43837)
    "gijsbotje",            # Gijs Boddeus: frontend dev @afosto (NL). "botje" = diminutivo NL.
                            #   5 issues reales de routing/i18n, 48 repos, 17 followers
    "MaxmaxmaximusGitHub",  # Иван Вольнов: desarrollador ruso. 5 issues reales de bugs/features
    "Talbot3",              # 翎栋: desarrollador chino. PRs reales de fix with-mobx, 133 repos
    "chris-tsongas-vercel", # Chris Tsongas: Technical Consultant @Vercel. PR real, conversaciones
    "wim-vercel",           # Cuenta Vercel activa (comentó en conversaciones, ≤12 filas)
    "benbot",               # Benjamin Botwin: dev de distributed systems. Issue real de SVG.
                            #   116 repos, 59 followers. "benbot" = Ben + Botwin (apellido)
    "gbotedc",              # Issue real de intercepting routes. type=User (≤10 filas)
    "bottxiang",            # 404 (cuenta eliminada). Métricas de commit reales (cdiv, fexp, le).
                            #   "Bott" puede ser apellido chino/alemán. ≤12 filas → humano
    "javiervillam-axiom-robotics",  # Javier Villa, Axiom Robotics. 2 issues técnicos de `use cache`
    "caleb-vercel",         # Caleb An: Agentic Security SWE @Vercel. PR de approvers file
    "Risbot",               # Armen Hajrapetjan: issue real de asset/inline bug. 12 repos

    # bots_candidatos.csv → verificados como humano (GET /users + actividad 2026-10-03)
    "bot08",                # type=User, 49 repos. PR real: "fixed tailwind ver in readme" (#42551)
    "cpubot",               # Zach Brown: PR real de React 16 support. 85 followers, activo desde 2011
    "TurekBot",             # Bradley Turek: PR real de docs (#31224). 118 repos
    "miinabot",             # type=User. PR real: lint-staged example fix. Comentó en conversaciones
    "reconbot",             # Francis Gulotta: mantenedor de @node-serialport. 483 followers, 292 repos,
                            #   activo desde 2008. PRs reales de types (#49166) y docs (#35922)
    "minimabot",            # Myeonghwan Cho: engineer en Japón. PR real de docs fix (#38586), 55 repos
    "Zoe-Bot",              # type=User. PR real: "docs(fix): example text unescaped entities" (#57255)
    "luiscobot",            # Luis Romero: dev en Creditop. PR real: "fix typo" (#80282). 55 followers

    # bots_candidatos con ≤12 filas → humano por regla (no vale la pena más análisis;
    # type=User sin evidencia de automatización en sus mensajes)
    "dawsbot",              # 6 filas en sc. ≤12 → humano
    "oop39391-bot",         # 2 filas en sc. ≤12 → humano
    "rsandsrealtor-bot",    # 2 filas en sc. ≤12 → humano
    "thomas-delivery-factory-bot",  # 2 filas en sc. ≤12 → humano
    "maths-bot",            # 2 filas en sc. ≤12 → humano
    "ishimwereponse223-bot",# 2 filas en sc. ≤12 → humano
    "jlaportebot",          # 2 filas en sc. ≤12 → humano
    "warmrobot",            # 2 filas en sc. ≤12 → humano
    "wootsbot",             # 2 filas en sc. ≤12 → humano
}

# ── lógica de clasificación ──────────────────────────────────────────────────

def clasificar(login: str) -> str:
    if login in DESCONOCIDOS:
        return "desconocido"
    if login in AGENTES_IA:
        return "agente_ia"
    if login.endswith("[bot]"):        # GitHub Apps (REST) no clasificados antes
        return "bot"
    if login in BOTS_CONOCIDOS:
        return "bot"
    if login in HUMANOS_VERIFICADOS:   # excepciones manuales tienen prioridad sobre humano genérico
        return "humano"
    return "humano"

# ── lectura de logins y escritura ────────────────────────────────────────────

logins_file = Path(__file__).parent / "bots_clasificados.csv"
todos = sorted(set(
    l.strip()
    for l in Path("/tmp/todos_logins.txt").read_text().splitlines()
    if l.strip()
))

rows = [(login, clasificar(login)) for login in todos]

with open(logins_file, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["login", "tipo_cuenta"])
    w.writerows(rows)

# ── resumen ──────────────────────────────────────────────────────────────────
from collections import Counter
counts = Counter(t for _, t in rows)
print("=== TOTALES ===")
for tipo, n in sorted(counts.items()):
    print(f"  {tipo:15s} {n:6d}")
print(f"  {'TOTAL':15s} {sum(counts.values()):6d}")

print("\n=== NO-HUMANOS ===")
print(f"{'login':<45} {'tipo_cuenta'}")
print("-" * 65)
no_humanos = [(l, t) for l, t in rows if t != "humano"]
for login, tipo in sorted(no_humanos, key=lambda x: (x[1], x[0])):
    print(f"{login:<45} {tipo}")
