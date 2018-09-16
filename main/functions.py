from main.models import Month,CurrentMonth


def get_current_month(user):
    """
    Return the current month

    :param: user: user for which we search current month
    :return: current month object
    """
    month = CurrentMonth.objects.filter(user=user).first()
    if month is None:
        month = Month.objects.last()
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
