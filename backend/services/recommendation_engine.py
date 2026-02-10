"""
Recommendation Engine for IdolCode
Analyzes user and idol Codeforces histories to generate
topic-aligned problem recommendations (1 easy, 1 medium, 1 hard).
"""

import httpx
import logging
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime, timezone
from collections import Counter

logger = logging.getLogger(__name__)

# ── Codeforces API helpers ──────────────────────────────────────────────

async def fetch_user_submissions(handle: str) -> List[Dict]:
    """Fetch all submissions for a user from Codeforces API."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(
            f"https://codeforces.com/api/user.status?handle={handle}"
        )
        if resp.status_code != 200:
            raise ValueError(f"Could not fetch submissions for {handle}")
        data = resp.json()
        if data.get("status") != "OK":
            raise ValueError(f"CF API error for {handle}")
        return data.get("result", [])


async def fetch_user_rating_history(handle: str) -> List[Dict]:
    """Fetch rating change history for a user."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"https://codeforces.com/api/user.rating?handle={handle}"
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        if data.get("status") != "OK":
            return []
        return data.get("result", [])


async def fetch_user_info(handle: str) -> Dict:
    """Fetch basic user info (rating, rank, etc.)."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"https://codeforces.com/api/user.info?handles={handle}"
        )
        if resp.status_code != 200:
            return {}
        data = resp.json()
        if data.get("status") == "OK" and data.get("result"):
            return data["result"][0]
        return {}


# ── Profile analysis ────────────────────────────────────────────────────

def _build_rating_at_time_fn(rating_history: List[Dict]):
    """Return a closure that gives rating at a given timestamp."""
    def get_rating(ts: int) -> Optional[int]:
        rating = None
        for contest in rating_history:
            if contest.get("ratingUpdateTimeSeconds", 0) <= ts:
                rating = contest.get("newRating")
            else:
                break
        return rating
    return get_rating


def analyze_user_profile(submissions: List[Dict]) -> Dict:
    """
    Analyze a Codeforces user's submission history.
    Returns:
        {
            "solved_by_tag": { tag: count },
            "failed_by_tag": { tag: count },
            "solved_problem_ids": set of "contestId+index",
            "total_solved": int,
            "total_attempted": int,
            "strengths": [top tags with high solve ratio],
            "weaknesses": [tags with low solve ratio or high fail count],
            "unexplored": [] (filled later by comparing with idol)
        }
    """
    solved_tags = Counter()
    failed_tags = Counter()
    attempted_tags = Counter()
    solved_ids: Set[str] = set()
    attempted_ids: Set[str] = set()

    for sub in submissions:
        problem = sub.get("problem", {})
        cid = problem.get("contestId")
        idx = problem.get("index", "")
        if not cid or not idx:
            continue
        pid = f"{cid}{idx}"
        tags = problem.get("tags", [])

        if sub.get("verdict") == "OK" and pid not in solved_ids:
            solved_ids.add(pid)
            for t in tags:
                solved_tags[t] += 1
        elif sub.get("verdict") not in (None, "OK") and pid not in solved_ids:
            if pid not in attempted_ids:
                attempted_ids.add(pid)
                for t in tags:
                    failed_tags[t] += 1

        for t in tags:
            attempted_tags[t] += 1

    # Compute per-tag solve ratios
    all_tags = set(solved_tags.keys()) | set(failed_tags.keys())
    tag_stats = {}
    for tag in all_tags:
        s = solved_tags.get(tag, 0)
        f = failed_tags.get(tag, 0)
        total = s + f
        ratio = s / total if total > 0 else 0
        tag_stats[tag] = {"solved": s, "failed": f, "ratio": ratio}

    # Strengths: tags with ratio > 0.7 and at least 3 solved
    strengths = sorted(
        [t for t, v in tag_stats.items() if v["ratio"] >= 0.7 and v["solved"] >= 3],
        key=lambda t: -tag_stats[t]["solved"]
    )[:10]

    # Weaknesses: tags with ratio < 0.5 OR tags with >= 2 failures
    weaknesses = sorted(
        [t for t, v in tag_stats.items()
         if v["ratio"] < 0.5 or v["failed"] >= 2],
        key=lambda t: tag_stats[t]["ratio"]
    )[:10]

    return {
        "solved_by_tag": dict(solved_tags),
        "failed_by_tag": dict(failed_tags),
        "solved_problem_ids": solved_ids,
        "total_solved": len(solved_ids),
        "total_attempted": len(attempted_ids | solved_ids),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "unexplored": [],
        "tag_stats": tag_stats,
    }


def analyze_idol_profile(
    submissions: List[Dict],
    rating_history: List[Dict],
    target_rank: Optional[str] = None,
) -> Dict:
    """
    Analyze the idol's history.
    Groups solved problems by topic and by the idol's rating range at
    the time of solving.
    Returns:
        {
            "solved_problems": [ { problemId, contestId, index, name, rating, tags, solvedAt, idolRatingAtSolve } ],
            "topics_mastered": { tag: count },
            "problems_by_difficulty": { "easy": [...], "medium": [...], "hard": [...] },
        }
    """
    get_rating = _build_rating_at_time_fn(rating_history)

    seen: Set[str] = set()
    problems = []
    topics_mastered = Counter()

    # Sort by time – oldest first
    sorted_subs = sorted(submissions, key=lambda x: x.get("creationTimeSeconds", 0))

    for sub in sorted_subs:
        if sub.get("verdict") != "OK":
            continue
        problem = sub.get("problem", {})
        cid = problem.get("contestId")
        idx = problem.get("index", "")
        if not cid or not idx:
            continue
        pid = f"{cid}{idx}"
        if pid in seen:
            continue
        seen.add(pid)

        ts = sub.get("creationTimeSeconds", 0)
        idol_rating = get_rating(ts)
        tags = problem.get("tags", [])
        p_rating = problem.get("rating")

        for t in tags:
            topics_mastered[t] += 1

        problems.append({
            "problemId": pid,
            "contestId": cid,
            "index": idx,
            "name": problem.get("name", ""),
            "rating": p_rating,
            "tags": tags,
            "solvedAt": ts,
            "idolRatingAtSolve": idol_rating,
        })

    # Bucket by difficulty using problem rating
    easy = [p for p in problems if p["rating"] and p["rating"] <= 1300]
    medium = [p for p in problems if p["rating"] and 1300 < p["rating"] <= 1900]
    hard = [p for p in problems if p["rating"] and p["rating"] > 1900]

    return {
        "solved_problems": problems,
        "topics_mastered": dict(topics_mastered),
        "problems_by_difficulty": {
            "easy": easy,
            "medium": medium,
            "hard": hard,
        },
    }


# ── Core recommendation logic ──────────────────────────────────────────

def _score_problem(
    problem: Dict,
    user_weaknesses: List[str],
    user_unexplored: List[str],
    user_solved_ids: Set[str],
) -> float:
    """
    Score a problem by how well it targets the user's weak / unexplored
    topics. Higher = better match. Returns 0 if already solved.
    """
    pid = problem["problemId"]
    if pid in user_solved_ids:
        return -1  # already solved, skip

    tags = set(problem.get("tags", []))
    score = 0.0

    # Weakness alignment (highest priority)
    weakness_overlap = tags & set(user_weaknesses)
    score += len(weakness_overlap) * 3.0

    # Unexplored topic bonus
    unexplored_overlap = tags & set(user_unexplored)
    score += len(unexplored_overlap) * 2.0

    # Slight bonus for having tags at all (diverse problems)
    if tags:
        score += 0.5

    return score


def select_recommendations(
    idol_profile: Dict,
    user_profile: Dict,
) -> List[Dict]:
    """
    Select 3 problems: 1 easy, 1 medium, 1 hard.
    Prioritizes topic weakness alignment and unexplored topics.
    Ensures no already-solved problems are returned.
    Returns list of problem dicts with an added 'difficulty' key.
    """
    user_solved = user_profile["solved_problem_ids"]
    weaknesses = user_profile["weaknesses"]
    unexplored = user_profile.get("unexplored", [])

    # Find unexplored topics: topics idol mastered but user never solved
    idol_topics = set(idol_profile["topics_mastered"].keys())
    user_topics = set(user_profile["solved_by_tag"].keys())
    auto_unexplored = list(idol_topics - user_topics)
    all_unexplored = list(set(unexplored + auto_unexplored))

    # Update the user profile with discovered unexplored topics
    user_profile["unexplored"] = all_unexplored[:15]

    results = []

    for difficulty, label in [("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")]:
        pool = idol_profile["problems_by_difficulty"].get(difficulty, [])

        # Score and sort
        scored = []
        for p in pool:
            s = _score_problem(p, weaknesses, all_unexplored, user_solved)
            if s > 0:
                scored.append((s, p))

        scored.sort(key=lambda x: -x[0])

        if scored:
            chosen = scored[0][1]
            chosen_copy = {**chosen, "difficulty": label}
            results.append(chosen_copy)

    return results


# ── Gemini description generation ──────────────────────────────────────

async def generate_description(
    gemini_client,
    recommendations: List[Dict],
    user_weaknesses: List[str],
    user_unexplored: List[str],
) -> str:
    """
    Use Gemini to produce a short 3-liner summary about the recommended
    problems and why they were chosen.
    Falls back to a simple template if Gemini is unavailable.
    """
    if not gemini_client or not recommendations:
        return _fallback_description(recommendations, user_weaknesses, user_unexplored)

    try:
        problem_lines = []
        for r in recommendations:
            problem_lines.append(
                f"- {r['name']} ({r['difficulty']}, rating {r.get('rating', '?')}, "
                f"tags: {', '.join(r.get('tags', [])[:4])})"
            )
        problems_text = "\n".join(problem_lines)
        weakness_text = ", ".join(user_weaknesses[:5]) if user_weaknesses else "none identified"
        unexplored_text = ", ".join(user_unexplored[:5]) if user_unexplored else "none"

        prompt = f"""You are a competitive programming coach. Write EXACTLY 3 short sentences 
(total ~50 words) explaining why these 3 problems were selected for this student.

Student's weak areas: {weakness_text}
Unexplored topics: {unexplored_text}

Recommended problems:
{problems_text}

Be specific about which topics each problem addresses. Do NOT use bullet points—write flowing sentences. Do NOT exceed 3 sentences."""

        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = response.text.strip()
        # Limit to 3 sentences max
        sentences = text.replace("\n", " ").split(". ")
        limited = ". ".join(sentences[:3])
        if not limited.endswith("."):
            limited += "."
        return limited

    except Exception as e:
        logger.error(f"Gemini description error: {e}")
        return _fallback_description(recommendations, user_weaknesses, user_unexplored)


def _fallback_description(
    recommendations: List[Dict],
    weaknesses: List[str],
    unexplored: List[str],
) -> str:
    """Simple template description when Gemini is unavailable."""
    parts = []
    weak_str = ", ".join(weaknesses[:3]) if weaknesses else "various topics"
    parts.append(f"These problems target your weak areas in {weak_str}.")
    if unexplored:
        parts.append(f"You'll also explore new topics like {', '.join(unexplored[:2])}.")
    difficulty_names = [r.get("difficulty", "?") for r in recommendations]
    parts.append(
        f"The set includes {', '.join(difficulty_names)} difficulties for balanced practice."
    )
    return " ".join(parts[:3])


# ── Main orchestrator ───────────────────────────────────────────────────

async def build_recommendations(
    user_handle: str,
    idol_handle: str,
    gemini_client=None,
    db=None,
) -> Dict:
    """
    Full pipeline:
    1. Fetch user + idol submissions from CF API
    2. Analyze profiles (strengths, weaknesses, unexplored)
    3. Select 3 problems (easy, medium, hard) based on topic alignment
    4. Generate a 3-liner description
    5. Store everything in MongoDB
    6. Return the result
    """
    # ── Step 1: Fetch data from Codeforces ──
    user_subs = await fetch_user_submissions(user_handle)
    idol_subs = await fetch_user_submissions(idol_handle)
    idol_rating_history = await fetch_user_rating_history(idol_handle)
    user_info = await fetch_user_info(user_handle)

    # ── Step 2: Analyze profiles ──
    user_profile = analyze_user_profile(user_subs)
    idol_profile = analyze_idol_profile(idol_subs, idol_rating_history)

    # ── Step 3: Select recommendations ──
    recommendations = select_recommendations(idol_profile, user_profile)

    # ── Step 4: Generate description ──
    description = await generate_description(
        gemini_client,
        recommendations,
        user_profile["weaknesses"],
        user_profile.get("unexplored", []),
    )

    # ── Step 5: Build result and store in MongoDB ──
    now = datetime.now(timezone.utc)

    # Prepare storable user profile (convert set to list)
    storable_user_profile = {
        "handle": user_handle,
        "rating": user_info.get("rating"),
        "rank": user_info.get("rank"),
        "strengths": user_profile["strengths"],
        "weaknesses": user_profile["weaknesses"],
        "unexplored": user_profile.get("unexplored", []),
        "total_solved": user_profile["total_solved"],
        "solved_by_tag": user_profile["solved_by_tag"],
        "failed_by_tag": user_profile["failed_by_tag"],
        "analyzedAt": now.isoformat(),
    }

    storable_idol_profile = {
        "handle": idol_handle,
        "topics_mastered": idol_profile["topics_mastered"],
        "total_problems": len(idol_profile["solved_problems"]),
        "problem_counts": {
            "easy": len(idol_profile["problems_by_difficulty"]["easy"]),
            "medium": len(idol_profile["problems_by_difficulty"]["medium"]),
            "hard": len(idol_profile["problems_by_difficulty"]["hard"]),
        },
        "analyzedAt": now.isoformat(),
    }

    # Build recommendation docs
    rec_docs = []
    for r in recommendations:
        doc = {
            "problemId": r["problemId"],
            "contestId": r["contestId"],
            "index": r["index"],
            "name": r["name"],
            "rating": r.get("rating"),
            "tags": r.get("tags", []),
            "difficulty": r["difficulty"],
            "url": f"https://codeforces.com/problemset/problem/{r['contestId']}/{r['index']}",
        }
        rec_docs.append(doc)

    result = {
        "userHandle": user_handle,
        "idolHandle": idol_handle,
        "recommendations": rec_docs,
        "description": description,
        "userProfile": storable_user_profile,
        "idolProfile": storable_idol_profile,
        "generatedAt": now.isoformat(),
    }

    # ── Step 6: Persist to MongoDB ──
    if db is not None:
        try:
            # Upsert user profile
            await db.user_profiles.update_one(
                {"handle": user_handle},
                {"$set": storable_user_profile},
                upsert=True,
            )
            # Upsert idol profile
            await db.idol_profiles.update_one(
                {"handle": idol_handle},
                {"$set": storable_idol_profile},
                upsert=True,
            )
            # Upsert recommendations
            await db.recommended_problems.update_one(
                {"userHandle": user_handle, "idolHandle": idol_handle},
                {"$set": result},
                upsert=True,
            )
        except Exception as e:
            logger.error(f"MongoDB write error: {e}")

    return result
