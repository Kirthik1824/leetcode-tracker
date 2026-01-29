import requests
import gspread
import json
import os
from datetime import date
from google.oauth2.service_account import Credentials
from syllabus import SYLLABUS

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"
SHEET_NAME = "Software_Daily_Questions"
QUESTIONS_PER_DAY = 2
START_DATE = date(2026, 1, 29)   # <-- change once


def get_day_number():
    return (date.today() - START_DATE).days


def get_today_plan(day):
    acc = 0
    for item in SYLLABUS:
        acc += item["days"]
        if day < acc:
            return item
    return None


def fetch_questions(topic):
    query = """
    query getTopicTag($slug: String!) {
      topicTag(slug: $slug) {
        questions {
          title
          titleSlug
          difficulty
          acRate
        }
      }
    }
    """

    res = requests.post(
        LEETCODE_GRAPHQL,
        json={"query": query, "variables": {"slug": topic}}
    )

    return res.json()["data"]["topicTag"]["questions"]


def main():
    day = get_day_number()
    plan = get_today_plan(day)

    if not plan:
        print("Syllabus completed 🎉")
        return

    creds = Credentials.from_service_account_info(
        json.loads(os.environ["GOOGLE_CREDS"]),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )

    client = gspread.authorize(creds)
    SHEET_ID = "1LqiCOZJ1GBM0NV8k1J1UB6A--eGJPv4UeqEmS6bV7nE"
    sheet = client.open_by_key(SHEET_ID).sheet1


    existing = set(sheet.col_values(5))

    problems = fetch_questions(plan["topic"])

    added = 0
    for q in problems:
        if q["difficulty"] != plan["difficulty"]:
            continue

        link = f"https://leetcode.com/problems/{q['titleSlug']}"

        if link in existing:
            continue

        row = [
            str(date.today()),
            plan["topic"],
            q["difficulty"],
            q["title"],
            link,
            ""
        ]

        sheet.append_row(row)
        added += 1

        if added == QUESTIONS_PER_DAY:
            break

    print(f"Added {added} questions — {plan['topic']} ({plan['difficulty']})")


if __name__ == "__main__":
    main()
