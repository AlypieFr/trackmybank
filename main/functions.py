# TrackMyBank, a simple bank management tool
# 
# Copyright (C) 2018 Floreal Cabanettes <comm@flo-art.fr>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 3.0

from collections import OrderedDict
import datetime
from django.utils.translation import ugettext as _

from main.models import Month, CurrentMonth, Category, Transaction

import plotly as py
import plotly.graph_objs as go


def get_current_month(user):
    """
    Return the current month

    :param: user: user for which we search current month
    :type user: User
    :return: current month object
    :rtype: Month
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


def _get_plotly_figure(plot_item, left_margin=15):
    layout = go.Layout(
        margin=go.layout.Margin(
            l=left_margin,
            r=10,
            b=30,
            t=30,
            pad=4
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        barmode='stack',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        hiddenlabels=[_("Free money")],
        yaxis=dict(rangemode='nonnegative',)
    )
    fig = go.Figure(data=[plot_item] if not isinstance(plot_item, list) else plot_item, layout=layout)
    return py.offline.plot(fig, output_type="div", include_plotlyjs=False, config={"showLink": False})


def build_category_pie_chart(count_by_cat, count_free_money):
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
    if count_free_money > 0:
        labels.append(_("Free money"))
        values.append(count_free_money)
        colors.append("#006600")
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


def build_weekly_spending(start, end):
    """
    Build total amount of spending per week graph

    :param start: starting date
    :type start: datetime.datetime
    :param end: ending date
    :type end: datetime.datetime
    :return:
    """
    start = start - datetime.timedelta(days=start.weekday())
    end = end + datetime.timedelta(days=-end.weekday() - 1, weeks=1)
    start_week = start
    end_week = start_week + datetime.timedelta(days=6)
    tr_per_week = OrderedDict()
    n = 0
    all_cats = set()
    while end_week < end + datetime.timedelta(days=2):
        tr_per_week_key = "%02d/%02d -> %02d/%02d" % (start_week.day, start_week.month, end_week.day, end_week.month)
        total_by_cat = {}
        for transaction in Transaction.objects.filter(group__date_t__gte=start_week, group__date_t__lte=end_week,
                                                      group__ignore_week_filters=False):
            cat = transaction.category
            if not cat.ignore_week_filters:
                cat_name = cat.name
                if cat_name not in total_by_cat:
                    all_cats.add(cat_name)
                    total_by_cat[cat_name] = 0
                total_by_cat[cat_name] += transaction.amount
        tr_per_week[tr_per_week_key] = total_by_cat
        start_week = end_week + datetime.timedelta(days=1)
        end_week = start_week + datetime.timedelta(days=6)
        n += 1
    if len(all_cats) > 0:
        for week, tr_week in tr_per_week.items():
            for cat in all_cats:
                if cat not in tr_week:
                    tr_week[cat] = 0
    traces = []
    if len(all_cats) > 0:
        for category in sorted(all_cats):
            traces.append(go.Bar(
                                 x=list(tr_per_week.keys()),
                                 y=[k[category] for k in tr_per_week.values()],
                                 name=category,
                                 marker=dict(
                                    color=Category.objects.get(name=category).color)
            ))
    else:
        traces.append(go.Bar(
            x=list(tr_per_week.keys()),
            y=[0 for k in tr_per_week.values()],
            name=_("No data")
        ))
    return _get_plotly_figure(traces, 50)


def build_goodies_pie_chart(salary, total_goodies):
    """
    Pie chart for showing proportion of goodies in current month

    :param salary: month's salary
    :param total_goodies: total of goodies spending
    :return: plotly figure
    """
    values = [total_goodies, salary - total_goodies]
    labels = [_("Goodies"), _("Other")]

    pie = go.Pie(values=values,
                 labels=labels,
                 hoverinfo="label+percent+value",
                 sort=False,
                 marker=dict(colors=["#ffbeb3", "#000"]))

    return _get_plotly_figure(pie)
