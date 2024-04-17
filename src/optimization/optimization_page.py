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

    # Ensure we account for the maximum number of entries in both before and after datasets
    max_entries = max(
        len(df_before["avg_priority_per_employee"]),
        len(df_after["avg_priority_per_employee"]),
    )
    bar_width = 0.35
    r1 = np.arange(max_entries)
    r2 = [x + bar_width for x in r1]

    # Define a helper function to safely get data
    def safe_get(df, index, column):  # type: ignore
        try:
            return df[index][column]
        except IndexError:
            return 0  # return 0 if index is out of bounds

    # Plot each metric
    for ax, metric_key, title in zip(
        axes,
        [
            "avg_priority_per_employee",
            "total_tickets_per_department",
            "employees_per_department",
        ],
        [
            "Average Ticket Priority Per Employee",
            "Total Tickets Per Department",
            "Unique Employees Per Department",
        ],
    ):
        # Plot before optimization
        ax.bar(
            r1,
            [
                safe_get(
                    df_before[metric_key],
                    i,
                    "avg_priority"
                    if "avg_priority" in df_before[metric_key].columns
                    else "total_tickets"
                    if "total_tickets" in df_before[metric_key].columns
                    else "unique_employees",
                )
                for i in range(max_entries)
            ],
            color="blue",
            width=bar_width,
            edgecolor="grey",
            label="Before Optimization",
        )
        # Plot after optimization
        ax.bar(
            r2,
            [
                safe_get(
                    df_after[metric_key],
                    i,
                    "avg_priority"
                    if "avg_priority" in df_after[metric_key].columns
                    else "total_tickets"
                    if "total_tickets" in df_after[metric_key].columns
                    else "unique_employees",
                )
                for i in range(max_entries)
            ],
            color="red",
            width=bar_width,
            edgecolor="grey",
            label="After Optimization",
        )
        ax.set_title(title)
        ax.set_xticks([r + bar_width / 2 for r in r1])
        ax.set_xticklabels(
            df_before[metric_key]["department"]
            if "department" in df_before[metric_key].columns
            else df_before[metric_key]["assigned_to"]
        )
        ax.legend()

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

    if "init" not in st.session_state:
        st.session_state.init = False
        st.session_state.tickets = None
        st.session_state.constraints = {}

    # Setup form for initializing ticket generation and optimization constraints
    with st.form("Initialization Form"):
        st.subheader("Initialize Tickets and Set Constraints")

        # Placeholder for other settings, assuming you might need some configurations for generating tickets
        generate_tickets = st.checkbox("Generate Tickets", value=st.session_state.init)

        # Constraints for optimization
        max_tickets = st.slider(
            "Maximum Tickets per Employee", min_value=1, max_value=10, value=5
        )
        max_priority_sum = st.slider(
            "Maximum Ticket Priority Sum per Employee",
            min_value=1,
            max_value=20,
            value=10,
        )
        min_employees = st.slider(
            "Minimum Employees per Department", min_value=1, max_value=5, value=2
        )

        # Form submission button
        submitted = st.form_submit_button("Initialize and Optimize")

        if submitted:
            st.session_state.init = generate_tickets
            st.session_state.constraints = {
                "max_tickets_per_employee": max_tickets,
                "max_ticket_priority_sum_per_employee": max_priority_sum,
                "min_employees_per_department": min_employees,
            }

    # If tickets are to be generated
    if st.session_state.init:
        # Generate tickets
        st.session_state.tickets = generate_tickets_page(org_structure)

        if st.session_state.tickets is None:
            st.write("No tickets found.")
        else:
            # Display unique departments from tickets
            # departments = st.session_state.tickets["department"].unique()
            # for dept in departments:
            #     dept_key = f"min_{dept}_tickets"
            #     if dept_key not in st.session_state.constraints:
            #         st.session_state.constraints[dept_key] = st.sidebar.slider(
            #             f"Minimum {dept} Tickets", min_value=0, max_value=10, value=2
            #         )

            # Check if the optimization should be triggered
            if "constraints" in st.session_state and st.session_state.constraints:
                # Optimize team composition
                st.session_state.tickets = st.session_state.tickets.with_columns(
                    arange(0, count()).alias("index")
                )
                st.session_state.tickets = st.session_state.tickets.sort(
                    "index", descending=False
                )
                optimized_tickets = optimize_team_composition(
                    st.session_state.tickets, st.session_state.constraints
                )

                st.write("Optimal Team Composition:")
                st.dataframe(optimized_tickets)

                # Generate fake data
                # fake_tickets = generate_fake_data(optimized_tickets)

                # # Generate plots based on fake and optimized data
                # generate_plots(fake_tickets, optimized_tickets)
