# =====================================================================
# PART 1 OF 5 — PASTE THIS FIRST AT LINE 1 OF YOUR GITHUB FILE
# CHICAGO CROSSFIRE — 24/7 PHASE OVERSEER, AUTO-GRADER & DEV REPORTER
# Requirements: discord.py, aiohttp | Env Vars: BOT_TOKEN, GEMINI_API_KEY
# =====================================================================
import asyncio
import datetime
import io
import json
import os
import re
import time
import aiohttp
from aiohttp import web
import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.getenv("BOT_TOKEN", "").strip().strip('"').strip("'")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
DB_FILE = "chicago_exams_db.json"
START_TIME, BOT_STATUS = time.time(), "Starting..."

# Active live written exams mapped by exam channel_id: {ch_id: session_dict}
ACTIVE_EXAMS: dict[int, dict] = {}

# Active live operational monitors mapped by (guild_id, user_id): session_dict
ACTIVE_MONITORS: dict[tuple[int, int], dict] = {}

# Official Starting Messages & Introductions for EVERY Phase & Executive Track
PHASE_INTROS = {
    "phase1": {
        "banner": "🎫 PHASE 1 — LIVE TICKET RESPONSE OVERSIGHT",
        "intro": (
            "Welcome to **Phase 1 of the Chicago Crossfire Moderator Trial**! "
            "Your Phase 1 request has been officially logged and **Automated Live Oversight** is now locked onto your profile. "
            "Do **not** expect a simple quiz—starting right now, the Overseer is silently monitoring how you greet players, "
            "investigate issues, verify Roblox usernames/proof, and maintain professionalism inside real ticket channels."
        ),
        "objective": (
            "• Claim & respond inside real **Chicago Crossfire ticket channels** (`support-`, `report-`, `appeal-`, `bug-`, `shop-`, `faction-`).\n"
            "• Greet the player respectfully, request their **Roblox Username** & valid proof/clips, cite exact rules, and resolve cleanly.\n"
            "• Complete **`4` monitored ticket responses** (or have a Dev click **Grade & Report Now**)."
        ),
        "rules": "⛔ **Instant Fail:** Rude/hostile tone, lazy 2-word replies, closing tickets without proof, or defending friends/faction members.",
        "color": discord.Color.from_rgb(59, 130, 246),
    },
    "phase2": {
        "banner": "👁️ PHASE 2 — LIVE CHAT SURVEILLANCE & MOD OVERSIGHT",
        "intro": (
            "Welcome to **Phase 2 of the Chicago Crossfire Moderator Trial**! "
            "You cleared Phase 1—now you are stepping into **live public chat & active moderation**. "
            "The Overseer is silently tracking your public chat responses, de-escalation discipline, and live Audit Log moderation actions "
            "(timeouts & rule-breaking message deletions) to see if you stay ice-cold under baiting and drama."
        ),
        "objective": (
            "• Patrol public chats (`#general`, `#faction-chat`, etc.) and shut down rulebreakers or baiters neutrally in 1–2 calm sentences.\n"
            "• Cite accurate server rules, direct disputes to tickets (Rule #6), and execute justified moderation actions.\n"
            "• Complete **`5` monitored public responses / mod actions** for automatic grading."
        ),
        "rules": "⛔ **Instant Fail:** Arguing with players in public chat, falling for trolls/bait, mini-modding over Senior Staff, or unlogged punishments.",
        "color": discord.Color.from_rgb(245, 158, 11),
    },
    "phase3": {
        "banner": "🔎 PHASE 3 — HYBRID TICKET FORENSICS & LIVE MOD OVERSIGHT",
        "intro": (
            "Welcome to **Phase 3 of the Chicago Crossfire Moderator Trial**! "
            "This is the operational crucible—you are now being monitored across **BOTH real ticket forensics AND live server moderation simultaneously**. "
            "Developers expect you to reject cropped 4-second RDM clips, verify Gamepass claims before escalating, and handle live chat pressure without a single slip-up."
        ),
        "objective": (
            "• Handle high-stakes tickets (`report-`, `appeal-`, `shop-`, `urgent-`) with airtight evidence checks AND moderate public channels.\n"
            "• Know exactly when to escalate to High Command / Developers vs. resolving independently.\n"
            "• Complete **`6` monitored ticket & moderation actions** (`88%+` required to pass)."
        ),
        "rules": "⛔ **Instant Fail:** Accepting doctored/cropped clips, sloppy transcripts, slow/lazy responses, or showing any faction bias.",
        "color": discord.Color.from_rgb(234, 88, 12),
    },
    "phase4": {
        "banner": "⚡ PHASE 4 — LIVE AMBUSH & UNDER-FIRE STRESS TEST",
        "intro": (
            "Welcome to **Phase 4 of the Chicago Crossfire Moderator Trial**! "
            "No mercy and no hand-holding. You have entered a locked **Live Ambush & Stress Room** overseen directly by Developers. "
            "You will face **5 brutal ambush scenarios**—coordinated raids, faction friend traps, faked Inspect Element proof, blackmail appeals, and corrupt orders."
        ),
        "objective": (
            "• Answer all **5 ambush scenarios** inside your private exam channel with concrete, step-by-step protocols.\n"
            "• Minimum **`25 words`** per response • Passing threshold: **`88%`**.\n"
            "• Every response speed, word count, and red flag is recorded for Developer review."
        ),
        "rules": "⛔ **Instant Fail:** Copy-pasting AI essays, 3 low-effort short-answer warnings, caving to friends/threats, or obeying proof-less orders.",
        "color": discord.Color.from_rgb(220, 38, 38),
    },
    "phase5": {
        "banner": "🏛️ PHASE 5 — CHIEF ADMINISTRATIVE & DEVELOPER FINAL BOARD",
        "intro": (
            "Welcome to **Phase 5 — The Final High Command Board** of **Chicago Crossfire**! "
            "Very few Trial Moderators survive to this room. Your complete **Phase 1–4 oversight history** has been pulled into your dossier, "
            "and you will now face **4 final board interrogation checkpoints** graded strictly for Developers & Chief Administration."
        ),
        "objective": (
            "• Deliver an honest self-audit, loophole-free policy rewrite, team-integrity defense, and final Moderator oath.\n"
            "• Minimum **`25 words`** per checkpoint • Passing threshold: **`90%`**.\n"
            "• Developers will cast the final verdict (**Approve & Promote** / **Oral Board** / **Fail**)."
        ),
        "rules": "⛔ **Instant Fail:** Dodging accountability, generic/AI answers, or failing your prior-phase audit inspection.",
        "color": discord.Color.from_rgb(124, 58, 237),
    },
    "staff3": {
        "banner": "👥 STAFF ENTRY GAUNTLET — 3 HARDCORE QUESTIONS",
        "intro": (
            "Welcome to the **Chicago Crossfire Staff Entry Gauntlet**! "
            "Only **3 high-pressure questions** stand between you and a Staff seat—which means every single sentence is scrutinized. "
            "Weak, generic, or one-line replies are rejected automatically by the Overseer."
        ),
        "objective": (
            "• Answer all **3 multi-layered Staff scenarios** covering multi-rule chaos triage, corruption pressure, and concrete contribution.\n"
            "• Minimum **`30 words`** per answer • Passing threshold: **`85%`**."
        ),
        "rules": "⛔ **Instant Fail:** AI-generated text, ignoring parts of a multi-step scenario, or 3 minimum-word rejections.",
        "color": discord.Color.blurple(),
    },
    "admin10": {
        "banner": "🛡️ ADMINISTRATION VETTING EXAM — 10 HARDCORE QUESTIONS",
        "intro": (
            "Welcome to the **Chicago Crossfire Administration Vetting Exam**! "
            "Issued directly by Leadership to filter out unqualified or biased candidates before granting dangerous Discord permissions. "
            "You will be tested cold on Role Hierarchy, token-grab containment, Audit Log forensics, raid lockdowns, and conflict-of-interest ethics."
        ),
        "objective": (
            "• Complete all **10 technical & ethical Admin questions** with exact operational steps.\n"
            "• Minimum **`25 words`** per answer • Passing threshold: **`90%`**."
        ),
        "rules": "⛔ **Instant Fail:** AI copy-paste detection, weak security knowledge, or defending faction bias.",
        "color": discord.Color.from_rgb(185, 28, 28),
    },
    "chief11": {
        "banner": "🔥🏛️ CHIEF ADMINISTRATIVE — HELL MODE EXECUTIVE GAUNTLET (11Q)",
        "intro": (
            "Welcome to **HELL MODE — The Chicago Crossfire Chief Administrative Executive Gauntlet**! "
            "This seat is the **#2 operational authority beneath Ownership**, commanding Administrators, Internal Affairs, Crisis Defense, and Server Security. "
            "Expect zero forgiveness: you will face simultaneous 3-front catastrophes, internal Admin corruption rings, legal/safety emergencies, "
            "40% staff mutinies, and executive KPI architecture."
        ),
        "objective": (
            "• Conquer all **11 nightmare-tier executive scenarios** with structured, actionable command plans.\n"
            "• Minimum **`45 words`** per answer • Passing threshold: **`92%`** + Developer/Ownership Oral Board."
        ),
        "rules": "⛔ **Instant Fail:** Leadership buzzwords without concrete execution steps, tipping off corrupt staff before securing proof, caving to blackmail/mutinies, or ANY AI usage.",
        "color": discord.Color.from_rgb(153, 27, 27),
    },
    "admin13": {
        "banner": "⚔️ FULL ADMINISTRATOR MASTERY EXAM — 13 HARDCORE QUESTIONS",
        "intro": (
            "Welcome to the **Chicago Crossfire Full Administrator Mastery Exam**! "
            "Full Administrators hold destructive permissions—this 13-question gauntlet verifies your live crisis judgment, "
            "webhook/bot security mastery, anti-framing forensics, Trial Mod coaching, and conflict-free appeal standards."
        ),
        "objective": (
            "• Complete all **13 comprehensive Admin questions** with technical precision.\n"
            "• Minimum **`25 words`** per answer • Passing threshold: **`88%`**."
        ),
        "rules": "⛔ **Instant Fail:** Unlogged moderation mindset, AI-generated answers, or missing critical Discord security fixes.",
        "color": discord.Color.from_rgb(190, 18, 60),
    },
}

# Operational Monitoring Phases (Live Oversight for Phases 1-3)
MONITOR_PHASES = {
    "phase1": (
        "Phase 1 — Live Ticket Response Oversight",
        85,
        "tickets",
        4,
        "Respond to real player tickets! The Overseer is silently monitoring your response speed, greeting, professionalism, proof/Roblox username verification, and rule accuracy.",
    ),
    "phase2": (
        "Phase 2 — Live Chat & Moderation Oversight",
        85,
        "public",
        5,
        "Monitor public chats & moderate calmly! The Overseer is tracking your rule citations, de-escalation tone, timeouts/deletions, and zero-drama discipline.",
    ),
    "phase3": (
        "Phase 3 — Hybrid Ticket Forensics & Mod Oversight",
        88,
        "both",
        6,
        "Handle both tickets (evidence/clip checks, escalations) AND live server moderation! Every ticket reply, public guidance, and mod action is logged and graded for Developers.",
    ),
}

TICKET_PFX = ("ticket", "support", "report", "appeal", "bug", "shop", "faction", "partner", "urgent")
GOOD_TICKET_W = ("hello", "welcome", "assist", "help", "roblox", "username", "proof", "clip", "video", "screenshot", "receipt", "rule", "escalat", "thank", "resolve", "anything else", "understand")
GOOD_MOD_W = ("please", "rule", "ticket", "keep it", "calm", "respect", "stop", "warning", "reminder", "channel", "appeal", "staff")
RUDE_W = ("shut up", "stfu", "idiot", "stupid", "dumb", "cry about it", "skill issue", "trash", "loser", "clown", "sybau", "idc", "whatever")
AI_FLAGS = (
    "as an ai", "in conclusion,", "furthermore, it is crucial",
    "delve into", "foster a positive", "multifaceted", "holistic approach",
    "it is imperative that", "paramount importance",
)

# =====================================================================
# PART 2 OF 5 — PASTE DIRECTLY BELOW PART 1 (FAR LEFT EDGE)
# =====================================================================
EXAMS = {
    "phase1": (
        "Mod Trial — Phase 1: Lockdown & Rules Drill", 90, 20, [
            ("Confirm Discord & Roblox 2FA status and explain why a compromised Trial Mod account threatens the whole server even without Ban permissions.", ["2fa", "token", "delete", "ping", "leak", "permission"]),
            ("A player posts a spaced invite ('d i s c o r d . g g / ...') and claims it isn't a link. Cite the rule, proof needed BEFORE deleting, and exact punishment.", ["rule", "advert", "screenshot", "proof", "delete", "timeout", "warn"]),
            ("Define RDM, Combat Logging, Metagaming, and Exploiting in Chicago Crossfire—and state which requires video vs. screenshot proof.", ["rdm", "combat", "meta", "exploit", "video", "clip", "screenshot"]),
            ("You accidentally timeout the wrong user in a fast argument. Detail your exact correction, apology, and staff-log steps within 60 seconds.", ["unmute", "remove", "apolog", "log", "staff", "mistake"]),
            ("What data inside #staff-chat, #transcript-logs, and Audit Logs is strictly classified, and what happens if you leak even a cropped screenshot?", ["leak", "confidential", "blacklist", "terminate", "demote", "transcript"]),
        ],
    ),
    "phase2": (
        "Mod Trial — Phase 2: Live Surveillance & Anti-Baiting", 85, 20, [
            ("Describe 3 real or realistic chat violations you must catch early before Senior Staff intervene, including rule numbers and logging steps.", ["rule", "log", "proof", "staff", "warn"]),
            ("A troll tries to rule-shark and bait you in #general to make you lose your temper. Write your exact 1-2 sentence neutral shutdown.", ["ticket", "calm", "neutral", "rule", "drama", "de-escalate"]),
            ("Where is the exact line between normal Chicago RP banter and Rule #1 Harassment when a gang leader mocks a new player without slurs?", ["target", "harass", "repeated", "new", "warn", "respect"]),
            ("Explain a specific scenario where deleting a rule-breaking message immediately is WORSE than waiting 5 seconds to capture proof first.", ["screenshot", "evidence", "proof", "id", "log", "delete"]),
            ("How do you spot disguised self-promotion or raid scouts in public chat without falsely punishing innocent players?", ["invite", "dm", "alt", "account", "age", "context", "verify"]),
        ],
    ),
    "phase3": (
        "Mod Trial — Phase 3: Ticket Triage & Clip Forensics", 85, 22, [
            ("Explain your complete workflow from claiming a Chicago Crossfire ticket to closing it with an airtight transcript.", ["claim", "proof", "roblox", "reason", "transcript", "close"]),
            ("A player sends a 4-second cropped clip of dying and yells 'BAN FOR RDM!' Why is it invalid and what exact evidence do you demand?", ["context", "full", "30", "longer", "bait", "username", "proof"]),
            ("A player opens a Shop/Gamepass ticket claiming a missing weapon pack with a blurry screenshot. What exact verification steps do you take before pinging Devs?", ["roblox", "receipt", "inventory", "gamepass", "username", "verify", "escalate"]),
            ("List 3 exact situations where you MUST escalate a ticket to High Command / Developers instead of handling it yourself.", ["exploit", "dev", "staff", "dox", "shop", "conflict", "urgent"]),
            ("A ticket opener gets impatient and starts swearing at you inside the ticket. How do you enforce rules while still resolving their actual report?", ["warn", "professional", "calm", "evidence", "close", "transcript"]),
        ],
    ),
    "phase4": (
        "Mod Trial — Phase 4: Live Ambush & Stress Test", 88, 25, [
            ("RAID AMBUSH: 8 alts flood #general with mass pings and fake Robux links while no Admins are online. Give your exact 30-second Mod-only action sequence.", ["slowmode", "timeout", "delete", "screenshot", "id", "ping", "admin"]),
            ("FRIEND TRAP: Your own faction Co-Leader is reported with clear 30s video of speed-hacking and DMs you begging to hide it. Detail your exact actions on BOTH the ticket and DM.", ["conflict", "recuse", "escalate", "screenshot", "dm", "bias", "ban"]),
            ("DOCTORED PROOF: Someone submits a screenshot of a rival gang leader using a slur, but you suspect Inspect Element/Photoshop. How do you verify it?", ["search", "log", "message", "id", "deleted", "audit", "verify"]),
            ("HOSTILE APPEAL: A banned player insults you and threatens a TikTok 'exposed' video unless unbanned in 5 mins. Write your word-for-word reply and closing action.", ["appeal", "evidence", "blackmail", "professional", "deny", "close", "transcript"]),
            ("CORRUPT ORDER: A Senior Mod orders you to ban someone immediately with zero proof ('I hate that kid'). Do you obey or refuse? Explain how you escalate.", ["refuse", "proof", "escalate", "admin", "chief", "screenshot", "log"]),
        ],
    ),
    "phase5": (
        "Mod Trial — Phase 5: Chief Admin Final Board", 90, 25, [
            ("SELF-AUDIT: Identify your biggest weakness or hardest judgment call during Mod duties, why it happens, and the concrete safeguard you use to fix it.", ["mistake", "verify", "double", "second", "log", "calm"]),
            ("POLICY REWRITE: Pick one Chicago Crossfire rule players abuse via loopholes and draft a stricter, loophole-free replacement.", ["loophole", "rule", "clip", "proof", "punish", "context"]),
            ("TEAM INTEGRITY: Explain how you handle disagreeing with a Fellow Mod's punishment in public chat vs. private staff channels.", ["private", "staff", "public", "rule", "admin", "professional"]),
            ("FINAL OATH: Why should Developers & Chief Administration trust you with permanent Moderator permissions over every other Trial Mod?", ["bias", "proof", "active", "audit", "trust", "accountab"]),
        ],
    ),
    "staff3": (
        "Staff Gauntlet (3 Hardcore Questions)", 85, 30, [
            ("MULTI-RULE TRIAGE: Simultaneously in #general: (A) rival factions trade personal insults, (B) a member advertises their Roblox game, and (C) a new player is mocked. Give exact priority order, rules, wording, and logging steps.", ["priority", "advert", "delete", "harass", "rule", "log", "timeout"]),
            ("CORRUPTION PRESSURE: You catch a higher-ranking Staff member deleting their friend's violation and they threaten to get you demoted. Detail your evidence preservation and chain-of-command steps.", ["screenshot", "log", "id", "chief", "owner", "escalate", "silent"]),
            ("CONCRETE VALUE: Give your real weekly schedule, one real personal weakness (and how you control it), and two specific improvements you will execute in 14 days.", ["schedule", "hour", "weakness", "improve", "ticket", "active"]),
        ],
    ),
    "admin10": (
        "Admin Vetting Exam (10 Hardcore Questions)", 90, 25, [
            ("Explain Discord's Role Hierarchy and the exact disaster if a Trial Mod or public Bot role sits above Admin or Auto-Mod.", ["hierarchy", "above", "cannot", "kick", "ban", "nuke", "top"]),
            ("A Mod's account is token-grabbed and starts spamming @everyone Nitro scams and deleting #announcements. List your exact first 5 containment actions in order.", ["strip", "role", "ban", "kick", "delete", "audit", "alert"]),
            ("A rival faction opens an URGENT exploit report against your own gang leader. What is the ONLY acceptable protocol and why?", ["recuse", "conflict", "bias", "escalate", "credib", "another"]),
            ("A player sends a DDoS threat screenshot + 5s cropped Roblox clip with no username. How do you check for Inspect Element and why does the clip fail?", ["inspect", "log", "id", "context", "username", "invalid", "proof"]),
            ("Someone secretly gave a user Manage Channels, wiped #general, and removed the role 20s later. Detail your exact Audit Log investigation.", ["audit", "filter", "role", "channel", "timestamp", "target", "id"]),
            ("You find a respected Mod banned an innocent player out of anger with zero proof. How do you unban, document, and coach privately without public drama?", ["unban", "private", "log", "apolog", "strike", "public"]),
            ("25 raid bots flood 4 channels with NSFW & pings. Walk through your exact Discord lockdown, purge, mass-ban, and safe reopening sequence.", ["pause", "invite", "verification", "lock", "slowmode", "ban", "purge"]),
            ("Name 4 Discord permissions Mods/junior Bots must NEVER hold and explain the exact nuke/abuse scenario each enables.", ["administrator", "webhook", "manage", "role", "channel", "ban", "nuke"]),
            ("A fellow Admin is consistently rude in tickets and punishes players out of anger. How do you build a factual case and escalate to Chief Admin?", ["transcript", "pattern", "evidence", "objective", "chief", "escalate"]),
            ("If promoted to Admin today, what is the #1 mistake you are most likely to make in Month 1 and what hard safeguard stops it?", ["mistake", "check", "second", "log", "safeguard", "bias"]),
        ],
    ),
    "chief11": (
        "Chief Administrative — HELL MODE (11 Executive Questions)", 92, 45, [
            ("3-FRONT CATASTROPHE (Owner offline 6h): Simultaneously (A) compromised Senior Admin deletes channels/bans members, (B) 40-bot NSFW raid hits public chat, (C) in-game dupe glitch leaks causing #general riots. Give your minute-by-minute Command Protocol (0-2m, 2-10m, 10-60m).", ["strip", "ban", "pause", "invite", "lock", "dev", "audit", "statement", "delegate"]),
            ("CORRUPTION RING: Whistleblower evidence shows your Head Admin + 3 Mods collude with a gang (tipping off spectates, deleting friend tickets, blacklisting rivals). Detail covert IA investigation, synchronized simultaneous strip, and wrongful-ban recovery.", ["covert", "audit", "transcript", "simultaneous", "strip", "retaliat", "review", "unban"]),
            ("LEGAL/SAFETY EMERGENCY: A Senior Mod is accused of pressuring a 13yo in DMs for personal photos while someone else doxxes a staff member's address in #general. Detail exact preservation (IDs/links), immediate removal, Discord/Roblox Trust & Safety escalation, and confidentiality.", ["delete", "dox", "message id", "user id", "trust", "safety", "suspend", "ban", "confidential"]),
            ("40% STAFF MUTINY: After rightfully blacklisting a popular abusive Admin, 2 Admins & 5 Mods threaten mass resignation unless you reinstate them while rival servers spread smears. Explain why you do/don't negotiate, emergency coverage, and PR discipline.", ["refuse", "negotiate", "blackmail", "coverage", "calm", "professional", "drama", "retain"]),
            ("ANTI-NUKE ARCHITECTURE: Blueprint Chicago Crossfire's full Discord security: Role Hierarchy layering, Webhook/Bot token Least-Privilege rules, 2FA policy, and your Sunday 5-min Security Audit checklist.", ["hierarchy", "webhook", "administrator", "2fa", "audit", "bot", "least"]),
            ("CREATOR BLACKMAIL: A 25k-follower YouTuber (owns all gamepasses + Server Booster) is caught on clear video using hitbox exploits and threatens an Exposed video if banned. Detail enforcement, evidence lock, Owner brief, and PR stance.", ["ban", "equal", "bias", "video", "proof", "owner", "credibility", "statement"]),
            ("CORRUPTION-PROOF KPIs: Quotas like '10 tickets/wk' cause ghost-claiming and rushed closes. Design a quality+quantity Staff Evaluation System catching stat-padding, plus fair LOA, strike decay, and promotion/demotion thresholds.", ["transcript", "audit", "quality", "sniping", "loa", "decay", "threshold", "metric"]),
            ("LOOPHOLE ELIMINATION: Gangs camp safe-zones, bait civilians into 1 shot, then clip only the civilian to fake RDM bans. Draft the exact new rule text, clip requirements, baiting penalty, in-game/Discord sync, and retroactive vs. prospective enforcement.", ["clip", "context", "30", "bait", "false", "prospective", "retroactive", "dev"]),
            ("ENDING DEPT WAR: Buggy update triggers blame war between Devs, Admin Staff, and PD/Faction Leads. Define exact workflow, SLA response standards, communication boundaries, and joint accountability.", ["sla", "triage", "boundary", "bug", "qa", "escalation", "joint", "accountab"]),
            ("INCORRUPTIBLE BLACKLIST & APPEALS: Stop bribed/quiet unbans. Design a tamper-proof Blacklist & Tribunal system with mandatory IDs/archives, dual-approval unbans, cooldowns, and weekly Unban Audit checks.", ["roblox", "discord", "id", "dual", "approval", "cooldown", "audit", "unban"]),
            ("EXECUTIVE MIRROR: Give (A) your concrete Week 1-4 Restructuring Plan, (B) your single most dangerous real leadership flaw + safeguard, and (C) 3 exact failures that justify Ownership stripping you on the spot.", ["week", "audit", "flaw", "safeguard", "leak", "bias", "strip", "owner"]),
        ],
    ),
}

# =====================================================================
# PART 3 OF 5 — PASTE DIRECTLY BELOW PART 2 (FAR LEFT EDGE)
# =====================================================================
EXAMS["admin13"] = (
    "Full Administrator Exam (13 Hardcore Questions)", 88, 25, [
        ("List your verified Admin+ track record and detail one real crisis you solved—including what went wrong and what you'd do faster.", ["crisis", "resolve", "faster", "mistake", "experience"]),
        ("Explain the exact risks of Manage Roles, Manage Webhooks, Manage Server, and Administrator—and how a rogue Manage Webhooks user ruins a server without Send Messages.", ["webhook", "role", "administrator", "spam", "nuke", "impersonat"]),
        ("Our Auto-Mod bot fails to auto-ban a rogue Senior Mod spamming scam links. Diagnose BOTH technical reasons and the exact fix.", ["hierarchy", "role", "above", "permission", "ban", "top"]),
        ("A Trial Mod escalates an URGENT ticket mixing a mass-exploiter, missing Gamepass claim, and staff misconduct complaint. How do you separate, investigate, and route all three?", ["separate", "dev", "chief", "proof", "transcript", "verify"]),
        ("Walk through your exact order of Discord actions during a 30-account raid without mass-banning legitimate players.", ["pause", "invite", "verification", "lock", "id", "age", "ban"]),
        ("A rival faction submits 3 screenshots accusing a PD Commander of corrupt DMs and powergaming. Give 4 technical checks to detect framing/impersonation.", ["id", "impersonat", "inspect", "context", "log", "video", "verify"]),
        ("A Phase 3 Trial Mod ignores proof rules and argues in tickets after 1 warning. Give your exact decision (retrain vs. fail) and write the exact DM.", ["proof", "fail", "demote", "professional", "reason", "reapply"]),
        ("A weapon nerf triggers 15 players spamming 'L DEVS' and mass-pinging Devs in #general. Regain control in 60s without unfairly locking the whole server.", ["slowmode", "redirect", "feedback", "warn", "ping", "calm"]),
        ("Ownership is offline during 3 failures: (A) Bloxlink fails to sync, (B) Ticket Bot crashes mid-rush, (C) Google Form webhook gets spammed. Detail all 3 fixes.", ["manual", "role", "fallback", "delete", "webhook", "notify", "dev"]),
        ("A furious user accuses YOU of power-tripping in #general in front of 50 people. Write your exact public reply, private step, and why silently deleting looks guilty.", ["ticket", "calm", "audit", "log", "transparent", "chief", "guilty"]),
        ("A player you banned 3 weeks ago submits a mature Ban Appeal. Should YOU alone decide it? Explain conflict-of-interest appeals.", ["conflict", "bias", "another", "admin", "second", "unbiased"]),
        ("Diagnose 2 real operational weaknesses in growing Chicago RP servers and design a concrete Admin-run fix for both.", ["activity", "shift", "ticket", "bias", "system", "track"]),
        ("State your daily active window (with timezone), accept instant termination for any unlogged abuse/leak/bias, and prove in 3 sharp sentences why Chicago Crossfire is safer with you.", ["timezone", "active", "blacklist", "accountab", "audit", "safe"]),
    ],
)


def load_db() -> dict:
    """Loads persisted server configuration and candidate grading records."""
    try:
        return json.load(open(DB_FILE, encoding="utf-8")) if os.path.exists(DB_FILE) else {}
    except Exception:
        return {}


def save_db() -> None:
    """Persists database safely to disk."""
    try:
        json.dump(DB, open(DB_FILE, "w", encoding="utf-8"), indent=2)
    except Exception:
        pass


DB = load_db()


def gcfg(gid: int) -> dict:
    return DB.setdefault(
        str(gid),
        {"dev_role": 0, "report_ch": 0, "exam_cat": 0, "approved_role": 0, "candidates": {}},
    )


def is_dev_or_admin(m: discord.Member) -> bool:
    """True for Administrators or members with the configured Developer Role."""
    if not isinstance(m, discord.Member):
        return False
    if m.guild_permissions.administrator:
        return True
    drid = gcfg(m.guild.id).get("dev_role", 0)
    return bool(drid and any(r.id == drid for r in m.roles))


def is_ticket_channel(ch) -> bool:
    """Detects whether a Discord channel is an active support/report/appeal ticket."""
    name = (getattr(ch, "name", "") or "").lower()
    topic = (getattr(ch, "topic", "") or "").lower()
    return name.startswith(TICKET_PFX) or any(k in topic for k in ("ccticket", "ruleticket", "ticketsys", "ticket |", "appeal"))


def build_starting_intro_embed(
    g: discord.Guild,
    u: discord.Member | None,
    phase_key: str,
    requested_by: discord.Member = None,
    exam_ch: discord.TextChannel = None,
    is_monitor: bool = False,
) -> discord.Embed:
    """Builds the official Starting Message & Phase Introduction embed with Candidate Avatar."""
    info = PHASE_INTROS[phase_key]
    cand_line = f"👤 **Candidate:** {u.mention} (`{u.display_name}` | ID: `{u.id}`)" if u else "👤 **Candidate:** *Open Phase Briefing*"
    req_line = f"\n📨 **Requested By:** {requested_by.mention}" if (requested_by and u and requested_by.id != u.id) else ""
    room_line = f"\n🚪 **Assigned Exam Room:** {exam_ch.mention}" if exam_ch else ""

    if is_monitor and phase_key in MONITOR_PHASES:
        _, pass_pct, scope, target_n, _ = MONITOR_PHASES[phase_key]
        mode_line = f"📡 **Mode:** Live Operational Monitoring (`{scope.upper()}`) • 🎯 **Goal:** `{target_n}` actions • ✅ **Pass:** `{pass_pct}%`"
    else:
        _, pass_pct, min_w, questions = EXAMS[phase_key]
        mode_line = f"📝 **Mode:** Overseen Exam Room • 📋 **Questions:** `{len(questions)}` • ✍️ **Min:** `{min_w}w` • ✅ **Pass:** `{pass_pct}%`"

    emb = discord.Embed(
        title=info["banner"],
        description=f"{cand_line}{req_line}{room_line}\n{mode_line}\n\n{info['intro']}",
        color=info["color"],
        timestamp=discord.utils.utcnow(),
    )
    emb.add_field(name="🎯 Phase Objectives & Requirements", value=info["objective"], inline=False)
    emb.add_field(name="⚠️ Strict Rules & Instant-Fail Policy", value=info["rules"], inline=False)
    emb.add_field(
        name="📊 Developer Oversight & Grading",
        value="Every response, timing metric, and action is logged and auto-graded, then transmitted with a full `.txt` dossier straight to **Chicago Crossfire Developers**.",
        inline=False,
    )

    if u:
        avatar_url = u.display_avatar.url
        emb.set_author(name=f"Chicago Crossfire Oversight — {u.display_name}", icon_url=avatar_url)
        emb.set_thumbnail(url=avatar_url)
        footer_prefix = f"MonitorKey:{phase_key} | CandidateID:{u.id}" if is_monitor else f"ExamKey:{phase_key} | CandidateID:{u.id}"
        emb.set_footer(text=f"{footer_prefix} • Chicago Crossfire Automated Overseer")
    else:
        if g and g.icon:
            emb.set_thumbnail(url=g.icon.url)
        emb.set_footer(text=f"Track:{phase_key} • Chicago Crossfire Automated Overseer")

    if phase_key == "phase5" and u and g:
        cand = gcfg(g.id)["candidates"].get(str(u.id), {})
        past = "\n".join(f"• `{h['exam']}`: **{h['score']}%** (`{h['verdict']}`)" for h in cand.get("history", [])[-6:]) or "*No prior phases recorded yet*"
        emb.add_field(name="📁 Prior Trial Phase History (Phases 1–4)", value=past, inline=False)

    return emb


# --- 2. 24/7 KEEP-ALIVE WEB SERVER & SELF-PINGER ---
async def run_web():
    app = web.Application()
    fn = lambda r: web.Response(text=f"Chicago Crossfire Exam Overseer 24/7 | Up:{int((time.time()-START_TIME)//60)}m | {BOT_STATUS}")
    app.router.add_get("/", fn)
    app.router.add_get("/health", fn)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()


async def self_ping():
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


# --- 3. WRITTEN EXAM GRADING ENGINE ---
def local_grade_exam(exam_key: str, answers: list[dict]) -> dict:
    """Strict built-in rubric grader that scores concept coverage, depth & anti-cheat flags."""
    title, pass_pct, min_words, questions = EXAMS[exam_key]
    notes, red_flags = [], []
    total_pts = 0.0

    for idx, ans in enumerate(answers):
        txt, low, words, elapsed = ans["text"], ans["text"].lower(), len(ans["text"].split()), ans["seconds"]
        concepts = questions[idx][1]
        hits = sum(1 for c in concepts if c in low)
        concept_ratio = min(1.0, hits / max(1, min(len(concepts), 4)))
        depth_ratio = min(1.0, words / max(min_words * 1.4, 30))
        pts = round((concept_ratio * 6.0) + (depth_ratio * 4.0), 1)

        if words >= 85 and elapsed < 6:
            red_flags.append(f"Q{idx+1}: Pasted {words} words in {elapsed:.1f}s (Possible Copy-Paste/AI)")
            pts = max(0.0, pts - 1.5)
        if any(f in low for f in AI_FLAGS):
            red_flags.append(f"Q{idx+1}: Robotic/AI phrasing detected")
            pts = max(0.0, pts - 2.0)
        if words < min_words:
            red_flags.append(f"Q{idx+1}: Low-effort answer ({words} words)")
            pts = min(pts, 4.0)

        total_pts += pts
        notes.append(f"Q{idx+1}: {pts}/10 ({hits}/{len(concepts)} key concepts, {words}w, {int(elapsed)}s)")

    pct = round((total_pts / (len(questions) * 10.0)) * 100, 1)
    verdict = "PASS" if pct >= pass_pct and len(red_flags) < 2 else ("BORDERLINE / INTERVIEW" if pct >= pass_pct - 8 else "FAIL")
    summary = f"Strict Rubric Score: {pct}% (Pass threshold: {pass_pct}%). {'Strong technical & policy alignment.' if verdict == 'PASS' else 'Missing critical protocols, depth, or triggered red flags.'}"
    return {"score_pct": pct, "verdict": verdict, "summary": summary, "red_flags": red_flags[:8], "breakdown": notes, "grader": "Local Strict Rubric"}


async def grade_exam(exam_key: str, member, answers: list[dict]) -> dict:
    """Grades the full exam using Gemini AI if configured, with automatic Local Rubric fallback."""
    local_res = local_grade_exam(exam_key, answers)
    if not GEMINI_KEY:
        return local_res

    title, pass_pct, min_words, questions = EXAMS[exam_key]
    qa_text = "\n\n".join(
        f"Q{i+1} ({questions[i][0]})\nExpected Concepts: {', '.join(questions[i][1])}\n"
        f"Candidate Answer ({a['seconds']:.1f}s, {len(a['text'].split())}w): {a['text'][:900]}"
        for i, a in enumerate(answers)
    )
    sys_p = (
        "You are the ruthless Chief Administrative & Developer Exam Grader for Chicago Crossfire (Roblox RP). "
        f"Exam: '{title}' | Pass Threshold: {pass_pct}% | Min Words: {min_words}. "
        "Grade STRICTLY. Penalize vague answers, bias, missing proof protocols, or AI-generated essays. "
        "Return ONLY valid JSON: {\"score_pct\": number (0-100), \"verdict\": \"PASS\"|\"BORDERLINE / INTERVIEW\"|\"FAIL\", "
        "\"summary\": \"2-3 sharp sentences for Developers\", \"red_flags\": [\"short red flag\"], "
        "\"breakdown\": [\"Q1: X/10 - brief note\"]}"
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
    body = {
        "contents": [{"parts": [{"text": f"CANDIDATE: {member} ({member.id})\n\n{qa_text}"}]}],
        "systemInstruction": {"parts": [{"text": sys_p}]},
        "generationConfig": {"temperature": 0.15, "responseMimeType": "application/json"},
    }
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=body, timeout=28) as r:
                if r.status == 200:
                    d = json.loads((await r.json())["candidates"][0]["content"]["parts"][0]["text"].strip())
                    ai_flags = list(d.get("red_flags", [])) + [f for f in local_res["red_flags"] if "Pasted" in f]
                    return {
                        "score_pct": float(d.get("score_pct", local_res["score_pct"])),
                        "verdict": str(d.get("verdict", local_res["verdict"])).upper(),
                        "summary": str(d.get("summary", local_res["summary"]))[:800],
                        "red_flags": ai_flags[:8],
                        "breakdown": [str(x)[:140] for x in d.get("breakdown", local_res["breakdown"])][:15],
                        "grader": "Gemini AI Strict Examiner",
                    }
    except Exception:
        pass
    return local_res

# =====================================================================
# PART 4 OF 5 — PASTE DIRECTLY BELOW PART 3 (FAR LEFT EDGE)
# =====================================================================
def build_exam_transcript(exam_key: str, member, answers: list[dict], res: dict, total_sec: float) -> bytes:
    """Exports full Q&A, timing forensics, and grading breakdown to a .txt file for Developers."""
    title, pass_pct, _, questions = EXAMS[exam_key]
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "================================================================",
        "   CHICAGO CROSSFIRE — OFFICIAL EXAM & GRADING REPORT           ",
        "================================================================",
        f"Exam        : {title}",
        f"Candidate   : {member} (ID: {member.id})",
        f"Completed   : {now} | Total Time: {int(total_sec // 60)}m {int(total_sec % 60)}s",
        f"Grader      : {res['grader']}",
        f"Final Score : {res['score_pct']}% (Pass Requirement: {pass_pct}%)",
        f"Verdict     : {res['verdict']}",
        f"Summary     : {res['summary']}",
        "Red Flags   : " + ("; ".join(res["red_flags"]) if res["red_flags"] else "None"),
        "================================================================\n",
    ]
    for i, a in enumerate(answers):
        b_note = res["breakdown"][i] if i < len(res["breakdown"]) else ""
        lines.append(f"--- QUESTION {i+1} ({int(a['seconds'])}s | {len(a['text'].split())} words) ---")
        lines.append(f"PROMPT : {questions[i][0]}")
        lines.append(f"ANSWER : {a['text']}")
        if b_note:
            lines.append(f"GRADE  : {b_note}")
        lines.append("")
    return "\n".join(lines).encode("utf-8")


def local_grade_monitor(phase_key: str, events: list[dict]) -> dict:
    """Grades real monitored ticket replies, public chat responses, and mod actions."""
    title, pass_pct, scope, _, _ = MONITOR_PHASES[phase_key]
    if not events:
        return {
            "score_pct": 0.0,
            "verdict": "FAIL",
            "summary": "Zero monitored ticket or moderation actions were recorded during oversight.",
            "red_flags": ["No activity recorded during active phase"],
            "breakdown": ["No recorded interactions"],
            "grader": "Local Live-Oversight Rubric",
        }

    total_pts = 0.0
    breakdown, red_flags = [], []

    for idx, ev in enumerate(events, 1):
        kind = ev["kind"]
        if kind == "mod_action":
            pts = 9.0
            total_pts += pts
            breakdown.append(f"#{idx} [Mod Action] {ev['action']} on {ev['target']} — {pts}/10")
            continue

        txt, low, words, delay, ch_name = ev["text"], ev["text"].lower(), len(ev["text"].split()), ev.get("delay_sec"), ev["channel"]
        pts = 5.5
        vocab = GOOD_TICKET_W if kind == "ticket_reply" else GOOD_MOD_W
        pts += min(2.5, sum(1 for w in vocab if w in low) * 0.9)
        if words >= 8:
            pts += 1.2
        elif words <= 3:
            pts -= 2.0
            red_flags.append(f"#{idx} (#{ch_name}): Very short/low-effort reply ('{txt[:40]}')")

        if delay is not None:
            if delay <= 90:
                pts += 0.8
            elif delay > 600:
                pts -= 0.8
                red_flags.append(f"#{idx} (#{ch_name}): Slow response time ({int(delay // 60)}m)")

        if any(rw in low for rw in RUDE_W):
            pts = max(0.0, pts - 5.0)
            red_flags.append(f"#{idx} (#{ch_name}): Unprofessional/hostile phrasing detected")

        pts = round(max(0.0, min(10.0, pts)), 1)
        total_pts += pts
        spd = f", {int(delay)}s reply" if delay is not None else ""
        breakdown.append(f"#{idx} [#{ch_name}] {pts}/10 ({words}w{spd})")

    pct = round((total_pts / (len(events) * 10.0)) * 100, 1)
    verdict = "PASS" if pct >= pass_pct and not any("Unprofessional" in r for r in red_flags) else ("BORDERLINE / INTERVIEW" if pct >= pass_pct - 10 else "FAIL")
    summary = f"Monitored {len(events)} real {scope} action(s) with an overall score of {pct}% (Pass: {pass_pct}%). {'Professional, timely, and thorough handling.' if verdict == 'PASS' else 'Needs improvement in depth, speed, or professionalism.'}"
    return {"score_pct": pct, "verdict": verdict, "summary": summary, "red_flags": red_flags[:8], "breakdown": breakdown[:15], "grader": "Local Live-Oversight Rubric"}


async def grade_monitor(phase_key: str, member, events: list[dict]) -> dict:
    """Uses Gemini AI (if enabled) or Local Live-Oversight Rubric to grade real mod actions."""
    local_res = local_grade_monitor(phase_key, events)
    if not GEMINI_KEY or not events:
        return local_res

    title, pass_pct, scope, _, _ = MONITOR_PHASES[phase_key]
    log_txt = "\n\n".join(
        (
            f"EVENT #{i+1} [{ev['kind'].upper()} in #{ev['channel']}] "
            f"(Response Delay: {int(ev['delay_sec']) if ev.get('delay_sec') is not None else 'N/A'}s)\n"
            f"PLAYER/CONTEXT ABOVE: {ev.get('context', 'N/A')}\n"
            f"MOD RESPONSE: {ev.get('text', ev.get('action', ''))}"
        )
        if ev["kind"] != "mod_action"
        else f"EVENT #{i+1} [MOD AUDIT ACTION]: {ev['action']} on {ev['target']} (Reason: {ev.get('reason', 'None')})"
        for i, ev in enumerate(events)
    )
    sys_p = (
        "You are the strict Moderation Oversight Evaluator for Chicago Crossfire (Roblox RP). "
        f"Evaluating '{title}' (Scope: {scope}, Pass Threshold: {pass_pct}%). "
        "Grade how the Trial Mod ACTUALLY responded to players in tickets/chats: check tone, speed, "
        "asking for Roblox username/proof/clips, citing rules accurately, avoiding bias/hostility, and avoiding lazy 2-word answers. "
        "Return ONLY valid JSON: {\"score_pct\": number (0-100), \"verdict\": \"PASS\"|\"BORDERLINE / INTERVIEW\"|\"FAIL\", "
        "\"summary\": \"2-3 direct sentences for Developers\", \"red_flags\": [\"short issue\"], "
        "\"breakdown\": [\"#1 (#channel): X/10 - brief note\"]}"
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
    body = {
        "contents": [{"parts": [{"text": f"MOD CANDIDATE: {member} ({member.id})\n\nLIVE MONITORED LOGS:\n{log_txt[:6000]}"}]}],
        "systemInstruction": {"parts": [{"text": sys_p}]},
        "generationConfig": {"temperature": 0.15, "responseMimeType": "application/json"},
    }
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=body, timeout=25) as r:
                if r.status == 200:
                    d = json.loads((await r.json())["candidates"][0]["content"]["parts"][0]["text"].strip())
                    return {
                        "score_pct": float(d.get("score_pct", local_res["score_pct"])),
                        "verdict": str(d.get("verdict", local_res["verdict"])).upper(),
                        "summary": str(d.get("summary", local_res["summary"]))[:800],
                        "red_flags": [str(x)[:160] for x in d.get("red_flags", local_res["red_flags"])][:8],
                        "breakdown": [str(x)[:140] for x in d.get("breakdown", local_res["breakdown"])][:15],
                        "grader": "Gemini AI Live Oversight Grader",
                    }
    except Exception:
        pass
    return local_res


def build_monitor_transcript(phase_key: str, member, events: list[dict], res: dict, total_sec: float) -> bytes:
    """Generates a full .txt dossier of every real ticket reply, chat message, and mod action observed."""
    title, pass_pct, scope, _, _ = MONITOR_PHASES[phase_key]
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "================================================================",
        "   CHICAGO CROSSFIRE — LIVE PHASE OVERSIGHT & GRADING DOSSIER   ",
        "================================================================",
        f"Phase       : {title} ({scope})",
        f"Candidate   : {member} (ID: {member.id})",
        f"Completed   : {now} | Oversight Duration: {int(total_sec // 60)}m {int(total_sec % 60)}s",
        f"Grader      : {res['grader']}",
        f"Final Score : {res['score_pct']}% (Pass Requirement: {pass_pct}%)",
        f"Verdict     : {res['verdict']}",
        f"Summary     : {res['summary']}",
        "Red Flags   : " + ("; ".join(res["red_flags"]) if res["red_flags"] else "None"),
        "================================================================\n",
    ]
    for i, ev in enumerate(events, 1):
        ts = datetime.datetime.fromtimestamp(ev["ts"], datetime.timezone.utc).strftime("%H:%M:%S UTC")
        if ev["kind"] == "mod_action":
            lines.append(f"[{ts}] EVENT #{i} — AUDIT MOD ACTION: {ev['action']} on {ev['target']}")
            lines.append(f"  Reason: {ev.get('reason', 'None')}\n")
        else:
            delay_s = f" | Reply Delay: {int(ev['delay_sec'])}s" if ev.get("delay_sec") is not None else ""
            lines.append(f"[{ts}] EVENT #{i} — {ev['kind'].upper()} in #{ev['channel']}{delay_s}")
            if ev.get("context"):
                lines.append(f"  Player/Context : {ev['context']}")
            lines.append(f"  Mod Response   : {ev['text']}")
            if i - 1 < len(res["breakdown"]):
                lines.append(f"  Grade Note     : {res['breakdown'][i - 1]}")
            lines.append("")
    return "\n".join(lines).encode("utf-8")


# --- 4. EXAM & LIVE OVERSIGHT LIFECYCLE ---
async def post_next_question(ch: discord.abc.Messageable, sess: dict) -> None:
    """Posts the next exam question with minimum word rules."""
    title, _, min_w, questions = EXAMS[sess["exam_key"]]
    idx = sess["q_idx"]
    sess["q_start"] = time.time()
    emb = discord.Embed(
        title=f"📝 Question {idx + 1} of {len(questions)} — {title}",
        description=f"**{questions[idx][0]}**",
        color=discord.Color.from_rgb(220, 53, 69) if sess["exam_key"] == "chief11" else discord.Color.blurple(),
    )
    emb.set_footer(text=f"Minimum {min_w} words required • Type your answer in chat below (or type 'cancel' to forfeit)")
    await ch.send(content=f"<@{sess['user_id']}>", embed=emb)


def parse_phase_request(msg: discord.Message, bot_id: int):
    """Parses chat requests formatted as: Name: @user / Phase: 1-5 (or Staff/Admin/Chief) / @Bot."""
    raw = re.sub(rf"<@!?{bot_id}>", "", msg.content or "").strip()
    phase_m = re.search(r"phase\s*[:\-]\s*([^\n]+)", raw, re.IGNORECASE)
    if not phase_m:
        return None, None

    val = phase_m.group(1).strip().lower()
    exam_key = None
    if "chief" in val or re.search(r"\b11\b", val):
        exam_key = "chief11"
    elif "full admin" in val or re.search(r"\b13\b", val):
        exam_key = "admin13"
    elif "admin" in val or re.search(r"\b10\b", val):
        exam_key = "admin10"
    elif "staff" in val:
        exam_key = "staff3"
    else:
        num_m = re.search(r"\b([1-5])\b", val)
        if num_m:
            exam_key = f"phase{num_m.group(1)}"

    other_mentions = [m for m in msg.mentions if m.id != bot_id]
    return (other_mentions[0] if other_mentions else msg.author), exam_key


async def send_candidate_dm_intro(u: discord.Member, emb: discord.Embed, extra_line: str = "") -> None:
    """Sends a private DM copy of the official Starting Message & Phase Introduction."""
    try:
        await u.send(content=f"🔥 **Your Chicago Crossfire Phase Has Officially Started!** {extra_line}".strip(), embed=emb)
    except Exception:
        pass


async def launch_exam_room(g: discord.Guild, u: discord.Member, exam_key: str, requested_by: discord.Member = None):
    """Creates a private overseen exam room, posts the Starting Message & Intro, and DMs the candidate."""
    for ch_id, s in ACTIVE_EXAMS.items():
        if s["guild_id"] == g.id and s["user_id"] == u.id:
            return None, None, f"⚠️ {u.mention} already has an active exam running in <#{ch_id}>!"

    c = gcfg(g.id)
    dev_role = g.get_role(c.get("dev_role", 0))
    cat = g.get_channel(c.get("exam_cat", 0))
    if not isinstance(cat, discord.CategoryChannel):
        cat = None

    title = EXAMS[exam_key][0]
    safe = re.sub(r"[^a-z0-9-]", "", u.name.lower())[:14] or "user"
    ow = {
        g.default_role: discord.PermissionOverwrite(view_channel=False),
        u: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        g.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, read_message_history=True, attach_files=True),
    }
    if dev_role:
        ow[dev_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

    try:
        exam_ch = await g.create_text_channel(name=f"exam-{exam_key}-{safe}"[:80], category=cat, overwrites=ow, topic=f"CCExam | Key:{exam_key} | UserID:{u.id}")
    except discord.Forbidden:
        return None, None, "❌ Bot needs **Manage Channels** permission to open the exam room!"

    sess = {"guild_id": g.id, "user_id": u.id, "exam_key": exam_key, "q_idx": 0, "answers": [], "started_at": time.time(), "q_start": time.time(), "warnings": 0}
    ACTIVE_EXAMS[exam_ch.id] = sess

    intro_emb = build_starting_intro_embed(g, u, exam_key, requested_by=requested_by, exam_ch=exam_ch, is_monitor=False)
    await exam_ch.send(
        content=f"📣 {u.mention} {dev_role.mention if dev_role else ''} — **Read your official Phase Starting Introduction below!**".strip(),
        embed=intro_emb,
        view=LiveExamControls(),
    )
    asyncio.create_task(send_candidate_dm_intro(u, intro_emb, f"Head into {exam_ch.mention} to begin!"))
    await asyncio.sleep(2)
    await post_next_question(exam_ch, sess)

    rep_ch = g.get_channel(c.get("report_ch", 0))
    if rep_ch:
        try:
            await rep_ch.send(f"👁️ **Live Exam Started:** {u.mention} (`{title}`) — Oversee live in {exam_ch.mention}.")
        except Exception:
            pass
    return exam_ch, intro_emb, f"✅ Phase request accepted for {u.mention} (**{title}**)! Private room opened: {exam_ch.mention}"


async def start_phase_monitor(g: discord.Guild, u: discord.Member, phase_key: str, req_ch, requested_by: discord.Member = None):
    """Starts live operational monitoring (Phases 1-3) and builds the full Starting Message & Intro."""
    mkey = (g.id, u.id)
    if mkey in ACTIVE_MONITORS:
        cur = ACTIVE_MONITORS[mkey]
        return None, f"⚠️ {u.mention} is already being monitored for **`{MONITOR_PHASES[cur['phase_key']][0]}`** (`{len(cur['events'])}/{cur['target']}` actions logged)."

    title, _, scope, target_n, _ = MONITOR_PHASES[phase_key]
    ACTIVE_MONITORS[mkey] = {
        "guild_id": g.id, "user_id": u.id, "phase_key": phase_key, "scope": scope, "target": target_n,
        "events": [], "started_at": time.time(), "req_ch_id": getattr(req_ch, "id", 0), "requested_by": requested_by.id if requested_by else u.id,
    }
    intro_emb = build_starting_intro_embed(g, u, phase_key, requested_by=requested_by, is_monitor=True)
    asyncio.create_task(send_candidate_dm_intro(u, intro_emb, "Live Oversight is now active on your account!"))

    rep_ch = g.get_channel(gcfg(g.id).get("report_ch", 0))
    if rep_ch:
        try:
            await rep_ch.send(f"👁️ **Live Oversight Started:** Monitoring {u.mention} for **`{title}`** (`{scope}`).")
        except Exception:
            pass
    return intro_emb, f"✅ Starting message sent & Live Oversight active for {u.mention} (`{title}`)!"



