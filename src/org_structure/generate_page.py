import random
import string

import streamlit as st
import streamlit.components.v1 as components
from graphviz import Digraph  # type: ignore


def generate_employee_id() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def generate_work_email(name: str) -> str:
    domains = ["example.com", "company.com", "org.com"]
    return f"{name.lower().replace(' ', '.')}@{random.choice(domains)}"


def generate_employee(
    designation: str, department: str, max_depth: int, current_depth: int = 0
) -> dict:
    employee = {
        "id": generate_employee_id(),
        "designation": designation,
        "department": department,
        "manager": None,
        "team_members": [],
    }  # type: ignore

    if current_depth < max_depth:
        employee["manager"] = {
            "id": generate_employee_id(),
            "workEmail": generate_work_email(designation),  # type: ignore
        }  # type: ignore

    return employee


def generate_org_structure(num_managers: int, max_employees: int) -> dict:
    ceo = generate_employee("CEO", "Executive", 0)
    executives = [
        generate_employee("CTO", "Technology", 1),
        generate_employee("COO", "Operations", 1),
        generate_employee("CFO", "Finance", 1),
    ]
    ceo["team_members"] = executives

    for executive in executives:
        for _ in range(num_managers):
            manager = generate_employee(
                "Manager", executive["department"], max_employees
            )
            executive["team_members"].append(manager)
            for _ in range(random.randint(1, max_employees)):
                team_member = generate_employee("Employee", executive["department"], 0)
                manager["team_members"].append(team_member)

    return ceo


def build_org_chart(
    org_structure: dict, chart: Digraph, parent: str | None = None
) -> None:
    employee_id = generate_employee_id()
    chart.node(
        employee_id, f"{org_structure['designation']}\n{org_structure['department']}"
    )
    if parent:
        chart.edge(parent, employee_id)
    for team_member in org_structure["team_members"]:
        build_org_chart(team_member, chart, employee_id)


def generate_structure_page() -> dict:
    st.title("Employee Org Structure Generator")
    manager_state = st.slider(
        "Number of Managers per Executive", min_value=1, max_value=10
    )
    emply_depth = st.slider(
        "Maximum Number of Employees per Manager", min_value=1, max_value=10
    )
    org_structure: dict = {}
    if manager_state is not None and emply_depth is not None:
        if st.button("Generate"):
            org_structure = generate_org_structure(manager_state, emply_depth)
            with st.container():
                st.json(org_structure)
            chart = Digraph(format="svg")
            build_org_chart(org_structure, chart)
            chart_svg = chart.pipe(format="svg").decode("utf-8")
            components.html(
                f'<div style="overflow: auto; width: 1000px; height: 500px;">{chart_svg}</div>',
                height=520,
                width=1020,
            )
        return org_structure
    return org_structure
