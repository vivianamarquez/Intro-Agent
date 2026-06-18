"""Small teaching dataset for the World Cup Matchday Agent lessons.

This is intentionally tiny and local. It lets the examples feel real without
depending on live sports APIs during class.
"""

from __future__ import annotations


MATCHES = [
    {
        "id": "MEX-RSA",
        "group": "A",
        "home": "Mexico",
        "away": "South Africa",
        "date": "2026-06-11",
        "time": "7:00 PM local",
        "city": "Mexico City",
        "venue": "Mexico City Stadium",
        "status": "Final: Mexico 2, South Africa 0",
    },
    {
        "id": "USA-PAR",
        "group": "D",
        "home": "United States",
        "away": "Paraguay",
        "date": "2026-06-12",
        "time": "6:00 PM local",
        "city": "Los Angeles",
        "venue": "Los Angeles Stadium",
        "status": "Final: United States 4, Paraguay 1",
    },
    {
        "id": "ENG-CRO",
        "group": "L",
        "home": "England",
        "away": "Croatia",
        "date": "2026-06-18",
        "time": "4:00 PM local",
        "city": "Dallas",
        "venue": "Dallas Stadium",
        "status": "Final: England 4, Croatia 2",
    },
    {
        "id": "GHA-PAN",
        "group": "L",
        "home": "Ghana",
        "away": "Panama",
        "date": "2026-06-18",
        "time": "7:00 PM local",
        "city": "Toronto",
        "venue": "Toronto Stadium",
        "status": "Upcoming",
    },
    {
        "id": "UZB-COL",
        "group": "K",
        "home": "Uzbekistan",
        "away": "Colombia",
        "date": "2026-06-18",
        "time": "8:00 PM local",
        "city": "Mexico City",
        "venue": "Mexico City Stadium",
        "status": "Upcoming",
    },
    {
        "id": "BRA-HAI",
        "group": "C",
        "home": "Brazil",
        "away": "Haiti",
        "date": "2026-06-19",
        "time": "8:30 PM local",
        "city": "Philadelphia",
        "venue": "Philadelphia Stadium",
        "status": "Upcoming",
    },
]


TEAM_NOTES = {
    "brazil": "Brazil are always a major draw and tend to bring a huge neutral audience.",
    "colombia": "Colombia are returning with a fast, direct attacking style.",
    "croatia": "Croatia are experienced and dangerous in tight knockout-style matches.",
    "england": "England have a deep squad and lots of attention after a high-scoring opener.",
    "ghana": "Ghana are physical, direct, and usually bring a lively supporter section.",
    "haiti": "Haiti are underdogs, which can make their group matches especially emotional.",
    "mexico": "Mexico are co-hosts, so their matches have a true home-crowd feel.",
    "panama": "Panama are organized and can make games uncomfortable for favorites.",
    "south africa": "South Africa have pace and are looking to recover after the opener.",
    "united states": "The United States are co-hosts and opened with a statement win.",
    "uzbekistan": "Uzbekistan are tournament newcomers, so every match is historic for them.",
}


VENUE_NOTES = {
    "dallas": "Dallas Stadium is built for big crowds. Arrive early and expect long security lines.",
    "los angeles": "Los Angeles Stadium usually means heavy traffic. Leave extra travel time.",
    "mexico city": "Mexico City Stadium has altitude and a huge matchday atmosphere.",
    "philadelphia": "Philadelphia Stadium has strong transit options but busy post-match exits.",
    "toronto": "Toronto Stadium is central enough for transit, but downtown crowds build quickly.",
}


FAN_POLICIES = {
    "bags": "Use a small clear bag when possible. Stadium bag rules can be strict.",
    "tickets": "Use official ticketing channels and do not share screenshots of QR codes.",
    "travel": "Plan to arrive at least two hours early for a World Cup match.",
    "weather": "Check the local forecast before leaving; host cities can vary a lot.",
}


def normalize(text: str) -> str:
    return text.strip().lower()


def match_to_text(match: dict[str, str]) -> str:
    return (
        f"{match['id']}: {match['home']} vs {match['away']} "
        f"({match['group']}) on {match['date']} at {match['time']} "
        f"in {match['city']} - {match['status']}"
    )


def search_matches(query: str) -> str:
    """Search the small local match list."""
    query_text = normalize(query)
    words = [word for word in query_text.replace("-", " ").split() if word]

    results = []
    for match in MATCHES:
        haystack = normalize(
            " ".join(
                [
                    match["id"],
                    match["group"],
                    match["home"],
                    match["away"],
                    match["date"],
                    match["city"],
                    match["venue"],
                    match["status"],
                ]
            )
        )
        if not words or any(word in haystack for word in words):
            results.append(match_to_text(match))

    if not results:
        return "No matches found in the classroom dataset."

    return "\n".join(results[:4])


def lookup_team_note(team: str) -> str:
    """Return a short note about one team."""
    clean_team = normalize(team)
    return TEAM_NOTES.get(clean_team, f"No team note found for {team!r}.")


def lookup_venue_note(city: str) -> str:
    """Return a short matchday note for one host city."""
    clean_city = normalize(city)
    return VENUE_NOTES.get(clean_city, f"No venue note found for {city!r}.")


def lookup_fan_policy(topic: str) -> str:
    """Return a short fan policy note."""
    clean_topic = normalize(topic)
    return FAN_POLICIES.get(clean_topic, f"No fan policy found for {topic!r}.")


def sample_question() -> str:
    return "I am in Dallas. What should I know about England vs Croatia?"
