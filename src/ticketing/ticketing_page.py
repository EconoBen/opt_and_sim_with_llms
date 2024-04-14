import asyncio
import random
import string
from datetime import datetime, timedelta
from enum import Enum
from os import environ

import instructor
import streamlit as st  # type: ignore
from openai import AsyncOpenAI
from polars import DataFrame
from pydantic import BaseModel, Field

client = instructor.from_openai(AsyncOpenAI(api_key=environ["OPENAI_API_KEY"]))


# Utility functions
def generate_ticket_id() -> str:
    """Generate a random ticket ID consisting of uppercase letters and digits."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=5))


def generate_random_date() -> str:
    """Generate a random date within a specified range in ISO8601 format."""
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2023, 12, 31)
    random_date = start_date + timedelta(
        days=random.randint(0, (end_date - start_date).days)
    )
    return random_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")


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
    custom_mappings: dict = Field(default_factory=dict)


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
    custom_mappings: dict = Field(default_factory=dict)


async def create_ticket_with_prompt(employee: dict) -> Ticket:
    """Generate ticket details using an AI model with a descriptive prompt."""
    prompt = f"""
                Create a detailed Jira ticket for an employee in the role of {employee['designation']}.
                Include a description of the problem, suggested initial steps for troubleshooting,
                expected impacts on the project timeline, and any urgent resources or support needed.
                Specify the urgency and assign a priority based on the severity of the issue.
              """

    return await client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_model=Ticket,
        messages=[{"role": "user", "content": prompt}],
    )


# Async task management and Streamlit UI integration
async def generate_tickets_for_organization(org_structure: dict) -> DataFrame:
    tickets_data = []

    async def traverse_org(employee: dict) -> None:
        if employee["designation"] != "CEO":
            ticket: Ticket = await create_ticket_with_prompt(employee)
            tickets_data.append(
                {
                    "user_id": employee["id"],
                    "ticket_id": ticket.id,
                    "assignee_id": ticket.assignees[0].id,
                    "assignee_username": ticket.assignees[0].username,
                    "ticket_type": ticket.type,
                    "ticket_status": ticket.status,
                    "ticket_priority": ticket.priority,
                    "description": ticket.description,
                    "created_at": ticket.created_at,
                    "due_date": ticket.due_date,
                    "completed_at": ticket.completed_at,
                }
            )
        for team_member in employee.get("team_members", []):
            await traverse_org(team_member)

    await traverse_org(org_structure)
    return DataFrame(tickets_data)


def generate_api_response(tickets: DataFrame) -> dict:
    data = tickets.to_dict()
    return {
        "status_code": 200,
        "status": "OK",
        "service": "jira",
        "resource": "Tickets",
        "operation": "all",
        "data": data,
        "meta": {
            "items_on_page": len(data),
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
        tickets = asyncio.run(generate_tickets_for_organization(org_structure))
        st.dataframe(tickets)
        api_response = generate_api_response(tickets)
        with st.container():
            st.json(api_response)
