import random
import string
from datetime import datetime, timedelta

import streamlit as st


def generate_ticket_id() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=5))


def generate_random_date() -> str:
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2023, 12, 31)
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_number_of_days)
    return random_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def generate_random_ticket(employee: dict) -> dict:
    ticket_types = ["Technical", "Sales", "Billing", "Product"]
    ticket_subjects = [
        "Technical Support Request",
        "Sales Inquiry",
        "Billing Question",
        "Product Feedback",
    ]
    ticket_descriptions = [
        "I am facing issues with my internet connection",
        "I have a question about your product pricing",
        "I need assistance with my billing statement",
        "I would like to provide feedback on your product",
    ]
    ticket_statuses = ["open", "in progress", "resolved", "closed"]
    ticket_priorities = ["low", "medium", "high"]
    if employee.get("id") is None:
        employee["id"] = generate_ticket_id()
    ticket = {
        "id": generate_ticket_id(),
        "parent_id": generate_ticket_id(),
        "collection_id": generate_ticket_id(),
        "type": random.choice(ticket_types),
        "subject": random.choice(ticket_subjects),
        "description": random.choice(ticket_descriptions),
        "status": random.choice(ticket_statuses),
        "priority": random.choice(ticket_priorities),
        "assignees": [
            {
                "id": employee["id"],
                "username": employee["designation"],
            }
        ],
        "updated_at": generate_random_date(),
        "created_at": generate_random_date(),
        "created_by": employee["id"],
        "due_date": generate_random_date(),
        "completed_at": generate_random_date(),
        "tags": [
            {
                "id": generate_ticket_id(),
                "name": random.choice(["User Experience", "Bug", "Enhancement"]),
                "custom_mappings": {},
            }
        ],
        "custom_mappings": {},
    }
    return ticket


def generate_tickets_for_org(org_structure: dict) -> list[dict]:
    tickets = []

    def traverse_org(employee: dict) -> None:
        if employee["designation"] != "CEO":
            for _ in range(random.randint(1, 5)):
                ticket = generate_random_ticket(employee)
                tickets.append(ticket)
        for team_member in employee["team_members"]:
            traverse_org(team_member)

    traverse_org(org_structure)
    return tickets


def generate_api_response(tickets: list[dict]) -> dict:
    return {
        "status_code": 200,
        "status": "OK",
        "service": "jira",
        "resource": "Tickets",
        "operation": "all",
        "data": tickets,
        "meta": {
            "items_on_page": len(tickets),
            "cursors": {
                "previous": "em9oby1jcm06OnBhZ2U6OjE=",
                "current": "em9oby1jcm06OnBhZ2U6OjI=",
                "next": "em9oby1jcm06OnBhZ2U6OjM=",
            },
        },
        "links": {
            "previous": "https://unify.apideck.com/crm/companies?cursor=em9oby1jcm06OnBhZ2U6OjE%3D",
            "current": "https://unify.apideck.com/crm/companies",
            "next": "https://unify.apideck.com/crm/companies?cursor=em9oby1jcm06OnBhZ2U6OjM=",
        },
    }


def generate_tickets_page(org_structure: dict) -> None:
    if len(org_structure) == 0:
        pass
    else:
        tickets = generate_tickets_for_org(org_structure)
        api_response = generate_api_response(tickets)
        with st.container():
            st.json(api_response)
