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

