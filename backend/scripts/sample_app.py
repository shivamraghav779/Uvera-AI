"""A scripted application: what a model would answer at each generation stage.

"Hirewell" is a small recruitment product. Each constant below is the JSON one
pipeline stage expects, written by hand. ``reply`` picks the right one for a
prompt, so the real pipeline (planning, assembly, validation, quality review)
can run end to end with no model:

    - the backend's tests use it as a deterministic model double
    - ``scripts.dev_llm`` serves it over HTTP for offline development
    - ``scripts.export_contract`` exports the assembled document as the
      application fixture the frontend is tested against

THIS IS NOT A MODEL. It answers a handful of recognisable requests.
"""

import json
import re
from typing import Any

Json = dict[str, Any]

APP_WORDS = re.compile(
    r"\b(app|application|platform|saas|website|site|product|tool|portal|marketplace|store|crm)\b"
)

BLUEPRINT: Json = {
    "scope": "application",
    "name": "Hirewell",
    "category": "Recruitment SaaS",
    "description": (
        "An AI-assisted hiring workspace where recruiters open roles, review ranked "
        "candidates, move them through a pipeline and schedule interviews."
    ),
    "target_users": ["In-house recruiters", "Hiring managers"],
    "goals": ["Fill roles faster", "Keep every candidate moving", "See hiring health at a glance"],
    "features": [
        "AI candidate screening",
        "Hiring pipeline board",
        "Interview scheduling",
        "Hiring analytics",
    ],
    "navigation_style": "sidebar",
    "home": "dashboard",
    "screens": [
        {
            "id": "dashboard",
            "name": "Dashboard",
            "route": "/",
            "type": "dashboard",
            "purpose": "See open roles, pipeline health and what needs attention today.",
            "user_goal": "Know where hiring stands in ten seconds.",
            "in_navigation": True,
            "icon": "dashboard",
        },
        {
            "id": "jobs",
            "name": "Jobs",
            "route": "/jobs",
            "type": "listing",
            "purpose": "Browse and manage open roles.",
            "in_navigation": True,
            "icon": "briefcase",
            "entity": "jobs",
        },
        {
            "id": "job_new",
            "name": "Create job",
            "route": "/jobs/new",
            "type": "form",
            "purpose": "Open a new role.",
            "in_navigation": False,
            "entity": "jobs",
        },
        {
            "id": "candidates",
            "name": "Candidates",
            "route": "/candidates",
            "type": "listing",
            "purpose": "Review everyone who applied, ranked by match.",
            "in_navigation": True,
            "icon": "users",
            "entity": "candidates",
        },
        {
            "id": "candidate_detail",
            "name": "Candidate",
            "route": "/candidates/:candidateId",
            "type": "detail",
            "purpose": "Review one candidate and decide the next step.",
            "in_navigation": False,
            "entity": "candidates",
        },
        {
            "id": "pipeline",
            "name": "Pipeline",
            "route": "/pipeline",
            "type": "listing",
            "purpose": "Move candidates through the hiring stages.",
            "in_navigation": True,
            "icon": "kanban",
            "entity": "candidates",
        },
        {
            "id": "interviews",
            "name": "Interviews",
            "route": "/interviews",
            "type": "calendar",
            "purpose": "See upcoming interviews.",
            "in_navigation": True,
            "icon": "calendar",
            "entity": "interviews",
        },
    ],
    "entities": [
        {
            "name": "jobs",
            "label": "Jobs",
            "description": "Roles the company is hiring for.",
            "title_field": "title",
            "fields": [
                {"key": "title", "label": "Title", "type": "text"},
                {"key": "department", "label": "Department", "type": "text"},
                {"key": "location", "label": "Location", "type": "text"},
                {
                    "key": "status",
                    "label": "Status",
                    "type": "status",
                    "options": ["Open", "Paused", "Closed"],
                },
                {"key": "openings", "label": "Openings", "type": "number"},
                {"key": "posted_on", "label": "Posted", "type": "date"},
            ],
        },
        {
            "name": "candidates",
            "label": "Candidates",
            "description": "People who applied to a role.",
            "title_field": "name",
            "fields": [
                {"key": "name", "label": "Name", "type": "text"},
                {"key": "role", "label": "Applied for", "type": "text"},
                {"key": "job_id", "label": "Job", "type": "reference", "references": "jobs"},
                {
                    "key": "stage",
                    "label": "Stage",
                    "type": "status",
                    "options": ["Applied", "Screening", "Interview", "Offer", "Hired"],
                },
                {"key": "match_score", "label": "Match", "type": "percent"},
                {"key": "location", "label": "Location", "type": "text"},
                {"key": "email", "label": "Email", "type": "email"},
                {"key": "experience_years", "label": "Experience (years)", "type": "number"},
                {"key": "applied_on", "label": "Applied", "type": "date"},
            ],
        },
        {
            "name": "interviews",
            "label": "Interviews",
            "description": "Scheduled conversations with candidates.",
            "title_field": "candidate_name",
            "fields": [
                {
                    "key": "candidate_id",
                    "label": "Candidate",
                    "type": "reference",
                    "references": "candidates",
                },
                {"key": "candidate_name", "label": "Candidate name", "type": "text"},
                {"key": "interviewer", "label": "Interviewer", "type": "text"},
                {"key": "date", "label": "Date", "type": "date"},
                {"key": "time", "label": "Time", "type": "time"},
                {
                    "key": "format",
                    "label": "Format",
                    "type": "status",
                    "options": ["Video", "Onsite", "Phone"],
                },
            ],
        },
        {
            "name": "hiring_by_month",
            "label": "Hiring by month",
            "description": "Applications received and hires made per month.",
            "title_field": "month",
            "fields": [
                {"key": "month", "label": "Month", "type": "text"},
                {"key": "applications", "label": "Applications", "type": "number"},
                {"key": "hires", "label": "Hires", "type": "number"},
            ],
        },
    ],
    "workflows": [
        {"name": "Review a candidate", "steps": ["candidates", "candidate_detail", "interviews"]},
        {"name": "Open a role", "steps": ["jobs", "job_new", "jobs"]},
    ],
}

DESIGN: Json = {
    "style": "premium_saas",
    "summary": "A calm, confident workspace with generous spacing and one indigo accent.",
    "mood": ["polished", "trustworthy", "focused"],
    "rationale": "Recruiters live in this tool all day; it should feel dependable, not loud.",
    "mode": "light",
    "palette": "indigo_mist",
    "imagery": "product",
    "visual_language": (
        "Bright, natural-light photographs of small teams at work in modern offices; warm "
        "neutral tones with a hint of indigo; candid, never staged."
    ),
    "layout": "Figures first, then the main content beside its support in 8/4 splits.",
    "effects": ["reveal", "hover_lift"],
    "navigation_style": "sidebar",
}

# What the director answers when asked to make the application "more premium".
PREMIUM_DESIGN: Json = {
    "style": "luxury",
    "summary": "A restrained, premium look: serif display headings, wide margins, warm ink.",
    "mood": ["exclusive", "restrained", "timeless"],
    "mode": "light",
    "palette": "stone_ink",
    "imagery": "photography",
    "visual_language": "Quiet editorial photographs in warm neutral light.",
    "layout": "Fewer elements, more space around each.",
    "effects": ["reveal"],
}

DARK_DESIGN: Json = {**DESIGN, "mode": "dark", "palette": "slate_dark", "summary": "Dark mode."}

RECORDS: dict[str, list[Json]] = {
    "jobs": [
        {"id": "job-101", "title": "Senior Product Designer", "department": "Design",
         "location": "Berlin", "status": "Open", "openings": 2, "posted_on": "2026-09-02"},
        {"id": "job-102", "title": "Backend Engineer, Payments", "department": "Engineering",
         "location": "Remote (EU)", "status": "Open", "openings": 3, "posted_on": "2026-08-21"},
        {"id": "job-103", "title": "Customer Success Lead", "department": "Customer",
         "location": "Lisbon", "status": "Paused", "openings": 1, "posted_on": "2026-07-30"},
        {"id": "job-104", "title": "Data Analyst", "department": "Operations",
         "location": "Amsterdam", "status": "Open", "openings": 1, "posted_on": "2026-09-15"},
        {"id": "job-105", "title": "Head of People", "department": "People",
         "location": "London", "status": "Closed", "openings": 1, "posted_on": "2026-05-11"},
    ],
    "candidates": [
        {"id": "cand-001", "name": "Amara Okafor", "role": "Senior Product Designer",
         "job_id": "job-101", "stage": "Interview", "match_score": 92, "location": "Berlin",
         "email": "amara.okafor@mailbox.org", "experience_years": 8, "applied_on": "2026-09-20"},
        {"id": "cand-002", "name": "Jonas Lindqvist", "role": "Backend Engineer, Payments",
         "job_id": "job-102", "stage": "Screening", "match_score": 84, "location": "Stockholm",
         "email": "jonas.lindqvist@proton.me", "experience_years": 6, "applied_on": "2026-09-24"},
        {"id": "cand-003", "name": "Mei Tanaka", "role": "Data Analyst",
         "job_id": "job-104", "stage": "Applied", "match_score": 77, "location": "Amsterdam",
         "email": "mei.tanaka@fastmail.com", "experience_years": 3, "applied_on": "2026-09-28"},
        {"id": "cand-004", "name": "Rafael Mendes", "role": "Backend Engineer, Payments",
         "job_id": "job-102", "stage": "Offer", "match_score": 95, "location": "Porto",
         "email": "rafael.mendes@hey.com", "experience_years": 9, "applied_on": "2026-09-05"},
        {"id": "cand-005", "name": "Priya Raman", "role": "Senior Product Designer",
         "job_id": "job-101", "stage": "Applied", "match_score": 71, "location": "London",
         "email": "priya.raman@gmail.com", "experience_years": 5, "applied_on": "2026-09-29"},
        {"id": "cand-006", "name": "Tomasz Kowalski", "role": "Data Analyst",
         "job_id": "job-104", "stage": "Interview", "match_score": 88, "location": "Warsaw",
         "email": "t.kowalski@outlook.com", "experience_years": 4, "applied_on": "2026-09-18"},
        {"id": "cand-007", "name": "Leila Haddad", "role": "Backend Engineer, Payments",
         "job_id": "job-102", "stage": "Hired", "match_score": 97, "location": "Paris",
         "email": "leila.haddad@pm.me", "experience_years": 11, "applied_on": "2026-08-25"},
        {"id": "cand-008", "name": "Noah Fischer", "role": "Senior Product Designer",
         "job_id": "job-101", "stage": "Screening", "match_score": 80, "location": "Munich",
         "email": "noah.fischer@posteo.de", "experience_years": 7, "applied_on": "2026-09-26"},
    ],
    "interviews": [
        {"id": "int-01", "candidate_id": "cand-001", "candidate_name": "Amara Okafor",
         "interviewer": "Hannah Weiss", "date": "2026-10-07", "time": "10:00", "format": "Video"},
        {"id": "int-02", "candidate_id": "cand-006", "candidate_name": "Tomasz Kowalski",
         "interviewer": "Daniel Osei", "date": "2026-10-07", "time": "14:30", "format": "Onsite"},
        {"id": "int-03", "candidate_id": "cand-004", "candidate_name": "Rafael Mendes",
         "interviewer": "Sofia Marin", "date": "2026-10-08", "time": "11:15", "format": "Video"},
        {"id": "int-04", "candidate_id": "cand-002", "candidate_name": "Jonas Lindqvist",
         "interviewer": "Hannah Weiss", "date": "2026-10-09", "time": "09:30", "format": "Phone"},
    ],
    "hiring_by_month": [
        {"id": "m-05", "month": "May", "applications": 86, "hires": 3},
        {"id": "m-06", "month": "Jun", "applications": 104, "hires": 4},
        {"id": "m-07", "month": "Jul", "applications": 97, "hires": 2},
        {"id": "m-08", "month": "Aug", "applications": 131, "hires": 5},
        {"id": "m-09", "month": "Sep", "applications": 158, "hires": 6},
    ],
    "offers": [
        {"id": "off-01", "candidate_name": "Rafael Mendes", "role": "Backend Engineer, Payments",
         "salary": 92000, "status": "Sent", "sent_on": "2026-10-01"},
        {"id": "off-02", "candidate_name": "Leila Haddad", "role": "Backend Engineer, Payments",
         "salary": 104000, "status": "Accepted", "sent_on": "2026-09-12"},
        {"id": "off-03", "candidate_name": "Amara Okafor", "role": "Senior Product Designer",
         "salary": 88000, "status": "Draft", "sent_on": "2026-10-04"},
    ],
}  # fmt: skip

SCREEN_PLANS: dict[str, Json] = {
    "dashboard": {
        "screen_id": "dashboard",
        "width": "contained",
        "composition": "Figures across the top, the hiring trend beside recent applicants.",
        "sections": [
            {"pattern": "stats.strip", "purpose": "Hiring health at a glance",
             "priority": "primary"},
            {"pattern": "chart", "purpose": "Applications and hires per month", "span": 8,
             "entity": "hiring_by_month"},
            {"pattern": "collection.compact", "purpose": "Newest applicants", "span": 4,
             "entity": "candidates"},
            {"pattern": "media.image_right", "purpose": "This week in hiring", "image": True,
             "image_brief": "A small hiring team reviewing candidates together"},
        ],
        "responsive": "The chart and the list stack; figures wrap two per row.",
    },
    "jobs": {
        "screen_id": "jobs",
        "width": "contained",
        "composition": "Counts, then every role as a table that opens the candidates.",
        "sections": [
            {"pattern": "stats.strip", "purpose": "How many roles are open", "entity": "jobs"},
            {"pattern": "table", "purpose": "All roles", "priority": "primary", "entity": "jobs"},
        ],
    },
    "job_new": {
        "screen_id": "job_new",
        "width": "narrow",
        "composition": "One focused form.",
        "sections": [{"pattern": "form", "purpose": "Describe the role", "priority": "primary",
                      "entity": "jobs"}],
    },
    "candidates": {
        "screen_id": "candidates",
        "width": "contained",
        "composition": "A stage filter over the ranked list of candidates.",
        "sections": [
            {"pattern": "collection.list", "purpose": "Everyone who applied, best match first",
             "priority": "primary", "entity": "candidates"},
        ],
    },
    "candidate_detail": {
        "screen_id": "candidate_detail",
        "width": "contained",
        "composition": "Who this is across the top, profile beside their interviews.",
        "sections": [
            {"pattern": "profile_header.banner", "purpose": "Identify the candidate and act",
             "priority": "primary", "entity": "candidates"},
            {"pattern": "detail.grid", "purpose": "Profile facts", "span": 8,
             "entity": "candidates"},
            {"pattern": "calendar", "purpose": "Their interviews", "span": 4,
             "entity": "interviews"},
        ],
    },
    "pipeline": {
        "screen_id": "pipeline",
        "width": "wide",
        "composition": "The board is the screen.",
        "sections": [{"pattern": "kanban", "purpose": "Candidates by stage",
                      "priority": "primary", "entity": "candidates"}],
    },
    "interviews": {
        "screen_id": "interviews",
        "width": "contained",
        "composition": "The agenda beside the candidates in the interview stage.",
        "sections": [
            {"pattern": "calendar", "purpose": "Upcoming interviews", "priority": "primary",
             "span": 8, "entity": "interviews"},
            {"pattern": "collection.compact", "purpose": "Candidates to schedule", "span": 4,
             "entity": "candidates"},
        ],
    },
    "offers": {
        "screen_id": "offers",
        "width": "contained",
        "composition": "Open offers as a table.",
        "sections": [
            {"pattern": "stats.strip", "purpose": "Offers out", "entity": "offers"},
            {"pattern": "table", "purpose": "All offers", "priority": "primary",
             "entity": "offers"},
        ],
    },
}  # fmt: skip

ASSETS: Json = {
    "assets": [
        {
            "id": "hiring_team",
            "decision": "generate",
            "kind": "photo",
            "prompt": (
                "A candid photograph of three colleagues around a laptop in a bright modern "
                "office, reviewing candidate profiles together, natural window light, warm "
                "neutral tones with a hint of indigo, shallow depth of field, space on the left."
            ),
            "query": "team reviewing candidates office",
            "alt": "Three colleagues reviewing candidate profiles at a laptop",
            "width": 1200,
            "height": 900,
            "usage": "Dashboard: this week in hiring",
            "screen_id": "dashboard",
        }
    ]
}

INTERACTIONS: Json = {
    "interactions": [
        {"id": "open_candidate", "label": "Open candidate", "type": "navigate",
         "screen_id": "candidates", "trigger": "A candidate's row", "entity": "candidates",
         "target_route": "/candidates/:candidateId", "result": "Shows the candidate"},
        {"id": "create_job", "label": "Create job", "type": "record_create",
         "screen_id": "job_new", "trigger": "The form", "entity": "jobs",
         "target_route": "/jobs", "result": "Adds the role and returns to the list"},
        {"id": "shortlist_candidate", "label": "Move to interview", "type": "record_update",
         "screen_id": "candidate_detail", "trigger": "Header button", "entity": "candidates",
         "set_field": "stage", "set_value": "Interview", "result": "The candidate's stage changes"},
        {"id": "move_candidate", "label": "Move between stages", "type": "record_update",
         "screen_id": "pipeline", "trigger": "Dragging a card", "entity": "candidates",
         "set_field": "stage", "result": "The candidate's stage changes"},
    ]
}  # fmt: skip

_OPEN_CANDIDATE: Json = {"type": "navigate", "payload": {"to": "/candidates/:candidateId"}}
_CANDIDATE_CARD: Json = {
    "title": "name", "subtitle": "role", "badge": "stage", "avatar": True,
    "meta": [{"key": "match_score", "label": "Match", "format": "percent"}],
}  # fmt: skip
_ONE_CANDIDATE: Json = {"dataset": "candidates", "where": [{"field": "id", "param": "candidateId"}]}

# Ids are deliberately not prefixed with the screen id: the assembler does that.
SCREENS: dict[str, list[Json]] = {
    "dashboard": [
        {
            "type": "stats", "id": "kpis", "variant": "strip", "style": {"priority": "primary"},
            "items": [
                {"label": "Open roles", "icon": "briefcase",
                 "data_source": {"dataset": "jobs", "field": "id", "aggregate": "count",
                                 "where": [{"field": "status", "value": "Open"}]}},
                {"label": "Candidates", "icon": "users",
                 "data_source": {"dataset": "candidates", "field": "id", "aggregate": "count"}},
                {"label": "In interview", "icon": "calendar",
                 "data_source": {"dataset": "candidates", "field": "id", "aggregate": "count",
                                 "where": [{"field": "stage", "value": "Interview"}]}},
                {"label": "Average match", "icon": "target", "format": "percent",
                 "data_source": {"dataset": "candidates", "field": "match_score",
                                 "aggregate": "avg"}},
            ],
        },
        {
            "type": "chart", "id": "hiring_trend", "title": "Applications and hires",
            "chart_type": "area", "x_key": "month", "y_keys": ["applications", "hires"],
            "data_source": {"dataset": "hiring_by_month"}, "layout": {"span": 8, "height": "md"},
        },
        {
            "type": "collection", "id": "recent_applicants", "variant": "compact",
            "title": "Newest applicants", "layout": {"span": 4},
            "data_source": {"dataset": "candidates", "limit": 5,
                            "sort": {"field": "applied_on", "direction": "desc"}},
            "fields": _CANDIDATE_CARD, "item_action": _OPEN_CANDIDATE,
        },
        {
            "type": "media", "id": "this_week", "variant": "image_right",
            "eyebrow": "This week", "title": "Four interviews, one offer out",
            "body": "Rafael Mendes has an offer for Backend Engineer, Payments. Two design "
                    "candidates are waiting for a first conversation.",
            "bullets": ["Review the two newest design applicants", "Confirm Thursday's panel"],
            "image": "hiring_team",
            "actions": [{"label": "Open the pipeline",
                         "action": {"type": "navigate", "payload": {"to": "/pipeline"}}}],
        },
    ],
    "jobs": [
        {
            "type": "stats", "id": "counts", "variant": "strip",
            "items": [
                {"label": "Open", "data_source": {"dataset": "jobs", "field": "id",
                 "aggregate": "count", "where": [{"field": "status", "value": "Open"}]}},
                {"label": "Paused", "data_source": {"dataset": "jobs", "field": "id",
                 "aggregate": "count", "where": [{"field": "status", "value": "Paused"}]}},
                {"label": "Openings", "data_source": {"dataset": "jobs", "field": "openings",
                 "aggregate": "sum"}},
            ],
            "layout": {"span": 9},
        },
        {
            "type": "button", "id": "new_job", "label": "Create job", "layout": {"span": 3},
            "action": {"type": "navigate", "payload": {"to": "/jobs/new"}},
        },
        {
            "type": "table", "id": "jobs_table", "title": "All roles",
            "style": {"priority": "primary"},
            "columns": [
                {"key": "title", "label": "Role"},
                {"key": "department", "label": "Department"},
                {"key": "location", "label": "Location"},
                {"key": "status", "label": "Status"},
                {"key": "openings", "label": "Openings", "format": "number", "align": "right"},
                {"key": "posted_on", "label": "Posted", "format": "date"},
            ],
            "data_source": {"dataset": "jobs", "sort": {"field": "posted_on", "direction": "desc"}},
            "row_action": {"type": "navigate", "payload": {"to": "/candidates"}},
        },
    ],
    "job_new": [
        {
            "type": "form", "id": "job_form", "title": "Describe the role",
            "fields": [
                {"type": "input", "id": "title", "name": "title", "label": "Title",
                 "placeholder": "Senior Product Designer", "required": True},
                {"type": "input", "id": "department", "name": "department",
                 "label": "Department", "layout": {"span": 6}},
                {"type": "input", "id": "location", "name": "location", "label": "Location",
                 "layout": {"span": 6}},
                {"type": "select", "id": "status", "name": "status", "label": "Status",
                 "default_value": "Open", "layout": {"span": 6},
                 "options": [{"label": "Open", "value": "Open"},
                             {"label": "Paused", "value": "Paused"}]},
                {"type": "input", "id": "openings", "name": "openings", "label": "Openings",
                 "input_type": "number", "default_value": 1, "layout": {"span": 6}},
            ],
            "submit_label": "Create job",
            "submit_action": {"type": "record_create",
                              "payload": {"entity": "jobs", "navigate_to": "/jobs"}},
        },
        {
            "type": "button", "id": "cancel", "label": "Back to jobs", "variant": "ghost",
            "action": {"type": "navigate", "payload": {"to": "/jobs"}},
        },
    ],
    "candidates": [
        {
            "type": "select", "id": "stage_filter", "name": "stage", "label": "Stage",
            "layout": {"span": 4},
            "options": [{"label": s, "value": s}
                        for s in ("Applied", "Screening", "Interview", "Offer", "Hired")],
            "on_change": {"type": "filter",
                          "payload": {"dataset": "candidates", "field": "stage",
                                      "target": "candidate_list"}},
        },
        {
            "type": "collection", "id": "candidate_list", "variant": "list",
            "title": "All candidates", "style": {"priority": "primary"},
            "data_source": {"dataset": "candidates",
                            "sort": {"field": "match_score", "direction": "desc"}},
            "fields": {**_CANDIDATE_CARD,
                       "meta": [{"key": "match_score", "label": "Match", "format": "percent"},
                                {"key": "location", "label": "Location"}]},
            "item_action": _OPEN_CANDIDATE,
        },
    ],
    "candidate_detail": [
        {
            "type": "profile_header", "id": "header", "variant": "banner",
            "style": {"priority": "primary"}, "data_source": _ONE_CANDIDATE,
            "fields": {**_CANDIDATE_CARD,
                       "meta": [{"key": "location", "label": "Location"},
                                {"key": "match_score", "label": "Match", "format": "percent"},
                                {"key": "experience_years", "label": "Experience (years)",
                                 "format": "number"}]},
            "actions": [
                {"label": "Move to interview",
                 "action": {"type": "record_update",
                            "payload": {"entity": "candidates", "set_field": "stage",
                                        "set_value": "Interview", "key_param": "candidateId"}}},
                {"label": "All candidates", "variant": "ghost",
                 "action": {"type": "navigate", "payload": {"to": "/candidates"}}},
            ],
        },
        {
            "type": "detail", "id": "profile", "title": "Profile", "variant": "grid",
            "columns": 2, "layout": {"span": 8}, "data_source": _ONE_CANDIDATE,
            "fields": [
                {"key": "email", "label": "Email"},
                {"key": "role", "label": "Applied for"},
                {"key": "stage", "label": "Stage"},
                {"key": "applied_on", "label": "Applied", "format": "date"},
            ],
        },
        {
            "type": "calendar", "id": "their_interviews", "title": "Interviews",
            "layout": {"span": 4},
            "data_source": {"dataset": "interviews",
                            "where": [{"field": "candidate_id", "param": "candidateId"}]},
            "date_field": "date", "time_field": "time", "title_field": "interviewer",
            "badge_field": "format",
        },
    ],
    "pipeline": [
        {
            "type": "kanban", "id": "board", "style": {"priority": "primary"},
            "data_source": {"dataset": "candidates"}, "group_by": "stage",
            "columns": [
                {"value": "Applied", "label": "Applied"},
                {"value": "Screening", "label": "Screening"},
                {"value": "Interview", "label": "Interview", "tone": "info"},
                {"value": "Offer", "label": "Offer", "tone": "warning"},
                {"value": "Hired", "label": "Hired", "tone": "success"},
            ],
            "fields": _CANDIDATE_CARD, "item_action": _OPEN_CANDIDATE,
            "move_action": {"type": "record_update",
                            "payload": {"entity": "candidates", "set_field": "stage"}},
        },
    ],
    "interviews": [
        {
            "type": "calendar", "id": "agenda", "title": "Upcoming interviews",
            "style": {"priority": "primary"}, "layout": {"span": 8},
            "data_source": {"dataset": "interviews", "sort": {"field": "date", "direction": "asc"}},
            "date_field": "date", "time_field": "time", "title_field": "candidate_name",
            "subtitle_field": "interviewer", "badge_field": "format",
            "item_action": {"type": "navigate",
                            "payload": {"to": "/candidates/:candidateId",
                                        "from_field": "candidate_id"}},
        },
        {
            "type": "collection", "id": "to_schedule", "variant": "compact",
            "title": "In the interview stage", "layout": {"span": 4},
            "data_source": {"dataset": "candidates",
                            "where": [{"field": "stage", "value": "Interview"}]},
            "fields": _CANDIDATE_CARD, "item_action": _OPEN_CANDIDATE,
        },
    ],
    "offers": [
        {
            "type": "stats", "id": "offer_counts", "variant": "strip",
            "items": [
                {"label": "Offers", "data_source": {"dataset": "offers", "field": "id",
                                                    "aggregate": "count"}},
                {"label": "Average salary", "format": "currency",
                 "data_source": {"dataset": "offers", "field": "salary", "aggregate": "avg"}},
            ],
        },
        {
            "type": "table", "id": "offers_table", "title": "All offers",
            "columns": [
                {"key": "candidate_name", "label": "Candidate"},
                {"key": "role", "label": "Role"},
                {"key": "salary", "label": "Salary", "format": "currency", "align": "right"},
                {"key": "status", "label": "Status"},
                {"key": "sent_on", "label": "Sent", "format": "date"},
            ],
            "data_source": {"dataset": "offers"},
        },
    ],
}  # fmt: skip

# What the generator answers when asked to redesign the dashboard: the same content,
# recomposed around the pipeline instead of the trend.
REDESIGNED_DASHBOARD: list[Json] = [
    SCREENS["dashboard"][0],
    {
        "type": "chart", "id": "stage_split", "title": "Candidates by stage",
        "chart_type": "bar", "x_key": "stage", "y_keys": ["count"],
        "data_source": {"dataset": "candidates", "group_by": "stage"},
        "layout": {"span": 7, "height": "md"},
    },
    {**SCREENS["dashboard"][2], "layout": {"span": 5}},
    {**SCREENS["dashboard"][1], "layout": {"span": 12, "height": "md"}},
]  # fmt: skip

ADDITION: Json = {
    "screens": [
        {
            "id": "offers",
            "name": "Offers",
            "route": "/offers",
            "type": "listing",
            "purpose": "Track offers that are out.",
            "in_navigation": True,
            "icon": "award",
            "entity": "offers",
        }
    ],
    "entities": [
        {
            "name": "offers",
            "label": "Offers",
            "title_field": "candidate_name",
            "fields": [
                {"key": "candidate_name", "label": "Candidate", "type": "text"},
                {"key": "role", "label": "Role", "type": "text"},
                {"key": "salary", "label": "Salary", "type": "currency"},
                {"key": "status", "label": "Status", "type": "status",
                 "options": ["Draft", "Sent", "Accepted", "Declined"]},
                {"key": "sent_on", "label": "Sent", "type": "date"},
            ],
        }
    ],
}  # fmt: skip


def section(content: str, title: str) -> str:
    """Text of one titled block of a prompt (blocks are separated by blank lines)."""
    match = re.search(
        rf"(?:^|\n\n){re.escape(title)}[^\n]*\n(.*?)(?=\n\n[A-Z][^\n]*\n|\Z)", content, re.S
    )
    return match.group(1).strip() if match else ""


def _route(prompt: str) -> Json:
    request = section(prompt, "User request").lower()
    outline = section(prompt, "Application outline")
    if re.search(r"go back|restore|undo|revert|compare|original", request):
        return {"level": "component", "intent": "edit"}
    if re.search(r"\bredesign\b|\brework\b|\brebuild\b", request):
        named = next(
            (
                screen_id
                for screen_id in re.findall(r"- screen (\w+)", outline)
                if screen_id.replace("_", " ") in request
            ),
            None,
        )
        return {"level": "screen", "intent": "redesign_screen", "screen_id": named}
    if re.search(r"\badd\b.*\b(screen|section|page|area)\b", request):
        return {"level": "application", "intent": "add_screen"}
    if re.search(
        r"premium|minimal|playful|editorial|dark|light mode|whole app|entire app", request
    ):
        return {"level": "application", "intent": "restyle"}
    return {"level": "component", "intent": "edit"}


def reply(system: str, prompt: str) -> str | None:
    """The scripted answer of whichever generation stage ``system`` belongs to.

    Returns ``None`` for prompts of other stages (the single-view and edit
    prompts, which ``scripts.dev_llm`` answers itself).
    """
    if system.startswith("You are the product architect"):
        idea = section(prompt, "User idea").lower()
        if APP_WORDS.search(idea):
            return json.dumps(BLUEPRINT)
        return json.dumps({"scope": "single_view", "name": "View", "description": idea[:200]})
    if system.startswith("You are the design director"):
        change = section(prompt, "Change requested").lower()
        if "dark" in change:
            return json.dumps(DARK_DESIGN)
        return json.dumps(PREMIUM_DESIGN if change else DESIGN)
    if system.startswith("You write the sample data"):
        wanted = re.findall(r"^- (\w+) \(", section(prompt, "Entities to fill"), re.M)
        return json.dumps(
            {"entities": [{"name": name, "records": RECORDS.get(name, [])} for name in wanted]}
        )
    if system.startswith("You are the visual composition planner"):
        wanted = re.findall(r"^- (\w+) \(", section(prompt, "Screens"), re.M)
        return json.dumps({"screens": [SCREEN_PLANS[s] for s in wanted if s in SCREEN_PLANS]})
    if system.startswith("You are the art director"):
        return json.dumps(ASSETS)
    if system.startswith("You plan what people can do"):
        return json.dumps(INTERACTIONS)
    if system.startswith("You are a senior product designer"):
        screen_id = re.search(r"\(id (\w+),", section(prompt, "Screen plan"))
        key = screen_id.group(1) if screen_id else ""
        redesign = "Change requested" in prompt and key == "dashboard"
        children = REDESIGNED_DASHBOARD if redesign else SCREENS.get(key, [])
        return json.dumps({"children": children})
    if system.startswith("You route an edit request"):
        return json.dumps(_route(prompt))
    if system.startswith("You extend an existing application"):
        return json.dumps(ADDITION)
    return None
