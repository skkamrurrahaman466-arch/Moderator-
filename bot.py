# =====================================================================
# PART 1 OF 2 — PASTE THIS FIRST AT LINE 1 OF YOUR GITHUB FILE
# CHICAGO CROSSFIRE — COMBINED MANAGEMENT HUB BOT (24/7 SINGLE FILE)
#   1. Simple Phase Requests (Name: @user / Phase: 1-5 / @Bot)
#   2. Manager, Senior Manager, Head Manager & Chief Manager Trials
#   3. Management Support Tickets (Claim, Escalate, DM Transcript & On-Call)
# Requirements: discord.py, aiohttp | Env Var: BOT_TOKEN
# =====================================================================
import asyncio, datetime, io, json, os, re, time, aiohttp
from aiohttp import web
import discord
from discord.ext import commands

TOKEN = os.getenv("BOT_TOKEN", "").strip().strip('"').strip("'")
DB_FILE = "management_hub_db.json"
START, STATUS = time.time(), "Starting..."
ACTIVE_TRIALS: dict[int, dict] = {}

# --- 1. PHASE INTROS, MANAGEMENT TRIALS & SUPPORT CATEGORIES ---
PHASE_INTROS = {
    "phase1": ("🎫 Phase 1 — Ticket Response Oversight", "Respond to real player tickets cleanly. Ask for Roblox username & proof, stay respectful, and avoid lazy short replies.", discord.Color.blue()),
    "phase2": ("👁️ Phase 2 — Chat Surveillance & Moderation", "Monitor public chat calmly. De-escalate drama in 1–2 neutral sentences, cite exact rules, and log every moderation action.", discord.Color.gold()),
    "phase3": ("🔎 Phase 3 — Forensics & Hybrid Operations", "Handle high-stakes reports, reject cropped 4s clips, verify Gamepass claims, and moderate public chat simultaneously.", discord.Color.orange()),
    "phase4": ("⚡ Phase 4 — Under-Fire Stress Ambush", "Prove zero bias and fast judgment under raids, friend-traps, doctored screenshots, and hostile appeals.", discord.Color.red()),
    "phase5": ("🏛️ Phase 5 — Final High Command Board", "Final review of Phases 1–4. Defend your record and prove you deserve permanent clearance.", discord.Color.purple()),
}

# key: (Title, Pass%, MinWords, Color, Intro, [(Question, [expected_keywords]), ...])
TRIALS = {
    "manager": (
        "Manager Trial", 80, 18, discord.Color.blue(),
        "Welcome to the **Manager Trial**! Prove you can lead day-to-day staff operations, handle escalations fairly, and keep support active.",
        [
            ("Two moderators argue publicly in #general over a punishment while players watch. Give your exact steps to stop the drama and resolve it privately.", ["private", "staff", "calm", "stop", "log", "professional"]),
            ("A staff member keeps claiming tickets and closing them with 2-word answers to farm stats. How do you verify this and handle it fairly?", ["transcript", "audit", "warn", "coach", "evidence", "quality"]),
            ("Tickets are piling up during peak hours and half the mods are AFK. What exact steps do you take in the next 10 minutes?", ["oncall", "ping", "claim", "delegate", "active", "priorit"]),
        ],
    ),
    "senior": (
        "Senior Manager Trial", 85, 22, discord.Color.teal(),
        "Welcome to the **Senior Manager Trial**! You are tested on overseeing Managers, catching bias, and resolving high-stakes disputes.",
        [
            ("A Manager promotes their close friend who failed Phase 3 and skipped logs. Detail your exact investigation, reversal, and disciplinary steps.", ["audit", "log", "bias", "demote", "evidence", "escalate", "chief"]),
            ("A player opens an URGENT ticket claiming a Staff member threatened them in DMs with screenshots. How do you authenticate proof before acting?", ["id", "inspect", "verify", "context", "suspend", "impersonat", "proof"]),
            ("Staff activity drops by 50% in one week due to burnout and boring shifts. Outline a concrete 7-day recovery plan you would run.", ["schedule", "loa", "quota", "recruit", "motivat", "shift", "check"]),
            ("A rival server sends 15 members to mass-report and bait your Managers into breaking rules. How do you brief and protect your team?", ["calm", "bait", "log", "lock", "slowmode", "evidence", "ban"]),
        ],
    ),
    "head": (
        "Head Manager Trial", 88, 25, discord.Color.orange(),
        "Welcome to the **Head Manager Trial**! You command Management divisions, enforce zero-corruption standards, and protect server stability.",
        [
            ("A Senior Manager's account is compromised and starts editing channels and stripping roles. List your exact first 5 containment actions in order.", ["strip", "ban", "role", "audit", "lock", "pause", "alert"]),
            ("Developers and Management blame each other for delayed bug fixes and angry players. Design a strict SLA & escalation workflow to end friction.", ["sla", "triage", "dev", "boundary", "ticket", "verify", "accountab"]),
            ("Design a fair, tamper-proof Promotion & Strike Decay system for Manager -> Senior Manager so favoritism is impossible.", ["metric", "audit", "transcript", "objective", "threshold", "decay", "log"]),
            ("A top Donor/Booster breaks rules repeatedly and threatens to pull all boosts if punished. State your decision, evidence steps, and public stance.", ["ban", "equal", "bias", "proof", "credib", "rule"]),
        ],
    ),
    "chief": (
        "Chief Manager Trial — HELL MODE", 92, 35, discord.Color.dark_red(),
        "Welcome to **HELL MODE — The Chief Manager Executive Trial**! You are vetted for the highest Management authority beneath Ownership & Developers. Zero mercy.",
        [
            ("3-FRONT CRISIS (Owner offline): Simultaneously a Head Manager leaks staff chats, 30 raid bots spam NSFW in #general, and tickets flood with an exploit. Give your minute-by-minute Command Protocol.", ["strip", "ban", "pause", "invite", "lock", "dev", "audit", "delegate", "statement"]),
            ("CORRUPTION RING: Proof shows a Head Manager + 2 Senior Managers secretly protect a faction and blacklist rivals. Detail covert IA proof gathering, synchronized simultaneous removal, and wrongful-ban recovery.", ["covert", "proof", "audit", "simultaneous", "strip", "retaliat", "unban", "review"]),
            ("40% MANAGEMENT MUTINY: After blacklisting a popular Senior Manager, 6 Managers threaten mass resignation unless you reverse it. Explain why you refuse, emergency coverage, and PR discipline.", ["refuse", "blackmail", "coverage", "calm", "professional", "retain", "drama"]),
            ("ANTI-NUKE & LEAST-PRIVILEGE: Blueprint our Discord Role Hierarchy, Bot/Webhook security rules, mandatory 2FA policy, and weekly Security Audit checklist.", ["hierarchy", "webhook", "administrator", "2fa", "audit", "least", "bot"]),
            ("EXECUTIVE MIRROR: Give (A) your concrete 30-day restructuring roadmap, (B) your single biggest real flaw + safeguard, and (C) 3 failures that justify instant stripping by Ownership.", ["week", "audit", "flaw", "safeguard", "bias", "leak", "strip", "owner"]),
        ],
    ),
}

SUPPORT_CATS = {
    "general": ("Management Support", "mgmt-help", "💬", discord.Color.blurple(), "Describe your question and an On-Call Manager will assist you."),
    "report": ("Staff / Manager Report", "mgmt-report", "🚨", discord.Color.red(), "Provide the user's name, incident details, and screenshot/clip proof."),
    "partner": ("Partnership / Faction Inquiry", "mgmt-partner", "🤝", discord.Color.green(), "Share your server/faction details and inquiry below."),
    "exec": ("Head / Chief Manager Escalation", "mgmt-exec", "👑", discord.Color.gold(), "High-priority executive matter. Explain clearly why Chief/Head Management is needed."),
}


def load_db() -> dict:
    """Loads persisted server configuration and clearance records from JSON."""
    try:
        return json.load(open(DB_FILE, encoding="utf-8")) if os.path.exists(DB_FILE) else {}
    except Exception:
        return {}


def save_db() -> None:
    """Saves server configuration and clearance records safely to JSON."""
    try:
        json.dump(DB, open(DB_FILE, "w", encoding="utf-8"), indent=2)
    except Exception:
        pass


DB = load_db()


def gcfg(gid: int) -> dict:
    return DB.setdefault(str(gid), {"dev_role": 0, "mgmt_role": 0, "chief_role": 0, "log_ch": 0, "cat_id": 0, "oncall": [], "records": {}})


def is_mgmt(m: discord.Member) -> bool:
    """Checks if a user is Management, Chief, Developer, or Admin."""
    if not isinstance(m, discord.Member):
        return False
    if m.guild_permissions.administrator or m.guild_permissions.manage_channels:
        return True
    c = gcfg(m.guild.id)
    rids = {c["dev_role"], c["mgmt_role"], c["chief_role"]} - {0}
    return any(r.id in rids for r in m.roles)


def is_exec(m: discord.Member) -> bool:
    """Checks if a user is Chief Management, Developer, or Admin."""
    if not isinstance(m, discord.Member):
        return False
    if m.guild_permissions.administrator:
        return True
    c = gcfg(m.guild.id)
    rids = {c["dev_role"], c["chief_role"]} - {0}
    return any(r.id in rids for r in m.roles)


# --- 2. 24/7 RENDER KEEP-ALIVE WEB SERVER ---
async def run_web():
    """Starts the aiohttp health server for Render & cron-job.org pings."""
    app = web.Application()
    fn = lambda r: web.Response(text=f"Management Hub Bot 24/7 | Up:{int((time.time()-START)//60)}m | {STATUS}")
    app.router.add_get("/", fn)
    app.router.add_get("/health", fn)
    r = web.AppRunner(app)
    await r.setup()
    await web.TCPSite(r, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()


async def self_ping():
    """Backup keep-alive ping loop."""
    await asyncio.sleep(25)
    url = os.environ.get("RENDER_EXTERNAL_URL") or f"http://127.0.0.1:{os.environ.get('PORT', 10000)}/"
    async with aiohttp.ClientSession() as s:
        while True:
            try:
                async with s.get(url, timeout=10):
                    pass
            except Exception:
                pass
            await asyncio.sleep(240)


# --- 3. TRANSCRIPTS, AUTO-GRADING & TRIAL LAUNCHER ---
async def build_channel_transcript(ch: discord.TextChannel, closer: discord.Member, reason: str) -> bytes:
    """Exports all messages & attachments in a support ticket into a .txt file."""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"=== {ch.guild.name} MANAGEMENT SUPPORT TRANSCRIPT ===", f"Channel: #{ch.name} | Closed By: {closer} | Reason: {reason} | At: {now}\n"]
    async for m in ch.history(limit=None, oldest_first=True):
        ts = m.created_at.strftime("%Y-%m-%d %H:%M")
        lines.append(f"[{ts}] {m.author.display_name}: {m.content}")
        for a in m.attachments:
            lines.append(f"  [File] {a.url}")
    return "\n".join(lines).encode("utf-8")


async def close_support_ticket(i: discord.Interaction, reason: str = "Resolved by Management"):
    """Saves the ticket transcript, DMs the opener, archives to logs, and deletes the channel."""
    ch, g = i.channel, i.guild
    topic = ch.topic or ""
    if not topic.startswith("MgmtTicket |"):
        return await i.response.send_message("❌ Use this inside a Management Support ticket.", ephemeral=True)
    await i.response.send_message(f"📄 Saving transcript & DMing opener... Closing in **5s**.\n> **Reason:** {reason}")
    uid_m = re.search(r"UserID:(\d+)", topic)
    opener_id = int(uid_m.group(1)) if uid_m else None
    raw = await build_channel_transcript(ch, i.user, reason)
    fname = f"transcript-{ch.name}.txt"

    if opener_id:
        try:
            usr = g.get_member(opener_id) or await i.client.fetch_user(opener_id)
            await usr.send(f"📄 **{g.name} — Management Support Transcript (`#{ch.name}`)**\nClosed by **{i.user.display_name}** | Reason: `{reason}`", file=discord.File(io.BytesIO(raw), filename=fname))
        except Exception:
            pass

    log_ch = g.get_channel(gcfg(g.id)["log_ch"])
    if log_ch:
        try:
            await log_ch.send(f"📁 **Support Ticket Closed:** `#{ch.name}` | Opener: {f'<@{opener_id}>' if opener_id else 'Unknown'} | Closed By: {i.user.mention} | Reason: `{reason}`", file=discord.File(io.BytesIO(raw), filename=fname))
        except Exception:
            pass

    await asyncio.sleep(5)
    try:
        await ch.delete(reason=f"Closed by {i.user}: {reason}")
    except Exception:
        pass


def grade_trial(rank_key: str, answers: list[dict]) -> tuple[float, str, list[str], bytes]:
    """Strictly grades a Management Trial and exports a .txt dossier."""
    title, pass_pct, min_w, _, _, qs = TRIALS[rank_key]
    total, breakdown, lines = 0.0, [], [f"=== {title.upper()} DOSSIER ==="]
    for idx, ans in enumerate(answers):
        txt, low, words = ans["text"], ans["text"].lower(), len(ans["text"].split())
        keys = qs[idx][1]
        hits = sum(1 for k in keys if k in low)
        pts = round((min(1.0, hits / max(1, min(len(keys), 4))) * 6.0) + (min(1.0, words / max(min_w * 1.4, 25)) * 4.0), 1)
        if words >= 80 and ans["sec"] < 6:
            pts = max(0.0, pts - 2.0)
            breakdown.append(f"Q{idx+1}: {pts}/10 ⚠️ Fast paste ({words}w in {ans['sec']:.1f}s)")
        else:
            breakdown.append(f"Q{idx+1}: {pts}/10 ({hits}/{len(keys)} key points, {words}w)")
        total += pts
        lines.extend([f"\nQ{idx+1}: {qs[idx][0]}", f"ANSWER ({words}w, {int(ans['sec'])}s): {txt}", f"SCORE: {pts}/10"])
    pct = round((total / (len(qs) * 10.0)) * 100, 1)
    verdict = "PASS" if pct >= pass_pct else ("BORDERLINE / ORAL BOARD" if pct >= pass_pct - 8 else "FAIL")
    lines.insert(1, f"Final Score: {pct}% (Pass: {pass_pct}%) | Verdict: {verdict}\n")
    return pct, verdict, breakdown, "\n".join(lines).encode("utf-8")


async def start_management_trial(g: discord.Guild, u: discord.Member, rank_key: str) -> str:
    """Opens a private Management Trial room, posts Starting Intro with Avatar & asks Q1."""
    for cid, s in ACTIVE_TRIALS.items():
        if s["guild_id"] == g.id and s["user_id"] == u.id:
            return f"⚠️ {u.mention} already has an active trial in <#{cid}>!"

    c = gcfg(g.id)
    title, pass_pct, min_w, col, intro, qs = TRIALS[rank_key]
    cat = g.get_channel(c["cat_id"])
    cat = cat if isinstance(cat, discord.CategoryChannel) else None
    ow = {
        g.default_role: discord.PermissionOverwrite(view_channel=False),
        u: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        g.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, read_message_history=True),
    }
    for rid in (c["dev_role"], c["chief_role"]):
        role = g.get_role(rid)
        if role:
            ow[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

    safe = re.sub(r"[^a-z0-9-]", "", u.name.lower())[:14] or "user"
    try:
        tch = await g.create_text_channel(name=f"trial-{rank_key}-{safe}", category=cat, overwrites=ow, topic=f"MgmtTrial | Key:{rank_key} | UserID:{u.id}")
    except discord.Forbidden:
        return "❌ Bot needs **Manage Channels** permission!"

    ACTIVE_TRIALS[tch.id] = {"guild_id": g.id, "user_id": u.id, "rank_key": rank_key, "q_idx": 0, "answers": [], "q_start": time.time(), "warnings": 0}

    emb = discord.Embed(title=f"🔥 {title.upper()} — STARTING INTRODUCTION", description=f"👤 **Candidate:** {u.mention} (`{u.display_name}`)\n📋 **Questions:** `{len(qs)}` • ✍️ **Min:** `{min_w} words` • ✅ **Pass:** `{pass_pct}%`\n\n{intro}", color=col, timestamp=discord.utils.utcnow())
    emb.set_author(name=f"Chicago Crossfire Management Trials — {u.display_name}", icon_url=u.display_avatar.url)
    emb.set_thumbnail(url=u.display_avatar.url)
    emb.set_footer(text="Type 'cancel' anytime to forfeit • Report goes straight to Developers & Chief Management")
    await tch.send(content=u.mention, embed=emb)

    q_emb = discord.Embed(title=f"📝 Question 1 of {len(qs)} — {title}", description=f"**{qs[0][0]}**", color=col)
    q_emb.set_footer(text=f"Minimum {min_w} words required")
    await tch.send(embed=q_emb)
    return f"✅ **{title}** started for {u.mention}! Head into {tch.mention}."
