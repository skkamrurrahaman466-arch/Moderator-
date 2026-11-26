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

# =====================================================================
# PART 2 OF 2 — PASTE DIRECTLY BELOW PART 1 (AT THE FAR LEFT EDGE)
# =====================================================================
class VerdictView(discord.ui.View):
    """1-tap Developer / Chief Manager verdict buttons for Phase Requests & Trials."""

    def __init__(self):
        super().__init__(timeout=None)

    def _meta(self, emb: discord.Embed):
        ft = (emb.footer.text if emb and emb.footer else "") or ""
        km, um = re.search(r"Track:([a-z0-9]+)", ft), re.search(r"UserID:(\d+)", ft)
        return (km.group(1) if km else "phase"), (int(um.group(1)) if um else 0)

    async def _act(self, i: discord.Interaction, label: str, col: discord.Color, passed: bool):
        if not is_exec(i.user):
            return await i.response.send_message("❌ Developers / Chief Management / Admins only.", ephemeral=True)
        emb = i.message.embeds[0]
        track, uid = self._meta(emb)
        if passed and uid:
            rec = gcfg(i.guild.id)["records"].setdefault(str(uid), [])
            if track not in rec:
                rec.append(track)
                save_db()
        for child in self.children:
            child.disabled = True
        emb.color = col
        emb.add_field(name="🏛️ Official Decision", value=f"**{label}** by {i.user.mention}", inline=False)
        await i.response.edit_message(embed=emb, view=self)
        if uid:
            try:
                usr = i.guild.get_member(uid) or await i.client.fetch_user(uid)
                await usr.send(f"🔥 **{i.guild.name} — Result for `{track.upper()}`:** {label} (Reviewed by {i.user.display_name})")
            except Exception:
                pass

    @discord.ui.button(label="Approve / Pass", style=discord.ButtonStyle.success, emoji="✅", custom_id="mhv:pass")
    async def b_pass(self, i: discord.Interaction, b: discord.ui.Button):
        await self._act(i, "✅ APPROVED / PASSED", discord.Color.green(), True)

    @discord.ui.button(label="Oral Board", style=discord.ButtonStyle.primary, emoji="🎙️", custom_id="mhv:oral")
    async def b_oral(self, i: discord.Interaction, b: discord.ui.Button):
        await self._act(i, "🎙️ ORAL BOARD REQUIRED", discord.Color.gold(), False)

    @discord.ui.button(label="Fail", style=discord.ButtonStyle.danger, emoji="❌", custom_id="mhv:fail")
    async def b_fail(self, i: discord.Interaction, b: discord.ui.Button):
        await self._act(i, "❌ FAILED", discord.Color.dark_red(), False)


class TrialSelect(discord.ui.Select):
    """Dropdown for Manager, Senior Manager, Head Manager & Chief Manager Trials."""

    def __init__(self):
        opts = [
            discord.SelectOption(label="Manager Trial (3Q)", value="manager", emoji="📋", description="Pass: 80% • Day-to-day staff leadership"),
            discord.SelectOption(label="Senior Manager Trial (4Q)", value="senior", emoji="⭐", description="Pass: 85% • Overseeing Managers & bias checks"),
            discord.SelectOption(label="Head Manager Trial (4Q)", value="head", emoji="👑", description="Pass: 88% • Division command & crisis defense"),
            discord.SelectOption(label="Chief Manager Trial — HELL MODE (5Q)", value="chief", emoji="🔥", description="Pass: 92% • Brutal executive gauntlet"),
        ]
        super().__init__(placeholder="👑 Choose a Management Trial to Start...", options=opts, custom_id="mht:sel")

    async def callback(self, i: discord.Interaction):
        await i.response.defer(ephemeral=True)
        await i.followup.send(await start_management_trial(i.guild, i.user, self.values[0]), ephemeral=True)


class TrialPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TrialSelect())


class SupportModal(discord.ui.Modal):
    """Intake form for Management Support tickets."""

    def __init__(self, key: str):
        title, _, emoji, _, _ = SUPPORT_CATS[key]
        super().__init__(title=f"{emoji} {title}"[:45])
        self.key = key
        self.rblx = discord.ui.TextInput(label="Roblox Username", required=True, max_length=50)
        self.info = discord.ui.TextInput(label="Details / Evidence", style=discord.TextStyle.paragraph, required=True, max_length=800)
        self.add_item(self.rblx)
        self.add_item(self.info)

    async def on_submit(self, i: discord.Interaction):
        await i.response.defer(ephemeral=True)
        g, u, c = i.guild, i.user, gcfg(i.guild.id)
        title, pfx, emoji, col, tip = SUPPORT_CATS[self.key]
        cat = g.get_channel(c["cat_id"])
        cat = cat if isinstance(cat, discord.CategoryChannel) else None

        ow = {
            g.default_role: discord.PermissionOverwrite(view_channel=False),
            u: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True),
            g.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, read_message_history=True),
        }
        for rid in (c["mgmt_role"], c["chief_role"], c["dev_role"]):
            role = g.get_role(rid)
            if role:
                ow[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        safe = re.sub(r"[^a-z0-9-]", "", u.name.lower())[:14] or "user"
        try:
            tch = await g.create_text_channel(name=f"{pfx}-{safe}", category=cat, overwrites=ow, topic=f"MgmtTicket | Type:{self.key} | UserID:{u.id}")
        except discord.Forbidden:
            return await i.followup.send("❌ Missing **Manage Channels** permission!", ephemeral=True)

        # Smart On-Call Ping: pings On-Call Managers (or Chief role for executive tickets)
        if self.key == "exec" and c["chief_role"]:
            ping = f"<@&{c['chief_role']}>"
        elif c["oncall"]:
            ping = " ".join(f"<@{uid}>" for uid in c["oncall"][:10])
        elif c["mgmt_role"]:
            ping = f"<@&{c['mgmt_role']}>"
        else:
            ping = "**Management**"

        emb = discord.Embed(title=f"{emoji} {title}", description=f"Welcome {u.mention}! {tip}", color=col, timestamp=discord.utils.utcnow())
        emb.set_thumbnail(url=u.display_avatar.url)
        emb.add_field(name="🎮 Roblox User", value=f"`{self.rblx.value}`", inline=True)
        emb.add_field(name="🙋‍♂️ Claimed By", value="*Unclaimed*", inline=True)
        emb.add_field(name="📝 Details", value=self.info.value, inline=False)
        await tch.send(content=f"{u.mention} {ping}", embed=emb, view=TicketCtrlView())
        await i.followup.send(f"✅ Support ticket created: {tch.mention}", ephemeral=True)


class CloseModal(discord.ui.Modal, title="🔒 Close Management Ticket"):
    reason = discord.ui.TextInput(label="Closing Reason", default="Issue resolved", required=True, max_length=250)

    async def on_submit(self, i: discord.Interaction):
        await close_support_ticket(i, self.reason.value)


class TicketCtrlView(discord.ui.View):
    """Persistent Claim, Escalate to Chief & Close buttons inside Management Support tickets."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, emoji="🙋‍♂️", custom_id="mhtc:clm")
    async def b_clm(self, i: discord.Interaction, b: discord.ui.Button):
        if not is_mgmt(i.user):
            return await i.response.send_message("❌ Management only.", ephemeral=True)
        b.disabled, b.label = True, f"Claimed by {i.user.display_name}"[:75]
        emb = i.message.embeds[0] if i.message.embeds else None
        if emb and len(emb.fields) > 1:
            emb.set_field_at(1, name="🙋‍♂️ Claimed By", value=i.user.mention, inline=True)
            await i.response.edit_message(embed=emb, view=self)
        else:
            await i.response.edit_message(view=self)
        await i.channel.send(f"✅ {i.user.mention} has claimed this support ticket!")

    @discord.ui.button(label="Escalate (Chief)", style=discord.ButtonStyle.primary, emoji="⬆️", custom_id="mhtc:esc")
    async def b_esc(self, i: discord.Interaction, b: discord.ui.Button):
        if not is_mgmt(i.user):
            return await i.response.send_message("❌ Management only.", ephemeral=True)
        b.disabled, b.label = True, "Escalated 🔴"
        await i.response.edit_message(view=self)
        cid = gcfg(i.guild.id)["chief_role"]
        await i.channel.send(f"🚨 {f'<@&{cid}>' if cid else '**Chief Management**'} — Ticket escalated by {i.user.mention}!")

    @discord.ui.button(label="Close & DM", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="mhtc:cls")
    async def b_cls(self, i: discord.Interaction, b: discord.ui.Button):
        if not (is_mgmt(i.user) or f"UserID:{i.user.id}" in (i.channel.topic or "")):
            return await i.response.send_message("❌ Management or opener only.", ephemeral=True)
        await i.response.send_modal(CloseModal())


class SupportPanelView(discord.ui.View):
    """4-button Management Support Ticket Center."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Management Support", style=discord.ButtonStyle.primary, emoji="💬", custom_id="mhsp:gen", row=0)
    async def b1(self, i: discord.Interaction, b: discord.ui.Button): await i.response.send_modal(SupportModal("general"))

    @discord.ui.button(label="Staff / Manager Report", style=discord.ButtonStyle.danger, emoji="🚨", custom_id="mhsp:rep", row=0)
    async def b2(self, i: discord.Interaction, b: discord.ui.Button): await i.response.send_modal(SupportModal("report"))

    @discord.ui.button(label="Partnership / Faction", style=discord.ButtonStyle.success, emoji="🤝", custom_id="mhsp:par", row=1)
    async def b3(self, i: discord.Interaction, b: discord.ui.Button): await i.response.send_modal(SupportModal("partner"))

    @discord.ui.button(label="Chief Manager Escalation", style=discord.ButtonStyle.secondary, emoji="👑", custom_id="mhsp:exc", row=1)
    async def b4(self, i: discord.Interaction, b: discord.ui.Button): await i.response.send_modal(SupportModal("exec"))


# --- 5. BOT CORE, CHAT LISTENERS & SLASH COMMANDS ---
class ManagementHubBot(commands.Bot):
    def __init__(self, mi: bool = True):
        it = discord.Intents.default()
        it.message_content = mi
        super().__init__(command_prefix="!", intents=it, help_command=None)
        self._synced = False

    async def setup_hook(self):
        for v in (VerdictView(), TrialPanelView(), SupportPanelView(), TicketCtrlView()):
            self.add_view(v)
        if not self._synced:
            try:
                await self.tree.sync()
                self._synced = True
            except Exception as e:
                print(f"Sync: {e}")

    async def on_ready(self):
        global STATUS
        STATUS = f"ONLINE as {self.user}"
        print(f"✅ Combined Management Hub Bot ONLINE as {self.user}")
        try:
            await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Phases, Trials & Support 🔥"))
        except Exception:
            pass

    async def on_message(self, msg: discord.Message):
        if msg.author.bot or not msg.guild:
            return
        await self.process_commands(msg)

        # 1. Active Management Trial Room Listener
        sess = ACTIVE_TRIALS.get(msg.channel.id)
        if sess and msg.author.id == sess["user_id"]:
            txt = (msg.content or "").strip()
            if not txt:
                return
            if txt.lower() in ("cancel", "quit", "forfeit"):
                ACTIVE_TRIALS.pop(msg.channel.id, None)
                await msg.channel.send("🛑 Trial cancelled. Closing room in 5s...")
                await asyncio.sleep(5)
                try:
                    await msg.channel.delete(reason="Trial cancelled")
                except Exception:
                    pass
                return

            title, pass_pct, min_w, col, _, qs = TRIALS[sess["rank_key"]]
            words = len(txt.split())
            if words < min_w:
                sess["warnings"] += 1
                if sess["warnings"] >= 3:
                    ACTIVE_TRIALS.pop(msg.channel.id, None)
                    await msg.channel.send("❌ **Auto-Failed:** 3x short answers. Closing room in 6s...")
                    await asyncio.sleep(6)
                    try:
                        await msg.channel.delete(reason="Auto-failed short answers")
                    except Exception:
                        pass
                    return
                return await msg.reply(f"⚠️ Too short (`{words}/{min_w}` words). Write a detailed answer *(Warning `{sess['warnings']}/3`)*.")

            sess["answers"].append({"text": txt[:1500], "sec": time.time() - sess["q_start"]})
            sess["q_idx"] += 1
            try:
                await msg.add_reaction("✅")
            except Exception:
                pass

            if sess["q_idx"] < len(qs):
                sess["q_start"] = time.time()
                q_emb = discord.Embed(title=f"📝 Question {sess['q_idx']+1} of {len(qs)} — {title}", description=f"**{qs[sess['q_idx']][0]}**", color=col)
                q_emb.set_footer(text=f"Minimum {min_w} words required")
                return await msg.channel.send(embed=q_emb)

            ACTIVE_TRIALS.pop(msg.channel.id, None)
            pct, verdict, breakdown, raw = grade_trial(sess["rank_key"], sess["answers"])
            c = gcfg(msg.guild.id)
            log_ch = msg.guild.get_channel(c["log_ch"])
            ping = f"<@&{c['dev_role']}>" if c["dev_role"] else "**Developers**"
            rep = discord.Embed(title=f"📊 MANAGEMENT TRIAL REPORT — {title}", description=f"👤 **Candidate:** {msg.author.mention}\n🎯 **Score:** **`{pct}%`** *(Pass: `{pass_pct}%`)* • ⚖️ **Verdict:** **`{verdict}`**", color=discord.Color.green() if verdict == "PASS" else discord.Color.red(), timestamp=discord.utils.utcnow())
            rep.set_thumbnail(url=msg.author.display_avatar.url)
            rep.add_field(name="📝 Question Breakdown", value="\n".join(f"• {x}" for x in breakdown), inline=False)
            rep.set_footer(text=f"Track:{sess['rank_key']} | UserID:{msg.author.id}")
            if log_ch:
                try:
                    await log_ch.send(content=f"📣 {ping} — New **{title}** graded!", embed=rep, file=discord.File(io.BytesIO(raw), filename=f"trial-{sess['rank_key']}-{msg.author.id}.txt"), view=VerdictView())
                except Exception:
                    pass
            await msg.channel.send(f"✅ **Trial Complete!** Score: **`{pct}%`** (`{verdict}`). Report sent to Developers! Closing in 10s...")
            await asyncio.sleep(10)
            try:
                await msg.channel.delete(reason="Management trial complete")
            except Exception:
                pass
            return

        # 2. Simple Chat Phase & Trial Request Listener (Name: @user / Phase: 1-5 or Manager / @Bot)
        if self.user in msg.mentions:
            clean = re.sub(rf"<@!?{self.user.id}>", "", msg.content or "").strip()
            low = clean.lower()
            other = [m for m in msg.mentions if m.id != self.user.id]
            cand = other[0] if other else msg.author

            for key, kw in (("chief", "chief"), ("head", "head"), ("senior", "senior"), ("manager", "manager")):
                if kw in low:
                    return await msg.reply(await start_management_trial(msg.guild, cand, key))

            pm = re.search(r"phase\s*[:\-]?\s*([1-5])", low)
            if not pm:
                return await msg.reply(f"📋 **Request Format:**\n```\nName: @user\nPhase: 1 / 2 / 3 / 4 / 5  (or Manager / Senior / Head / Chief Manager)\n@{self.user.display_name}\n```")

            pkey = f"phase{pm.group(1)}"
            ptitle, pdesc, pcol = PHASE_INTROS[pkey]
            emb = discord.Embed(title=f"🔥 {ptitle} — STARTING MESSAGE", description=f"👤 **Candidate:** {cand.mention} (`{cand.display_name}`)\n📨 **Requested By:** {msg.author.mention}\n\n{pdesc}", color=pcol, timestamp=discord.utils.utcnow())
            emb.set_author(name=f"Chicago Crossfire Phase Request — {cand.display_name}", icon_url=cand.display_avatar.url)
            emb.set_thumbnail(url=cand.display_avatar.url)
            emb.set_footer(text=f"Track:{pkey} | UserID:{cand.id} • Developers: Approve or Fail below")
            try:
                await msg.add_reaction("✅")
            except Exception:
                pass
            await msg.reply(content=f"📣 {cand.mention} — **Phase Request Logged!**", embed=emb, view=VerdictView())

            log_ch = msg.guild.get_channel(gcfg(msg.guild.id)["log_ch"])
            if log_ch and log_ch.id != msg.channel.id:
                dev_p = f"<@&{gcfg(msg.guild.id)['dev_role']}>" if gcfg(msg.guild.id)["dev_role"] else "**Developers**"
                try:
                    await log_ch.send(content=f"📣 {dev_p} — New Phase Request by {cand.mention}!", embed=emb, view=VerdictView())
                except Exception:
                    pass


def reg_cmds(bot: ManagementHubBot):
    @bot.tree.command(name="setup", description="One-time setup for Developers, Management, Chief Role, Log Channel & Ticket Category")
    async def s_setup(i: discord.Interaction, dev_role: discord.Role, manager_role: discord.Role, chief_role: discord.Role, log_channel: discord.TextChannel, category: discord.CategoryChannel):
        if not i.user.guild_permissions.administrator:
            return await i.response.send_message("❌ Administrators only.", ephemeral=True)
        gcfg(i.guild.id).update({"dev_role": dev_role.id, "mgmt_role": manager_role.id, "chief_role": chief_role.id, "log_ch": log_channel.id, "cat_id": category.id})
        save_db()
        await i.response.send_message(f"✅ **Management Hub Configured!**\n🛠️ Devs: {dev_role.mention} | 📋 Managers: {manager_role.mention} | 👑 Chief: {chief_role.mention}\n📜 Logs: {log_channel.mention} | 📁 Category: `{category.name}`\n👉 Run `/phase_panel`, `/trial_panel`, and `/support_panel`!", ephemeral=True)

    @bot.tree.command(name="phase_panel", description="Post the Simple Phase Requests guide panel")
    async def s_pp(i: discord.Interaction):
        if not is_mgmt(i.user):
            return await i.response.send_message("❌ Management only.", ephemeral=True)
        emb = discord.Embed(title="🔥 SIMPLE PHASE REQUESTS", description=f"Type this format in chat to start your phase:\n```\nName: @user\nPhase: 1 / 2 / 3 / 4 / 5\n@{bot.user.display_name}\n```\n*Sends your Starting Intro with your avatar and notifies Developers automatically!*", color=discord.Color.from_rgb(220, 53, 69))
        await i.response.send_message(embed=emb)

    @bot.tree.command(name="trial_panel", description="Post the Manager, Senior, Head & Chief Manager Trials panel")
    async def s_tp(i: discord.Interaction):
        if not is_mgmt(i.user):
            return await i.response.send_message("❌ Management only.", ephemeral=True)
        emb = discord.Embed(title="👑 MANAGEMENT TRIALS CENTER", description="Select your target rank below to open a private, auto-graded trial room:\n\n📋 **Manager Trial** (3Q • `80%`)\n⭐ **Senior Manager Trial** (4Q • `85%`)\n👑 **Head Manager Trial** (4Q • `88%`)\n🔥 **Chief Manager Trial — HELL MODE** (5Q • `92%`)", color=discord.Color.dark_red())
        await i.response.send_message(embed=emb, view=TrialPanelView())

    @bot.tree.command(name="support_panel", description="Post the Management Support Ticket Center")
    async def s_sp(i: discord.Interaction):
        if not is_mgmt(i.user):
            return await i.response.send_message("❌ Management only.", ephemeral=True)
        n_on = len(gcfg(i.guild.id)["oncall"])
        emb = discord.Embed(title="🎧 MANAGEMENT SUPPORT CENTER", description=f"Need Management assistance? Pick a category below to open a private ticket!\n\n🟢 **Managers Currently On-Call:** `{n_on}` *(Staff use `/oncall` to toggle)*\n📄 *Full transcripts are automatically sent to your DMs when closed.*", color=discord.Color.blurple())
        await i.response.send_message(embed=emb, view=SupportPanelView())

    @bot.tree.command(name="oncall", description="Toggle yourself On-Call / Off-Call for Management Support pings")
    async def s_oc(i: discord.Interaction):
        if not is_mgmt(i.user):
            return await i.response.send_message("❌ Management only.", ephemeral=True)
        oc = gcfg(i.guild.id)["oncall"]
        if i.user.id in oc:
            oc.remove(i.user.id)
            txt = f"🔴 {i.user.mention} is now **OFF-CALL**."
        else:
            oc.append(i.user.id)
            txt = f"🟢 {i.user.mention} is now **ON-CALL** for Management Support tickets!"
        save_db()
        await i.response.send_message(txt)

    @bot.tree.command(name="close", description="Close this Management Support ticket and DM the transcript")
    async def s_cls(i: discord.Interaction, reason: str = "Resolved by Management"):
        if not is_mgmt(i.user):
            return await i.response.send_message("❌ Management only.", ephemeral=True)
        await close_support_ticket(i, reason)

    @bot.tree.command(name="record", description="View a member's passed Phases & Management Trials")
    async def s_rec(i: discord.Interaction, member: discord.Member):
        passed = gcfg(i.guild.id)["records"].get(str(member.id), [])
        emb = discord.Embed(
            title=f"📁 Clearance Record — {member.display_name}",
            description=", ".join(f"`{x.upper()}`" for x in passed) or "*No approved phases or trials yet.*",
            color=discord.Color.blurple(),
        )
        emb.set_thumbnail(url=member.display_avatar.url)
        await i.response.send_message(embed=emb, ephemeral=True)


# --- 6. 24/7 ENTRYPOINT WITH 429 AUTO-RETRY ---
async def main():
    global STATUS
    await run_web()
    asyncio.create_task(self_ping())
    if not TOKEN:
        STATUS = "MISSING BOT_TOKEN"
        print("❌ Add BOT_TOKEN in Environment Variables!")
        while True:
            await asyncio.sleep(3600)
    mi, w = True, 90
    while True:
        bot = ManagementHubBot(mi)
        reg_cmds(bot)
        try:
            await bot.start(TOKEN)
            break
        except discord.PrivilegedIntentsRequired:
            await bot.close()
            mi = False
        except discord.HTTPException as e:
            await bot.close()
            if e.status == 429:
                STATUS = f"429 wait {w}s"
                await asyncio.sleep(w)
                w = min(w + 60, 300)
            else:
                await asyncio.sleep(60)
        except Exception as e:
            await bot.close()
            STATUS = f"Retry ({type(e).__name__})"
            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
    
