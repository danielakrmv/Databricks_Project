from uapc_aiacad.transformations.get_most_purchased_and_less_purchased_articles_per_unit_of_measure import *

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta
from pyspark.sql import DataFrame
from sklearn.linear_model import LinearRegression

reg = LinearRegression()
current_time = datetime.now()
to_date = current_time.date() - timedelta(weeks=5)


def creating_visualization_from_df(df: DataFrame, x_axis_col: str, y_axis_col: str, unit_of_measure: str, top: str):
    # first display df with data for better illustration
    display_df(df)

    vis_data = df.toPandas()
    fig, ax = plt.subplots(figsize=(15, 6))
    s = sns.barplot(data=vis_data,
                    x=f"{x_axis_col}",
                    y=f"{y_axis_col}",
                    hue=vis_data["group_names"],
                    palette="magma",
                    ax=ax,
                    dodge=False)

    for c in ax.containers:
        ax.bar_label(c, label_type='edge', color="black")

    for names in ax.get_xticklabels():
        names.set_fontweight("bold")

    for numbers in ax.get_yticklabels():
        numbers.set_fontweight("bold")

    plt.xlabel(xlabel=f"Total quantity per {unit_of_measure}", fontsize=20)
    plt.ylabel(ylabel="Names of articles", fontsize=20)
    plt.title(f"10 {top} purchased articles per {unit_of_measure} in Bulgaria from {to_date} to {current_time.date()}",
              fontsize=20)
    plt.show()

    return fig


def draw_linear_regression_for_daily_purchased_quantity(df: DataFrame, x_axis_column: str, y_axis_column: str, top: str, unit_of_measure: str):
    # first display df with data for better illustration
    display_df(df)

    # extract x and y from dataframe
    x = df[[x_axis_column]] # day of week from 1-7 and corresponding indexes - predictor
    y = df[[y_axis_column]] # min_daily_quantity_in_thousand and corresponding indexes - dependent var

    # fit the mode
    reg.fit(x, y) # class 'sklearn.linear_model._base.LinearRegression'

    # Y = bX + A - where -
    # Y denotes the predicted value,
    # b denotes the slope of the line,
    # X denotes the independent variable,
    # A is the Y intercept

    # print the slope and intercept if desired
    print('intercept:', reg.intercept_[0])
    print('slope:', reg.coef_[0][0])

    # select x1 and x2 and get the corresponding date from the index
    x1 = df[x_axis_column].min()
    x1_date = df[df[x_axis_column].eq(x1)].index[0]
    x2 = df[x_axis_column].max()
    x2_date = df[df[x_axis_column].eq(x2)].index[0]

    # calculate y1, given x1
    y1 = reg.predict(np.array([[x1]]))[0][0]

    print('y1:', y1)

    # calculate y2, given x2
    y2 = reg.predict(np.array([[x2]]))[0][0]

    print('y2:', y2)

    ax1 = df.plot(y=y_axis_column, x='day_name', c='k', figsize=(15, 6), legend=False)
    ax1.plot([x1_date, x2_date], [y1, y2], label='Linear Model', c='magenta')
    plt.legend(fontsize="large")
    plt.xlabel("Day of the week", size=16)
    if unit_of_measure == "ST":
        plt.ylabel(f"{top} daily quantity in thsd", size=16)
    elif unit_of_measure == "KG":
        plt.ylabel(f"{top} daily quantity", size=16)
    plt.title(f"Linear regression of {top} distribute daily quantity "
              f"of the articles sold per {unit_of_measure} in Bulgaria on this day from from {to_date} to {current_time.date()}",
              size=16)
    ax1.yaxis.set_tick_params(labelsize=12)
    ax1.xaxis.set_tick_params(labelsize=12)
    ax1.yaxis.offsetText.set_fontsize(12)

    return plt.show()