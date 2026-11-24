import os, sqlite3, secrets
from functools import wraps
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, abort
from werkzeug.security import generate_password_hash, check_password_hash

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(ROOT, "qaida.db"))
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cle-a-changer-pour-un-usage-en-ligne")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

PLAYLIST = "https://www.youtube.com/playlist?list=PL35d5prLj5n_ulpItCWJnlhHVcakcv4iR"

# QCM d'entraînement rédigés à partir des notions et objectifs du livre PDF fourni.
# Les questions de lecture orale nécessitent aussi une vérification par l'enseignant.
LESSONS = [
 {"title":"Les lettres de l'alphabet","video":"Présentation et alphabet","book":"Chapitre 1","questions":[
  ("Combien de lettres compte l'alphabet arabe présenté dans le livre ?",["26","28","30"],1),
  ("Une lettre arabe possède notamment…",["une forme, un nom et un son","un seul son écrit en français","toujours la même forme"],0),
  ("Dans ce chapitre, l'élève apprend aussi à reconnaître…",["uniquement les chiffres","les différentes formes des lettres et la Hamzah","seulement les voyelles"],1)]},
 {"title":"Les voyelles et la Soukoûn","video":"Les voyelles dans la langue arabe","book":"Chapitre 2","questions":[
  ("Quelles voyelles sont étudiées dans le chapitre ?",["Fathah, Kasrah et Dammah","Tanwîn, Chaddah et Hamzah","Alif, Wâw et Yâ"],0),
  ("La Soukoûn indique que la lettre est…",["doublée","sans voyelle","prolongée"],1),
  ("Quelle est la progression des voyelles indiquée dans le livre ?",["Dammah, Kasrah, Fathah","Fathah, Kasrah, Dammah","Kasrah, Dammah, Fathah"],1)]},
 {"title":"Le Tanwîn","video":"Le Tanwin","book":"Chapitre 3","questions":[
  ("Le Tanwîn est décrit comme…",["un Noûn Sâkinah supplémentaire prononcé à la liaison","une lettre écrite après chaque mot","une prolongation"],0),
  ("Combien de formes de Tanwîn sont étudiées ?",["Deux","Trois","Quatre"],1),
  ("Lorsqu'on s'arrête à la fin d'un nom portant le Tanwîn, celui-ci…",["se prononce toujours","ne se prononce pas","devient une Chaddah"],1)]},
 {"title":"La Chaddah et les voyelles","video":"La Shadda","book":"Chapitre 4","questions":[
  ("Une lettre Mouchaddadah correspond à…",["une lettre Sâkin suivie de la même lettre voyellisée","deux lettres différentes","une lettre prolongée"],0),
  ("Quelles voyelles sont associées à la Chaddah dans ce chapitre ?",["Fathah, Kasrah et Dammah","Tanwîn uniquement","Soukoûn uniquement"],0),
  ("Peut-on prononcer isolément une lettre Mouchaddadah selon l'explication du livre ?",["Oui, toujours","Non, elle est lue avec la lettre qui la précède","Seulement à la fin d'une phrase"],1)]},
 {"title":"Récapitulatif : Chaddah et Tanwîn","video":"Récapitulatif sur la Shadda et le Tanwin","book":"Chapitre 5","questions":[
  ("Le chapitre 5 associe la Chaddah à…",["la Soukoûn seulement","les trois formes du Tanwîn","la Hamzatou-l-Wasl"],1),
  ("Quelles formes de Tanwîn sont reprises avec la Chaddah ?",["Deux Fathah, deux Kasrah et deux Dammah","Fathah seulement","Kasrah et Soukoûn"],0),
  ("Le livre prévoit aussi une leçon sur…",["les nombres","les mots contenant deux lettres Mouchaddadah successives","le Lâm lunaire"],1)]},
 {"title":"La Hamzatou-l-Qat‘ et la Hamzatou-l-Wasl","video":"La Hamza","book":"Chapitre 6","questions":[
  ("La Hamzatou-l-Qat‘…",["se prononce au début du mot","ne se prononce jamais","n'a jamais de voyelle"],0),
  ("La Hamzatou-l-Wasl précédée d'un mot lors de la liaison…",["se prononce toujours","ne se prononce pas","devient un Tanwîn"],1),
  ("Quel test le livre propose-t-il pour les distinguer ?",["ajouter la lettre Wâw avant le mot et écouter la Hamzah","compter les lettres","remplacer la Hamzah par un Alif"],0)]},
 {"title":"La prolongation naturelle","video":"Les prolongations courtes","book":"Chapitre 7","questions":[
  ("Quelles sont les trois lettres de prolongation naturelle ?",["ا – و – ي","ب – ت – ث","س – ش – ص"],0),
  ("Le Alif est une prolongation naturelle lorsqu'il est précédé de…",["Kasrah","Fathah","Dammah"],1),
  ("Les lettres de prolongation naturelle portent-elles une voyelle ?",["Oui, une Fathah","Non, elles sont Sâkinah","Elles portent toujours une Chaddah"],1)]},
 {"title":"Le Alif après le Wâw Al-Jamâ‘ah","video":"Le Alif après Waw Jama3a","book":"Chapitre 8","questions":[
  ("Où se trouve le Alif étudié ?",["Au début du nom","À la fin du verbe après le Wâw Al-Jamâ‘ah","Après chaque lettre Wâw"],1),
  ("Ce Alif final…",["s'écrit et se prononce","s'écrit mais ne se prononce pas","ne s'écrit jamais"],1),
  ("Selon le livre, il indique que le Wâw désigne…",["le pluriel","une prolongation","une Hamzah"],0)]},
 {"title":"Le Tâ Marboutah","video":"Le Tè Marbouta","book":"Chapitre 9","questions":[
  ("Le Tâ Marboutah se trouve généralement…",["au début du mot","à la fin du mot","au milieu uniquement"],1),
  ("Quelle écriture correspond au Tâ Marboutah ?",["ة – ـة","ا – ى","و – ي"],0),
  ("Le chapitre apprend à lire le Tâ Marboutah…",["seulement isolé","en liaison et à l'arrêt","uniquement avec une Chaddah"],1)]},
 {"title":"Le Lâm lunaire et le Lâm solaire","video":"Le Lèm lunaire et solaire","book":"Chapitre 10","questions":[
  ("Le Lâm lunaire…",["s'écrit et se lit","s'écrit mais ne se lit pas","ne s'écrit pas"],0),
  ("Le Lâm solaire…",["se lit toujours","s'écrit mais ne se lit pas","est une lettre de prolongation"],1),
  ("Quel test est proposé pour les distinguer ?",["placer un Wâw avant le mot et vérifier si le Lâm se prononce","ajouter une Fathah","supprimer le début du mot"],0)]},
 {"title":"Exercices récapitulatifs : lecture","video":"Exercices récapitulatifs","book":"Chapitre 11","questions":[
  ("Le chapitre de lecture progresse notamment de…",["mots vers phrases puis texte","texte vers alphabet","nombres vers lettres"],0),
  ("Le livre prévoit des exemples de lecture avec…",["deux, trois et quatre mots, puis une phrase et un texte","uniquement des lettres isolées","uniquement des nombres"],0),
  ("Pour lire un exemple de plusieurs mots, l'élève doit…",["relier progressivement les mots puis lire l'ensemble","lire seulement le premier mot","ignorer les voyelles"],0)]},
 {"title":"Termes et règles spécifiques au Coran","video":"Termes et règles spécifiques au Coran","book":"Chapitre 12","questions":[
  ("Le chapitre 12 porte sur…",["les écritures spécifiques au Moushaf","les nombres de 0 à 20","les lettres de l'alphabet seulement"],0),
  ("L'écriture ‘Outhmânî du Moushaf peut différer…",["de l'écriture contemporaine","de la langue arabe","du sens de chaque mot"],0),
  ("Un petit signe placé au-dessus d'une grande lettre peut indiquer…",["qu'il faut lire la petite lettre","qu'il faut toujours doubler la lettre","qu'il faut supprimer le mot"],0)]}
]

# Deux questions supplémentaires par chapitre : 5 questions permettent
# d'appliquer réellement le seuil de validation de 80 %.
EXTRA_QUESTIONS = [
 [("Combien de formes différentes d'une lettre le livre invite-t-il à reconnaître ?",["Une seule","Plusieurs selon sa position","Aucune"],1),
  ("Quel est l'objectif général du premier chapitre ?",["Reconnaître et lire les lettres","Apprendre les nombres","Étudier uniquement le Tanwîn"],0)],
 [("Quelle voyelle est présentée en premier dans la progression du livre ?",["La Fathah","La Dammah","La Kasrah"],0),
  ("La Soukoûn est étudiée dans le même chapitre que…",["les lettres avec voyelles","les nombres","le Tâ Marboutah"],0)],
 [("Les deux Fathah sont placées…",["au-dessus de la dernière lettre","sous la première lettre","après le mot"],0),
  ("Le Tanwîn des deux Kasrah se place…",["au-dessus de la lettre","en-dessous de la dernière lettre","sur le Alif initial"],1)],
 [("La Chaddah avec la Kasrah se reconnaît par…",["une Kasrah associée à la Chaddah","deux Fathah","un Alif muet"],0),
  ("Le chapitre 4 entraîne à lire la Chaddah avec…",["les voyelles","les nombres","le Lâm solaire seulement"],0)],
 [("Le chapitre 5 reprend la Chaddah avec…",["les deux Fathah, Kasrah et Dammah","la Hamzatou-l-Wasl uniquement","les prolongations uniquement"],0),
  ("Que faire lorsque deux lettres Mouchaddadah se suivent dans un mot ?",["Suivre les étapes de lecture progressives indiquées","Ignorer la première","Lire seulement la dernière"],0)],
 [("La Hamzatou-l-Qat‘ est écrite…",["au-dessus ou en dessous du Alif","uniquement après le Wâw","sans jamais de voyelle"],0),
  ("La Hamzatou-l-Wasl se prononce-t-elle quand elle est reliée au mot précédent ?",["Oui","Non"],1)],
 [("Le Wâw est une lettre de prolongation quand il est précédé d'une…",["Dammah","Fathah","Kasrah"],0),
  ("Le Yâ est une lettre de prolongation quand il est précédé d'une…",["Fathah","Kasrah","Dammah"],1)],
 [("Dans l'exemple du livre, le Alif après le Wâw Al-Jamâ‘ah se trouve dans…",["صَلُّوا","أَرْجُو","بِي"],0),
  ("Ce Alif final sert à indiquer…",["que le Wâw désigne le pluriel","une Chaddah","une voyelle courte"],0)],
 [("Le Tâ Marboutah ressemble en fin de mot à…",["un Hâ avec deux points","un Alif","un Wâw"],0),
  ("À l'arrêt sur le Tâ Marboutah, le livre distingue la lecture de…",["la liaison","la pause","la prolongation naturelle"],1)],
 [("Pour le Lâm solaire, la lettre Lâm…",["est prononcée","est écrite mais non prononcée","est supprimée à l'écrit"],1),
  ("Le Lâm lunaire ou solaire est lié au début du mot avec…",["Hamzatou-l-Wasl","Tanwîn","Alif après Wâw"],0)],
 [("Combien de leçons de lecture sont indiquées dans ce chapitre ?",["Deux","Cinq","Dix"],1),
  ("La progression du chapitre aboutit à la lecture…",["d'un texte","d'une lettre isolée seulement","des nombres"],0)],
 [("Le livre distingue l'écriture ‘Outhmânî de…",["l'écriture contemporaine","l'alphabet latin","la prononciation française"],0),
  ("Un cercle au-dessus de certaines lettres dites malades indique…",["qu'il ne faut pas les lire","qu'il faut les doubler","qu'il faut les prolonger"],0)]
]
for lesson, extras in zip(LESSONS, EXTRA_QUESTIONS):
    lesson["questions"].extend(extras)

BASE = """
<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Parcours Al Madaniyya</title>
<style>
:root{--green:#176b50;--pale:#edf6f1;--ink:#18332a;--muted:#61736b;--gold:#e4b95b}
*{box-sizing:border-box}body{margin:0;background:#f5f7f5;color:var(--ink);font:16px/1.5 Arial,sans-serif}
header{background:var(--green);color:white;padding:18px max(20px,calc((100% - 1050px)/2));display:flex;justify-content:space-between;gap:16px;align-items:center}
header a{color:white;text-decoration:none}main{max-width:1050px;margin:28px auto;padding:0 18px}.card{background:white;border:1px solid #e1e9e4;border-radius:16px;padding:22px;margin:14px 0;box-shadow:0 4px 18px #173b2810}
h1,h2,h3{line-height:1.2}h1{font-size:30px}h2{font-size:22px}.muted{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}
input,button{font:inherit;padding:11px 13px;border-radius:9px;border:1px solid #cbd8d0}input{width:100%;margin:5px 0 13px}
button,.btn{background:var(--green);color:white;border:0;cursor:pointer;text-decoration:none;display:inline-block;padding:11px 16px;border-radius:9px}
.btn.secondary,button.secondary{background:#e9f1ec;color:var(--green)}button:disabled{opacity:.45;cursor:not-allowed}
.progress{height:10px;background:#e7eee9;border-radius:20px;overflow:hidden}.progress span{display:block;height:100%;background:var(--green)}
.tag{display:inline-block;padding:4px 9px;border-radius:20px;background:var(--pale);color:var(--green);font-size:13px}
.lock{opacity:.58}.question{padding:14px 0;border-top:1px solid #e8eee9}.option{display:block;margin:8px 0}.option input{width:auto;margin:0 8px 0 0}
iframe{width:100%;aspect-ratio:16/9;border:0;border-radius:12px}.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}.right{margin-left:auto}
table{border-collapse:collapse;width:100%}td,th{padding:10px;border-bottom:1px solid #e5ece7;text-align:left;vertical-align:top}
.notice{background:#fff7df;border-left:4px solid var(--gold);padding:12px 15px;border-radius:8px}
@media(max-width:600px){header{padding:14px 16px}h1{font-size:25px}main{margin:18px auto}}
</style></head><body>
<header><strong>☘ Al Madaniyya · Apprendre à lire l'arabe</strong>
{% if user %}<span>{{ user.display_name }} · <a href="{{ url_for('logout') }}">Déconnexion</a></span>{% endif %}</header>
<main>
{% with messages=get_flashed_messages(with_categories=true) %}{% for cat,msg in messages %}<div class="card">{{ msg }}</div>{% endfor %}{% endwith %}
{{ body|safe }}
</main></body></html>
"""

def db():
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row
    return c

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
          display_name TEXT NOT NULL, password_hash TEXT NOT NULL,
          role TEXT NOT NULL CHECK(role IN ('teacher','student')),
          must_change_password INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS progress(
          student_id INTEGER NOT NULL, lesson_index INTEGER NOT NULL,
          best_score INTEGER NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0,
          validated INTEGER NOT NULL DEFAULT 0, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY(student_id,lesson_index), FOREIGN KEY(student_id) REFERENCES users(id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS attempts(
          id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
          lesson_index INTEGER NOT NULL, score INTEGER NOT NULL,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

def current_user():
    uid=session.get("uid")
    if not uid:return None
    with db() as c:return c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()

def page(body, **ctx):
    return render_template_string(BASE,body=render_template_string(body,**ctx),user=current_user())

def login_required(fn):
    @wraps(fn)
    def w(*a,**kw):
        if not current_user():return redirect(url_for("login"))
        return fn(*a,**kw)
    return w

def teacher_required(fn):
    @wraps(fn)
    def w(*a,**kw):
        u=current_user()
        if not u:return redirect(url_for("login"))
        if u["role"]!="teacher":abort(403)
        return fn(*a,**kw)
    return w

def csrf():
    if "csrf" not in session:session["csrf"]=secrets.token_urlsafe(24)
    if request.method=="POST":
        if not secrets.compare_digest(session.get("csrf",""),request.form.get("csrf","")):abort(400)
@app.before_request
def protect():csrf()

@app.route("/")
def home():return redirect(url_for("dashboard") if current_user() else url_for("login"))

@app.route("/connexion",methods=["GET","POST"])
def login():
    if request.method=="POST":
        with db() as c:u=c.execute("SELECT * FROM users WHERE username=?",(request.form.get("username","").strip().lower(),)).fetchone()
        if u and check_password_hash(u["password_hash"],request.form.get("password","")):
            session.clear();session["uid"]=u["id"];session["csrf"]=secrets.token_urlsafe(24)
            return redirect(url_for("change_password") if u["must_change_password"] else url_for("dashboard"))
        flash("Identifiant ou mot de passe incorrect.")
    return page("""<div class="card" style="max-width:460px;margin:40px auto"><h1>Connexion</h1><p class="muted">Accès professeur ou élève</p>
    <form method="post"><input type="hidden" name="csrf" value="{{session.csrf}}">
    <label>Identifiant</label><input name="username" required autocomplete="username">
    <label>Mot de passe</label><input type="password" name="password" required autocomplete="current-password">
    <button>Se connecter</button></form>
    {% if setup %}<p><a href="{{url_for('setup')}}">Créer le compte professeur initial</a></p>{% endif %}</div>""",
    setup=teacher_count()==0)

def teacher_count():
    with db() as c:return c.execute("SELECT COUNT(*) n FROM users WHERE role='teacher'").fetchone()["n"]

@app.route("/premier-demarrage",methods=["GET","POST"])
def setup():
    if teacher_count():return redirect(url_for("login"))
    if request.method=="POST":
        username=request.form.get("username","professeur").strip().lower()
        name=request.form.get("display_name","Professeur").strip()
        password=request.form.get("password","")
        if len(password)<12:flash("Le mot de passe doit contenir au moins 12 caractères.")
        elif not username or not name:flash("Complète tous les champs.")
        else:
            with db() as c:c.execute("INSERT INTO users(username,display_name,password_hash,role) VALUES(?,?,?,'teacher')",(username,name,generate_password_hash(password)))
            flash("Compte professeur créé. Connecte-toi.")
            return redirect(url_for("login"))
    return page("""<div class="card" style="max-width:520px;margin:auto"><h1>Premier démarrage</h1><p>Crée ton compte professeur. Choisis un mot de passe d'au moins 12 caractères.</p>
    <form method="post"><input type="hidden" name="csrf" value="{{session.csrf}}">
    <label>Identifiant</label><input name="username" value="professeur" required>
    <label>Nom affiché</label><input name="display_name" value="Professeur" required>
    <label>Mot de passe</label><input type="password" name="password" minlength="12" required>
    <button>Créer mon compte professeur</button></form></div>""")

@app.route("/deconnexion")
@login_required
def logout():session.clear();return redirect(url_for("login"))

def progress_for(uid):
    with db() as c:rows=c.execute("SELECT * FROM progress WHERE student_id=?",(uid,)).fetchall()
    return {r["lesson_index"]:r for r in rows}

@app.route("/tableau-de-bord")
@login_required
def dashboard():
    u=current_user()
    if u["must_change_password"]:return redirect(url_for("change_password"))
    if u["role"]=="teacher":return redirect(url_for("teacher"))
    prog=progress_for(u["id"])
    unlocked=0
    while unlocked<len(LESSONS) and prog.get(unlocked) and prog[unlocked]["validated"]:unlocked+=1
    cards=""
    for i,l in enumerate(LESSONS):
        p=prog.get(i);done=bool(p and p["validated"]);available=i<=unlocked
        status="Validé" if done else ("À commencer" if available else "Verrouillé")
        cards+=f"""<div class="card {'lock' if not available else ''}"><div class="row"><span class="tag">Chapitre {i+1}</span><span class="right muted">{status}</span></div>
        <h2>{l['title']}</h2><p class="muted">{l['book']} · vidéo : {l['video']}</p>
        {f'<div class="progress"><span style="width:{p["best_score"]}%"></span></div><p>Meilleur score : {p["best_score"]}%</p>' if p else ''}
        {f'<a class="btn" href="{url_for("lesson",idx=i)}">Ouvrir le chapitre</a>' if available else '<span class="muted">Réussis le chapitre précédent pour débloquer celui-ci.</span>'}</div>"""
    return page(f"""<div class="card"><h1>Bonjour {u['display_name']} !</h1><p>Avance à ton rythme : regarde la vidéo, révise la leçon et passe le QCM.</p>
    <div class="notice">Pour valider un chapitre, il faut obtenir au moins <b>80 %</b> au QCM. Le chapitre suivant se débloque automatiquement.</div></div>
    <h2>Ton parcours · 12 étapes</h2><div class="grid">{cards}</div>""")

@app.route("/chapitre/<int:idx>",methods=["GET","POST"])
@login_required
def lesson(idx):
    u=current_user()
    if u["role"]!="student":return redirect(url_for("teacher"))
    if not 0<=idx<len(LESSONS):abort(404)
    prog=progress_for(u["id"]);unlocked=0
    while unlocked<len(LESSONS) and prog.get(unlocked) and prog[unlocked]["validated"]:unlocked+=1
    if idx>unlocked:abort(403)
    l=LESSONS[idx];result=None
    if request.method=="POST":
        score=0
        for qi,q in enumerate(l["questions"]):
            if request.form.get(f"q{qi}")==str(q[2]):score+=1
        score=round(score/len(l["questions"])*100)
        validated=score>=80
        with db() as c:
            old=c.execute("SELECT * FROM progress WHERE student_id=? AND lesson_index=?",(u["id"],idx)).fetchone()
            best=max(score,old["best_score"] if old else 0)
            was_done=bool(old and old["validated"])
            c.execute("""INSERT INTO progress(student_id,lesson_index,best_score,attempts,validated,updated_at)
            VALUES(?,?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(student_id,lesson_index) DO UPDATE SET
            best_score=MAX(best_score,excluded.best_score),attempts=attempts+1,
            validated=MAX(validated,excluded.validated),updated_at=CURRENT_TIMESTAMP""",
            (u["id"],idx,score,1,1 if validated else 0))
            c.execute("INSERT INTO attempts(student_id,lesson_index,score) VALUES(?,?,?)",(u["id"],idx,score))
        result=(score,validated or was_done)
    questions=""
    for qi,(prompt,opts,correct) in enumerate(l["questions"]):
        options="".join(f'<label class="option"><input type="radio" name="q{qi}" value="{oi}" required> {opt}</label>' for oi,opt in enumerate(opts))
        questions+=f'<div class="question"><b>{qi+1}. {prompt}</b>{options}</div>'
    result_html=""
    if result:
        score,done=result
        result_html=f'<div class="card"><h2>Résultat : {score} %</h2><p>{"Chapitre validé ! Le suivant est débloqué." if done else "Il faut au moins 80 %. Relis la leçon et réessaie."}</p><a class="btn" href="{url_for("dashboard")}">Retour au parcours</a></div>'
    return page(f"""<p><a href="{url_for('dashboard')}">← Mon parcours</a></p><div class="card"><span class="tag">Chapitre {idx+1} · {l['book']}</span><h1>{l['title']}</h1>
    <p>Regarde la vidéo explicative de la playlist, puis réponds au QCM.</p>
    <iframe src="https://www.youtube-nocookie.com/embed/videoseries?list=PL35d5prLj5n_ulpItCWJnlhHVcakcv4iR" title="Playlist Al Madaniyya" allowfullscreen></iframe>
    <p><a href="{PLAYLIST}" target="_blank" rel="noopener">Ouvrir la playlist YouTube</a></p></div>
    <div class="card"><h2>QCM de validation</h2><p class="muted">3 questions · 80 % minimum</p>
    <form method="post"><input type="hidden" name="csrf" value="{{session.csrf}}">{questions}<button>Valider mes réponses</button></form></div>{result_html}""",questions=questions,result_html=result_html)

@app.route("/mot-de-passe",methods=["GET","POST"])
@login_required
def change_password():
    u=current_user()
    if request.method=="POST":
        new=request.form.get("new_password","")
        if len(new)<12:flash("Choisis au moins 12 caractères.")
        else:
            with db() as c:c.execute("UPDATE users SET password_hash=?,must_change_password=0 WHERE id=?",(generate_password_hash(new),u["id"]))
            flash("Mot de passe modifié.");return redirect(url_for("dashboard"))
    return page("""<div class="card" style="max-width:500px;margin:auto"><h1>Changer le mot de passe</h1>
    <form method="post"><input type="hidden" name="csrf" value="{{session.csrf}}"><label>Nouveau mot de passe (12 caractères minimum)</label>
    <input type="password" name="new_password" minlength="12" required><button>Enregistrer</button></form></div>""")

@app.route("/professeur",methods=["GET","POST"])
@teacher_required
def teacher():
    if request.method=="POST":
        username=request.form.get("username","").strip().lower();name=request.form.get("display_name","").strip()
        if not username or not name:flash("Identifiant et nom obligatoires.")
        else:
            temp=secrets.token_urlsafe(8)
            try:
                with db() as c:c.execute("INSERT INTO users(username,display_name,password_hash,role,must_change_password) VALUES(?,?,?,'student',1)",(username,name,generate_password_hash(temp)))
                session["new_creds"]={"username":username,"password":temp}
            except sqlite3.IntegrityError:flash("Cet identifiant existe déjà.")
        return redirect(url_for("teacher"))
    with db() as c:
        students=c.execute("SELECT * FROM users WHERE role='student' ORDER BY display_name").fetchall()
        stats=c.execute("""SELECT student_id,COUNT(*) total,SUM(validated) done,MAX(updated_at) updated FROM progress GROUP BY student_id""").fetchall()
    sm={s["student_id"]:s for s in stats}
    rows="".join(f'<tr><td>{s["display_name"]}<br><span class="muted">{s["username"]}</span></td><td>{sm[s["id"]]["done"] if s["id"] in sm else 0} / 12</td><td>{sm[s["id"]]["updated"] if s["id"] in sm else "Pas encore commencé"}</td></tr>' for s in students)
    creds=session.pop("new_creds",None)
    creds_html=f'<div class="notice"><b>Compte élève créé</b><br>Identifiant : {creds["username"]}<br>Mot de passe temporaire : <code>{creds["password"]}</code><br>Transmets ces informations en privé à l’élève.</div>' if creds else ""
    return page(f"""<div class="card"><h1>Espace professeur</h1><p>Crée les comptes élèves et suis leurs validations.</p>{creds_html}</div>
    <div class="card"><h2>Créer un compte élève</h2><form method="post"><input type="hidden" name="csrf" value="{{{{session.csrf}}}}">
    <label>Nom de l'élève</label><input name="display_name" required><label>Identifiant de connexion</label><input name="username" required>
    <button>Créer le compte</button></form></div>
    <div class="card"><h2>Suivi de la classe</h2><table><tr><th>Élève</th><th>Chapitres validés</th><th>Dernière activité</th></tr>{rows or '<tr><td colspan="3">Aucun élève pour le moment.</td></tr>'}</table></div>""")

@app.route("/sante")
def health():return {"status":"ok"}

init_db()
if __name__=="__main__":
    app.run(host="127.0.0.1",port=int(os.environ.get("PORT",5000)),debug=False)
