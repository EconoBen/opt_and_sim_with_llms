import random
import string
from datetime import datetime, timedelta
from enum import Enum

import streamlit as st  # type: ignore
from outlines import models
from outlines.generate import json
from pydantic import BaseModel, Field


class TicketType(str, Enum):
    technical = "Technical"
    sales = "Sales"
    billing = "Billing"
    product = "Product"


class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in progress"
    resolved = "resolved"
    closed = "closed"


class TicketPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TicketAssignee(BaseModel):
    id: str
    username: str


class TicketTag(BaseModel):
    id: str
    name: str
    custom_mappings: dict


class Ticket(BaseModel):
    id: str
    parent_id: str
    collection_id: str
    type: TicketType
    subject: str = Field(max_length=100)
    description: str = Field(max_length=1000)
    status: TicketStatus
    priority: TicketPriority
    assignees: list[TicketAssignee]
    updated_at: str
    created_at: str
    created_by: str
    due_date: str
    completed_at: str
    tags: list[TicketTag]
    custom_mappings: dict


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


def generate_random_ticket(employee: dict, ticket_history: list[dict]) -> dict:
    model = models.llamacpp(
        "./models/mistral-7b-instruct-v0.2.Q5_K_M.gguf",
        model_kwargs={"n_gpu_layers": -1},
    )
    generator = json(model, Ticket, whitespace_pattern="")

    prompt = f"""
    Generate a ticket for an employee with the following details:
    - Employee ID: {employee["id"]}
    - Employee Designation: {employee["designation"]}
    - Employee Department: {employee["department"]}
    - Ticket Date: {generate_random_date()}

    Take into account the following ticket history for this employee:
    {ticket_history}

    Generate a new ticket that progresses naturally from the previous tickets, if any.
    """

    ticket = generator(prompt)
    ticket["id"] = generate_ticket_id()
    ticket["parent_id"] = generate_ticket_id()
    ticket["collection_id"] = generate_ticket_id()
    ticket["assignees"] = [{"id": employee["id"], "username": employee["designation"]}]
    ticket["created_by"] = employee["id"]

    return ticket


def generate_tickets_for_org(org_structure: dict) -> list[dict]:
    tickets = []

    def traverse_org(employee: dict, ticket_history: list[dict]):
        if employee["designation"] != "CEO":
            for _ in range(random.randint(1, 5)):
                ticket = generate_random_ticket(employee, ticket_history)
                tickets.append(ticket)
                ticket_history.append(ticket)
        for team_member in employee["team_members"]:
            traverse_org(team_member, ticket_history)

    traverse_org(org_structure, [])
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
