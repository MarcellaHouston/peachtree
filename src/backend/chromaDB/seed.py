from backend.chromaDB.chroma_db import store_talking_point

USER_ID = "user_abc123"

# UNIX timestamp far in the future (year 9999) — used for static traits
# so they always pass the end_timestamp filter.
NEVER_EXPIRES = 253402300799

# Reference timestamps used to create a mix of expired and still-valid talking points.
JAN_2025 = 1735707600   # Jan 1 2025 — expired
DEC_2024 = 1733029200   # Dec 1 2024 — expired
APR_2027 = 1806552000   # Apr 1 2027 — still valid
JUN_2027 = 1811822400   # Jun 1 2027 — still valid

talking_points = [
    # ── Static traits (always relevant, never expire) ─────────────────────────
    {
        "document": "User is 6 feet 2 inches tall.",
        "verbose_summary": "The user mentioned their height is 6'2\" (188 cm) when discussing fitness goals. This is a permanent physical attribute.",
        "static_trait": True,
        "end_timestamp": NEVER_EXPIRES,
    },
    {
        "document": "User prefers to be called 'Alex' rather than their full name.",
        "verbose_summary": "During onboarding, the user said they go by 'Alex' and dislike being addressed by their full name Alexandra.",
        "static_trait": True,
        "end_timestamp": NEVER_EXPIRES,
    },
    {
        "document": "User is lactose intolerant.",
        "verbose_summary": "User mentioned they are lactose intolerant and avoid dairy products. This affects nutrition and meal recommendations.",
        "static_trait": True,
        "end_timestamp": NEVER_EXPIRES,
    },
    {
        "document": "User is left-handed.",
        "verbose_summary": "The user noted they are left-handed when discussing note-taking and journaling setups.",
        "static_trait": True,
        "end_timestamp": NEVER_EXPIRES,
    },

    # ── Time-bounded talking points (still valid) ─────────────────────────────
    {
        "document": "User committed to running a sub-35 minute 5K as their next fitness milestone.",
        "verbose_summary": "After completing their 5K goal in January 2025, the user set a stretch goal of finishing a 5K in under 35 minutes. They acknowledged it would be genuinely challenging and are excited about it.",
        "static_trait": False,
        "end_timestamp": APR_2027,
    },
    {
        "document": "User is saving $500 per month toward an emergency fund.",
        "verbose_summary": "The user set a savings goal of $500/month after realizing they had almost no financial buffer. They audited subscriptions to free up cash and are working toward automating the transfer.",
        "static_trait": False,
        "end_timestamp": JUN_2027,
    },
    {
        "document": "User is learning to cook 5 new healthy recipes by end of February.",
        "verbose_summary": "Bored of meal-prepping the same foods, the user set a goal to learn 5 new healthy recipes by end of February 2025. They completed chicken stir fry and lentil soup so far — 2 of 5 done.",
        "static_trait": False,
        "end_timestamp": APR_2027,
    },
    {
        "document": "User meditates for 10 minutes every morning and journals for 5 minutes after.",
        "verbose_summary": "The user started a morning meditation habit on New Year's Day 2025 and paired it with a short journaling practice (gratitude, daily intention, mood check). They had a 12-day streak as of mid-January.",
        "static_trait": False,
        "end_timestamp": JUN_2027,
    },

    # ── Time-bounded talking points (expired) ─────────────────────────────────
    {
        "document": "User wanted to finish reading Atomic Habits before January 1st 2025.",
        "verbose_summary": "In December 2024, the user was halfway through Atomic Habits and set a mini-goal to finish it before New Year's as a symbolic fresh start. They were on pace with 4-5 reading sessions remaining.",
        "static_trait": False,
        "end_timestamp": JAN_2025,
    },
    {
        "document": "User planned to audit unused subscriptions to cut monthly expenses in December 2024.",
        "verbose_summary": "The user suspected $50-100/month was leaking through forgotten subscriptions. They identified this as a first step toward their $500/month savings goal. Action was assigned for the week of December 22, 2024.",
        "static_trait": False,
        "end_timestamp": DEC_2024,
    },
    {
        "document": "User aimed to run a 5K without stopping by end of January 2025.",
        "verbose_summary": "Starting as a complete beginner in December 2024, the user committed to running a non-stop 5K by January 31st 2025. They ran 4.2K straight by January 9th and ultimately completed the full 5K on January 13th — two weeks early.",
        "static_trait": False,
        "end_timestamp": JAN_2025,
    },
]

if __name__ == "__main__":
    for tp in talking_points:
        point_id = store_talking_point(
            user_id=USER_ID,
            document=tp["document"],
            verbose_summary=tp["verbose_summary"],
            static_trait=tp["static_trait"],
            end_timestamp=tp["end_timestamp"],
        )
        trait_label = "STATIC" if tp["static_trait"] else "timed "
        print(f"[{trait_label}] {point_id[:8]}...  {tp['document'][:60]}")

    print(f"\nDone. {len(talking_points)} talking points seeded.")
    print(f"  Static traits:          {sum(1 for t in talking_points if t['static_trait'])}")
    print(f"  Valid timed points:     {sum(1 for t in talking_points if not t['static_trait'] and t['end_timestamp'] > 1741824000)}")
    print(f"  Expired timed points:   {sum(1 for t in talking_points if not t['static_trait'] and t['end_timestamp'] <= 1741824000)}")
