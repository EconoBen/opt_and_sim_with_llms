from random import choice

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns  # type: ignore
import streamlit as st
from polars import DataFrame, arange, col, count
from pulp import LpMinimize, LpProblem, LpVariable, lpSum  # type: ignore

from src.ticketing.ticketing_page import generate_tickets_page


def optimize_team_composition(tickets: DataFrame, constraints: dict) -> DataFrame:
    tickets = tickets.with_columns(
        col("ticket_priority")
        .map_dict({"low": 1, "medium": 2, "high": 3, None: 1})
        .alias("ticket_priority_int")
    )

    prob = LpProblem("Team Composition Problem", LpMinimize)
    indices = list(range(len(tickets)))

    # Define decision variables
    x = LpVariable.dicts("x", [(i, j) for i in indices for j in indices], cat="Binary")

    # Define objective function
    prob += lpSum(
        [x[i, j] * tickets["ticket_priority_int"][i] for i in indices for j in indices]
    )

    # Define constraints
    for i in indices:
        prob += (
            lpSum([x[i, j] for j in indices]) == 1
        )  # Each ticket must be assigned to exactly one employee
        prob += (
            lpSum([x[j, i] for j in indices]) <= constraints["max_tickets_per_employee"]
        )  # Limit tickets per employee

    departments = (
        tickets.select(col("department"))
        .unique()
        .to_dict(as_series=False)["department"]
    )
    for dept in departments:
        dept_indices = (
            tickets.filter(col("department") == dept)
            .select(arange(0, count()))
            .to_numpy()
            .flatten()
        )
        prob += (
            lpSum([x[i, j] for i in dept_indices for j in indices])
            >= constraints[f"min_{dept}_tickets"]
        )

    prob.solve()

    # Extracting and preparing decision variables
    ticket_index = [i for i in indices for j in indices]
    assigned_to = [j for i in indices for j in indices]
    decision = [
        1 if x[(i, j)].varValue == 1 else 0 for i in indices for j in indices
    ]  # directly convert to binary here

    # Create DataFrame
    assigned_tickets = DataFrame(
        {"ticket_index": ticket_index, "assigned_to": assigned_to, "decision": decision}
    )

    # Join and filter
    return tickets.join(
        assigned_tickets.filter(col("decision") == 1),
        left_on="index",
        right_on="ticket_index",
        how="left",
    )


def generate_fake_data(tickets: DataFrame) -> DataFrame:
    # Simulate less efficient 'assigned_to' values
    inefficient_assigned = tickets.with_columns(
        col("index").apply(lambda _: choice(range(len(tickets)))).alias("assigned_to")
    )
    # Retain ticket_priority_int in the fake data
    fake_tickets = tickets.join(
        inefficient_assigned.select(["index", "assigned_to"]), on="index", how="left"
    )
    return fake_tickets


def calculate_metrics(tickets: DataFrame) -> dict:
    metrics = {
        "avg_priority_per_employee": tickets.groupby("assigned_to")
        .agg([col("ticket_priority_int").mean().alias("avg_priority")])
        .sort("assigned_to"),
        "total_tickets_per_department": tickets.groupby("department")
        .agg([count().alias("total_tickets")])
        .sort("department"),
        "employees_per_department": tickets.groupby("department")
        .agg([col("assigned_to").n_unique().alias("unique_employees")])
        .sort("department"),
    }
    return metrics


def plot_bar_charts(metrics_before: dict, metrics_after: dict) -> None:
    # Convert to pandas for easier plotting
    df_before = {
        "avg_priority_per_employee": metrics_before[
            "avg_priority_per_employee"
        ].to_pandas(),
        "total_tickets_per_department": metrics_before[
            "total_tickets_per_department"
        ].to_pandas(),
        "employees_per_department": metrics_before[
            "employees_per_department"
        ].to_pandas(),
    }
    df_after = {
        "avg_priority_per_employee": metrics_after[
            "avg_priority_per_employee"
        ].to_pandas(),
        "total_tickets_per_department": metrics_after[
            "total_tickets_per_department"
        ].to_pandas(),
        "employees_per_department": metrics_after[
            "employees_per_department"
        ].to_pandas(),
    }

    fig, axes = plt.subplots(3, 1, figsize=(10, 18))

    # Settings for side-by-side bars
    bar_width = 0.35
    r1 = np.arange(len(df_before["avg_priority_per_employee"]))
    r2 = [x + bar_width for x in r1]

    # Average Priority Per Employee
    axes[0].bar(
        r1,
        df_before["avg_priority_per_employee"]["avg_priority"],
        color="blue",
        width=bar_width,
        edgecolor="grey",
        label="Before Optimization",
    )
    axes[0].bar(
        r2,
        df_after["avg_priority_per_employee"]["avg_priority"],
        color="red",
        width=bar_width,
        edgecolor="grey",
        label="After Optimization",
    )
    axes[0].set_xlabel("Employee ID", fontweight="bold")
    axes[0].set_ylabel("Average Priority")
    axes[0].set_title("Average Ticket Priority Per Employee")
    axes[0].set_xticks([r + bar_width / 2 for r in range(len(r1))])
    axes[0].set_xticklabels(df_before["avg_priority_per_employee"]["assigned_to"])
    axes[0].legend()

    # Total Tickets Per Department
    axes[1].bar(
        r1,
        df_before["total_tickets_per_department"]["total_tickets"],
        color="blue",
        width=bar_width,
        edgecolor="grey",
        label="Before Optimization",
    )
    axes[1].bar(
        r2,
        df_after["total_tickets_per_department"]["total_tickets"],
        color="red",
        width=bar_width,
        edgecolor="grey",
        label="After Optimization",
    )
    axes[1].set_xlabel("Department", fontweight="bold")
    axes[1].set_ylabel("Total Tickets")
    axes[1].set_title("Total Tickets Per Department")
    axes[1].set_xticks([r + bar_width / 2 for r in range(len(r1))])
    axes[1].set_xticklabels(df_before["total_tickets_per_department"]["department"])
    axes[1].legend()

    # Employees Per Department
    axes[2].bar(
        r1,
        df_before["employees_per_department"]["unique_employees"],
        color="blue",
        width=bar_width,
        edgecolor="grey",
        label="Before Optimization",
    )
    axes[2].bar(
        r2,
        df_after["employees_per_department"]["unique_employees"],
        color="red",
        width=bar_width,
        edgecolor="grey",
        label="After Optimization",
    )
    axes[2].set_xlabel("Department", fontweight="bold")
    axes[2].set_ylabel("Number of Employees")
    axes[2].set_title("Unique Employees Per Department")
    axes[2].set_xticks([r + bar_width / 2 for r in range(len(r1))])
    axes[2].set_xticklabels(df_before["employees_per_department"]["department"])
    axes[2].legend()

    st.pyplot(fig)


def plot_metrics(tickets: DataFrame, title: str) -> None:
    # Ensure DataFrame conversion for plotting
    df = tickets.to_pandas()

    # Create a scatter plot of ticket priority by assigned employee
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(
        data=df,
        x="assigned_to",
        y="ticket_priority_int",
        alpha=0.6,
        ax=ax,
    )
    ax.set_title(f"Ticket Priority Distribution by Employee - {title}")
    ax.set_xlabel("Employee ID")
    ax.set_ylabel("Ticket Priority")
    ax.grid(True)
    st.pyplot(fig)

    # Create a box plot of tickets per department
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=df, x="department", y="ticket_priority_int", ax=ax)
    ax.set_title(f"Ticket Priority Boxplot per Department - {title}")
    ax.set_xlabel("Department")
    ax.set_ylabel("Ticket Priority")
    plt.xticks(rotation=45)
    ax.grid(True)
    st.pyplot(fig)


def generate_plots(tickets_before: DataFrame, tickets_after: DataFrame) -> None:
    metrics_before = calculate_metrics(tickets_before)
    metrics_after = calculate_metrics(tickets_after)
    plot_bar_charts(metrics_before, metrics_after)


def generate_optimization_page(org_structure: dict) -> None:
    st.title("Team Composition Optimization")

    # Generate tickets
    tickets: DataFrame | None = generate_tickets_page(org_structure)

    if tickets is None:
        return

    # Get unique departments from tickets
    departments = tickets["department"].unique()

    # Define optimization constraints
    constraints = {
        "max_tickets_per_employee": st.sidebar.slider(
            "Maximum Tickets per Employee", min_value=1, max_value=10, value=5
        ),
        "max_ticket_priority_sum_per_employee": st.sidebar.slider(
            "Maximum Ticket Priority Sum per Employee",
            min_value=1,
            max_value=20,
            value=10,
        ),
        "min_employees_per_department": st.sidebar.slider(
            "Minimum Employees per Department", min_value=1, max_value=5, value=2
        ),
    }
    for dept in departments:
        constraints[f"min_{dept}_tickets"] = st.sidebar.slider(
            f"Minimum {dept} Tickets", min_value=0, max_value=10, value=2
        )

    # Optimize team composition
    tickets = tickets.with_columns(arange(0, count()).alias("index"))
    tickets = tickets.sort("index", descending=False)
    optimal_team_df = optimize_team_composition(tickets, constraints)

    st.write("Optimal Team Composition:")
    st.dataframe(optimal_team_df)

    # Generate fake data
    fake_tickets = generate_fake_data(optimal_team_df)

    # # Calculate metrics before and after optimization
    # fake_metrics = calculate_metrics(fake_tickets)
    # optimal_metrics = calculate_metrics(optimal_team_df)

    generate_plots(fake_tickets, optimal_team_df)
