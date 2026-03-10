from db import store_conversation

USER_ID = "user_abc123"

# Each goal has:
#   title   — short label stored in metadata (for display)
#   context — rich snippet that gets embedded (goal-specific, self-contained)
conversations = [
    {
        "conversation_id": "conv_001",
        "timestamp": 1734000000,  # Dec 12 2024
        "goals": [
            {
                "title": "Run a 5K without stopping by end of January",
                "context": (
                    "Goal: Run a 5K without stopping by end of January. "
                    "Status: Newly set. User is a complete beginner who hasn't exercised in over a year. "
                    "Plan: Start with walk-run intervals 3x/week and build up distance gradually. "
                    "No runs completed yet — this is the initial commitment."
                ),
            },
            {
                "title": "Go to the gym 3 times a week",
                "context": (
                    "Goal: Go to the gym 3 times a week. "
                    "Status: Newly set alongside a 5K running goal. "
                    "User is a beginner with no recent exercise history. "
                    "Gym sessions will be paired with run days to build overall strength. "
                    "No sessions completed yet — initial goal setting."
                ),
            },
        ],
        "llm_summary": "User wants to build a running habit and general fitness routine. They are a beginner and haven't exercised consistently in over a year. Difficulty rating: 6/10. Suggested starting with walk-run intervals 3x/week.",
        "full_transcript": "AI: Hey! What goals are you working toward? User: I really want to get fit. I want to run a 5K without stopping. AI: That's a great goal! When are you hoping to achieve it? User: By end of January. AI: Have you been running recently? User: Not really, I haven't exercised in over a year. AI: Let's start with walk-run intervals. Can you commit to 3 times a week? User: Yeah I think so. AI: Perfect. I'd also suggest pairing that with gym sessions on those same days to build overall strength.",
    },
    {
        "conversation_id": "conv_002",
        "timestamp": 1734259200,  # Dec 15 2024
        "goals": [
            {
                "title": "Read 12 books this year, one per month",
                "context": (
                    "Goal: Read 12 books this year, one per month. "
                    "Status: Newly set. User used to read a lot in college but has fallen off due to a busy lifestyle. "
                    "Recommended starting with shorter books and tracking on Goodreads. "
                    "No books read yet under this goal — initial commitment."
                ),
            },
            {
                "title": "Read for 20 minutes every night before bed",
                "context": (
                    "Goal: Read for 20 minutes every night before bed. "
                    "Status: Newly set as the habit anchor for the 12-books/year goal. "
                    "User identified bedtime as the most consistent available slot. "
                    "No sessions yet — establishing the routine starting tonight."
                ),
            },
        ],
        "llm_summary": "User wants to build a reading habit. They used to read a lot in college but have fallen off. Goal of 12 books/year is achievable. Recommended starting with shorter books and tracking on Goodreads. Difficulty: 4/10.",
        "full_transcript": "AI: What's on your mind today? User: I want to read more. I used to read all the time in college. AI: What changed? User: Just got busy. Work, life, you know. AI: How many books do you think you could realistically read this year? User: Maybe one a month? So 12? AI: That's very doable. Do you have a specific time you could set aside for reading? User: Maybe before bed? Like 20 minutes. AI: Perfect, a consistent nighttime routine is one of the best ways to build the habit. I'd suggest tracking on Goodreads to keep yourself accountable.",
    },
    {
        "conversation_id": "conv_003",
        "timestamp": 1734518400,  # Dec 18 2024
        "goals": [
            {
                "title": "Run a 5K without stopping by end of January",
                "context": (
                    "Goal: Run a 5K without stopping by end of January. "
                    "Status: In progress. User completed 2 run sessions this week — on track. "
                    "Reported it felt hard but manageable. No distance milestone recorded yet. "
                    "Continuing walk-run interval plan."
                ),
            },
            {
                "title": "Meal prep on Sundays to eat healthier during the week",
                "context": (
                    "Goal: Meal prep on Sundays to eat healthier during the week. "
                    "Status: Newly set. Introduced to support the existing fitness goals. "
                    "User admitted to eating poorly, which undermines run and gym performance. "
                    "Plan: Cook once on Sunday for the full week. No sessions completed yet."
                ),
            },
        ],
        "llm_summary": "User checked in on their running goal — they completed two sessions this week. Introduced a nutrition goal around meal prepping to support their fitness. Difficulty for meal prep: 3/10. Running is on track.",
        "full_transcript": "AI: How's the running going? User: Pretty good actually, I did two sessions this week. AI: That's great progress! How did it feel? User: Hard but I didn't die. AI: That's the spirit! Are you fueling yourself well for the runs? User: Honestly no, I eat pretty badly. AI: Want to add a nutrition goal? User: Yeah, maybe meal prepping? AI: Meal prepping on Sundays is a great anchor habit. You cook once and eat well all week. Want to commit to that? User: Yeah let's do it.",
    },
    {
        "conversation_id": "conv_004",
        "timestamp": 1734864000,  # Dec 22 2024
        "goals": [
            {
                "title": "Save $500 per month for an emergency fund",
                "context": (
                    "Goal: Save $500 per month for an emergency fund. "
                    "Status: Newly set. User has almost no savings and is anxious about finances heading into the new year. "
                    "Plan: Automate the $500 transfer so it happens before spending. "
                    "No savings accumulated yet under this goal."
                ),
            },
            {
                "title": "Cancel unused subscriptions to cut monthly expenses",
                "context": (
                    "Goal: Cancel unused subscriptions to cut monthly expenses. "
                    "Status: Newly set as a quick-win first step toward the savings goal. "
                    "User suspects $50-100/month is leaking through forgotten subscriptions. "
                    "Audit not started yet — action item for this week."
                ),
            },
        ],
        "llm_summary": "User is anxious about finances heading into the new year. Wants to build an emergency fund. Currently has almost no savings. Recommended auditing subscriptions first as a quick win, then automating $500/month savings. Difficulty: 5/10.",
        "full_transcript": "AI: What's been on your mind lately? User: Honestly money stuff. I have basically no savings and it stresses me out. AI: That's a really common source of anxiety. Do you have a savings goal in mind? User: I want to save like $500 a month. AI: That's a solid target. Do you know where your money is going right now? User: Not really. I probably have subscriptions I don't use. AI: That's a great place to start — a quick audit can free up $50-100 easily. Then we automate the $500 so it happens before you can spend it.",
    },
    {
        "conversation_id": "conv_005",
        "timestamp": 1735123200,  # Dec 25 2024
        "goals": [
            {
                "title": "Read 12 books this year, one per month",
                "context": (
                    "Goal: Read 12 books this year, one per month. "
                    "Status: On track. User has been reading consistently and is currently mid-way through Atomic Habits. "
                    "Nighttime reading habit is sticking. Ahead of the monthly pace."
                ),
            },
            {
                "title": "Finish reading Atomic Habits by January 1st",
                "context": (
                    "Goal: Finish reading Atomic Habits by January 1st. "
                    "Status: Newly set mini-goal. User is halfway through the book and can realistically finish by New Year's. "
                    "Framed as a symbolic fresh start for the new year. "
                    "Estimated 4-5 more reading sessions needed."
                ),
            },
        ],
        "llm_summary": "User is enjoying the reading habit and wants to finish Atomic Habits before the new year as a symbolic fresh start. On track with the monthly reading goal. Difficulty: 2/10 — they're already halfway through the book.",
        "full_transcript": "AI: Merry Christmas! How are things going? User: Pretty good! I've been reading a lot actually. AI: Which book are you on? User: Atomic Habits. It's really good. AI: Great choice — very fitting given our conversations! How far in are you? User: About halfway. AI: You could easily finish it by January 1st. Would that feel like a meaningful way to start the new year? User: Yeah actually that sounds really cool. AI: Let's make it a mini goal then.",
    },
    {
        "conversation_id": "conv_006",
        "timestamp": 1735468800,  # Dec 29 2024
        "goals": [
            {
                "title": "Go to the gym 3 times a week",
                "context": (
                    "Goal: Go to the gym 3 times a week. "
                    "Status: Consistently hitting target. User went 3 times this week — strong habit forming. "
                    "Started as a beginner 3 weeks ago; now feels routine. No signs of dropping off."
                ),
            },
            {
                "title": "Learn to cook 5 new healthy recipes by end of February",
                "context": (
                    "Goal: Learn to cook 5 new healthy recipes by end of February. "
                    "Status: Newly set. User has been meal prepping but eating the same meals and getting bored. "
                    "Plan: One new recipe every 1-2 weeks. Suggested starting with simple dishes like stir fry or sheet pan meals. "
                    "0 of 5 recipes completed."
                ),
            },
        ],
        "llm_summary": "User has been consistent with the gym. Meal prepping is going okay but they're bored of the same meals. Introduced a cooking goal to expand their recipe repertoire. Difficulty: 4/10. Suggested starting with one new recipe per week.",
        "full_transcript": "AI: How's the gym routine holding up? User: Really well actually, I went three times this week. AI: Crushing it. How about the meal prep? User: It's fine but I keep making the same stuff and getting bored. AI: Variety is important for sustainability. How would you feel about setting a goal to learn new recipes? User: That could be fun. AI: What if you aimed to learn 5 new healthy recipes by end of February? One every couple weeks. User: Yeah I could do that. AI: Start with something simple — maybe a stir fry or sheet pan meal.",
    },
    {
        "conversation_id": "conv_007",
        "timestamp": 1735776000,  # Jan 1 2025
        "goals": [
            {
                "title": "Run a 5K without stopping by end of January",
                "context": (
                    "Goal: Run a 5K without stopping by end of January. "
                    "Status: Strong progress. User ran 3K straight last week without stopping — a clear milestone. "
                    "On track to hit 5K by end of January with current trajectory."
                ),
            },
            {
                "title": "Save $500 per month for an emergency fund",
                "context": (
                    "Goal: Save $500 per month for an emergency fund. "
                    "Status: Slow start but moving. $200 saved so far after cancelling 3 unused subscriptions. "
                    "Automation not yet set up — next action item."
                ),
            },
            {
                "title": "Meditate for 10 minutes every morning",
                "context": (
                    "Goal: Meditate for 10 minutes every morning. "
                    "Status: Newly set as a New Year's goal for mental clarity and focus. "
                    "User has no prior meditation experience. "
                    "Plan: Use a guided app for the first few weeks. Day 1 starting today."
                ),
            },
        ],
        "llm_summary": "New Year's check-in. User is feeling motivated and reviewed all active goals. 5K goal is on track — ran 3K straight last week. Savings goal started with $200 saved so far. Added a meditation goal for mental clarity in the new year. Difficulty for meditation: 3/10.",
        "full_transcript": "AI: Happy New Year! Big goals this year — how are you feeling? User: Really motivated honestly. I feel like things are clicking. AI: Let's do a quick review. The 5K — where are you? User: I ran 3K straight last week without stopping. AI: That's incredible progress. You'll hit 5K easily by end of January. Savings? User: I've put away $200 so far. Slow start but I cancelled three subscriptions. AI: That's real progress. Any new goals for the new year? User: I want to meditate. I heard it's good for focus. AI: Even 10 minutes a morning makes a big difference. Let's add that.",
    },
    {
        "conversation_id": "conv_008",
        "timestamp": 1736121600,  # Jan 5 2025
        "goals": [
            {
                "title": "Meditate for 10 minutes every morning",
                "context": (
                    "Goal: Meditate for 10 minutes every morning. "
                    "Status: Excellent early consistency — 4 days in a row. "
                    "User finds it genuinely enjoyable and reports feeling calmer in the mornings. "
                    "Habit appears to be sticking naturally."
                ),
            },
            {
                "title": "Journal for 5 minutes after meditation to track mood",
                "context": (
                    "Goal: Journal for 5 minutes after meditation to track mood. "
                    "Status: Newly set to extend the existing morning meditation habit. "
                    "Format: Three lines — what you're grateful for, intention for the day, how you feel. "
                    "Designed to stay under 5 minutes. Day 1 starting tomorrow."
                ),
            },
        ],
        "llm_summary": "User started meditating and is enjoying it. Wants to pair it with journaling to build a full morning routine. Suggested a simple 3-line journal format (grateful for, intention for today, how I feel). Difficulty: 2/10.",
        "full_transcript": "AI: How's the meditation going? User: I've done it 4 days in a row. It's actually really nice in the morning. AI: That's great consistency. Does it feel sustainable? User: Yeah. I'm thinking about journaling after too. AI: They pair really well together. What kind of journaling were you thinking? User: Just like, how I'm feeling. AI: A simple format works best — try three lines: what you're grateful for, your intention for the day, and how you feel. Keeps it under 5 minutes. User: That's perfect, I can do that.",
    },
    {
        "conversation_id": "conv_009",
        "timestamp": 1736467200,  # Jan 9 2025
        "goals": [
            {
                "title": "Run a 5K without stopping by end of January",
                "context": (
                    "Goal: Run a 5K without stopping by end of January. "
                    "Status: Very close. User ran 4.2K straight yesterday — personal best. "
                    "One or two more training sessions should get them to 5K. On pace to hit goal early."
                ),
            },
            {
                "title": "Go to the gym 3 times a week",
                "context": (
                    "Goal: Go to the gym 3 times a week. "
                    "Status: Consistent — hit 3x/week every week since the goal was set. "
                    "Now feels like a default part of the weekly routine rather than an effort."
                ),
            },
            {
                "title": "Read 12 books this year, one per month",
                "context": (
                    "Goal: Read 12 books this year, one per month. "
                    "Status: Ahead of pace. Finished book 1 (Atomic Habits) and starting The Alchemist. "
                    "Nighttime reading habit is fully established. On track to exceed the annual target."
                ),
            },
        ],
        "llm_summary": "Mid-January check-in on multiple goals. User ran 4.2K without stopping — very close to 5K target. Gym attendance has been consistent at 3x/week. Finished first book of the year (Atomic Habits). All goals on track. Difficulty adjustments not needed.",
        "full_transcript": "AI: Mid-January check-in! How's everything going? User: Really well. I ran 4.2K without stopping yesterday. AI: You are so close! One more solid week of training and you'll hit 5K. User: I know I'm excited. AI: Gym? User: Three times a week, every week so far. AI: Remarkable consistency. Reading? User: I finished Atomic Habits! Starting The Alchemist next. AI: Great pick. You're ahead of your one-book-a-month pace. Honestly everything is tracking really well.",
    },
    {
        "conversation_id": "conv_010",
        "timestamp": 1736812800,  # Jan 13 2025
        "goals": [
            {
                "title": "Run a 5K without stopping by end of January",
                "context": (
                    "Goal: Run a 5K without stopping by end of January. "
                    "Status: COMPLETED — two weeks early. User ran a full 5K this morning without stopping. "
                    "Described the moment as emotional. Went from zero exercise to 5K in ~6 weeks. "
                    "New stretch goal set: sub-35 minute 5K."
                ),
            },
            {
                "title": "Save $500 per month for an emergency fund",
                "context": (
                    "Goal: Save $500 per month for an emergency fund. "
                    "Status: On track. Hit the $500 target for January. "
                    "Subscription audit freed up recurring cash. Automation likely in place."
                ),
            },
            {
                "title": "Learn to cook 5 new healthy recipes by end of February",
                "context": (
                    "Goal: Learn to cook 5 new healthy recipes by end of February. "
                    "Status: In progress — 2 of 5 done. Cooked chicken stir fry and lentil soup this week. "
                    "Both new recipes successfully made. 3 more needed by end of February."
                ),
            },
            {
                "title": "Meditate for 10 minutes every morning",
                "context": (
                    "Goal: Meditate for 10 minutes every morning. "
                    "Status: Strong streak — 12 consecutive days. "
                    "Now part of an established morning routine paired with journaling. "
                    "No missed days since the goal was set."
                ),
            },
        ],
        "llm_summary": "User ran their first full 5K without stopping — goal achieved two weeks early. Savings on track at $500 for January. Cooked two new recipes so far. Meditation streak is at 12 days. User is in a strong positive momentum phase. Suggested setting a stretch goal for the 5K: aim for a sub-35 minute time.",
        "full_transcript": "AI: Any big updates? User: I did it. I ran a full 5K without stopping this morning. AI: That is huge! How did it feel? User: Honestly amazing. I cried a little at the end. AI: You've earned that. You went from not exercising in a year to running 5K in about 6 weeks. How about everything else? User: Savings are at $500 for January. I cooked chicken stir fry and a lentil soup this week — both new recipes. AI: Two down, three to go on the cooking goal. And meditation? User: 12 days straight. AI: You're in a really strong momentum phase. Want to set a new running goal now that you've hit the 5K? User: Like a time goal? AI: Exactly — what about sub-35 minutes? User: Oh that's actually hard. Let's do it.",
    },
]

if __name__ == "__main__":
    for convo in conversations:
        goal_titles = [g["title"] for g in convo["goals"]]
        goal_contexts = [g["context"] for g in convo["goals"]]

        cid = store_conversation(
            user_id=USER_ID,
            goal_titles=goal_titles,
            goal_contexts=goal_contexts,
            llm_summary=convo["llm_summary"],
            full_transcript=convo["full_transcript"],
            conversation_id=convo["conversation_id"],
            timestamp=convo["timestamp"],
        )
        print(f"Stored {cid} ({len(goal_titles)} goals)")

    print("\nDone. 10 conversations seeded.")
