"""graph covid cases by date by state"""


from os import getcwd

import pandas as pd
import plotly.express as px


def main():
    """main"""
    covid_data = pd.read_csv(
        'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv')\
        .rename(columns={"state": "State"})

    state_pop = pd.read_csv(
        "https://raw.githubusercontent.com/jakevdp/data-USstates/master/state-population.csv")\
        .rename(columns={"state/region": "State"})
    states = pd.read_csv(f"{getcwd()}/csvData.csv")

    covid_data = massage_data(covid_data, state_pop, states)

    graph_data(covid_data)


def graph_data(covid_data):
    """
    Graph the data

    Args:
        covid_data (pd.DataFrame): Data to graph
    """
    max_cases_per_capita = max(covid_data["new_cases_per_capita"])

    fig = px.choropleth(covid_data,
                        locations='Code',
                        color="new_cases_per_capita",
                        animation_frame="date",
                        locationmode='USA-states',
                        scope="usa",
                        range_color=(0, max_cases_per_capita),
                        title='Cases per Capita by State',
                        height=600,
                        color_continuous_scale=["yellow", "red"]
                        )

    # Update legend to say "Cases per Capita"
    fig.update_layout(legend_title_text="Cases per Capita")

    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 1
    fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 1

    fig.show()


def massage_data(covid_data: pd.DataFrame,
                 state_pop: pd.DataFrame,
                 states: pd.DataFrame
                 ) -> pd.DataFrame:
    """
    Get the data in the right format

    Args:
        covid_data (pd.DataFrame): covid data
        state_pop (pd.DataFrame): state population data
        states (pd.DataFrame): state abbreviations

    Returns:
        pd.DataFrame: massaged data
    """

    # Only get state totals
    state_pop = state_pop[state_pop["ages"] == "total"]
    state_pop = state_pop.groupby("State").max(
    ).reset_index().rename(columns={"Code": "State"})

    # for each state, for each day, get the difference in numbers of cases
    covid_data["new_cases"] = covid_data.groupby("State")["cases"].diff()

    # turn NaN into 0 in new_cases
    covid_data["new_cases"].fillna(0, inplace=True)

    # for each state, get the 7 day moving average of new cases
    covid_data["7_day_moving_average"] = covid_data.groupby("State")["new_cases"].\
        transform(lambda x: x.rolling(7).mean())

    # Join the data
    covid_data = covid_data.join(states.set_index('State'), on='State')
    covid_data = covid_data.join(state_pop.set_index('State'), on='Code')

    covid_data = covid_data.drop(columns=["deaths", "Abbrev", "year", "ages"])

    # new cases per capita is the new cases divided by the population of the state
    covid_data["new_cases_per_capita"] = covid_data["7_day_moving_average"] / \
        covid_data["population"]

    # turn NaN into 0
    covid_data["new_cases_per_capita"] = covid_data["new_cases_per_capita"].fillna(
        0)

    # turn date column into date type
    covid_data["date"] = pd.to_datetime(covid_data["date"])
    covid_data = covid_data.sort_values('date', ascending=True)
    covid_data['date'] = covid_data['date'].dt.strftime('%m-%d-%Y')

    return covid_data


if __name__ == "__main__":
    main()
