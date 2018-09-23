# TrackMyBank, a simple bank management tool
# 
# Copyright (C) 2018 Floreal Cabanettes <comm@flo-art.fr>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 3.0

from main.models import Month, CurrentMonth, Category
import plotly as py
import plotly.graph_objs as go


def get_current_month(user):
    """
    Return the current month

    :param: user: user for which we search current month
    :return: current month object
    """
    month = CurrentMonth.objects.filter(user=user).first()
    if month is None:
        month = Month.objects.last()
        if month is not None:
            c_month = CurrentMonth(month=month, user=user)
            c_month.save()
        return month
    return month.month


def set_current_month(month, user):
    """
    Set current month for a user

    :param month:
    :param user:
    :return:
    """
    c_month = CurrentMonth.objects.filter(user=user)
    if month is not None:
        c_month.delete()
    c_month = CurrentMonth(month=month, user=user)
    c_month.save()


def _get_plotly_figure(plot_item):
    layout = go.Layout(
        margin=go.Margin(
            l=15,
            r=10,
            b=30,
            t=30,
            pad=4
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400
    )
    fig = go.Figure(data=[plot_item], layout=layout)
    return py.offline.plot(fig, output_type="div", include_plotlyjs=False, config={"showLink": False})


def build_category_pie_chart(count_by_cat):
    """
    Build category pie chart

    :param count_by_cat: total amount of transactions by category
    :type count_by_cat: dict
    :return:
    """
    values = []
    labels = []
    colors = []
    for category, amount in count_by_cat.items():
        values.append(amount)
        labels.append(category)
        colors.append(Category.objects.get(name=category).color)
    pie = go.Pie(values=values,
                 labels=labels,
                 hoverinfo="label+percent+value",
                 marker=dict(colors=colors))
    return _get_plotly_figure(pie)


def build_tranches_pie_chart(counts_by_tranches):
    """
    Build pie charts of ranges of amounts

    :param counts_by_tranches: count by tranche
    :type counts_by_tranches: dict
    :return:
    """
    values = []
    labels = []
    for tranche, count_t in counts_by_tranches.items():
        if count_t > 0:
            if tranche[1] > 0:
                labels.append("-".join(map(str, tranche)))
            else:
                labels.append("> " + str(tranche[0]))
            values.append(count_t)

    pie = go.Pie(values=values,
                 labels=labels,
                 hoverinfo="label+percent+value")

    return _get_plotly_figure(pie)
