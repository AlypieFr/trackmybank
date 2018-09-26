trackmybank = {};

trackmybank.csrftocken = null;
trackmybank.current_month = null;
trackmybank.in_edition = null;
trackmybank.lang = null;
trackmybank.last_selected = null;
trackmybank.filters = {
    "category": {},
    "range": {}
};

trackmybank.init = function (csrftoken, lang) {
    trackmybank.csrftocken = csrftoken;
    trackmybank.lang = lang;
    trackmybank.current_month = $("select#months").val();
    trackmybank.load_content();
};

trackmybank.load_content = function() {
    $("input,select,textarea,#add").prop("disabled", true);
    trackmybank.show_loading();
    window.setTimeout(() => {
        trackmybank.get(
            url = "/transaction/",
            data = {},
            success = function (data, success) {
                if (success && data["success"]) {
                    $(".main-content").html(data["html"]);
                    trackmybank.resize_table();
                    trackmybank.init_special_fields();
                    trackmybank.init_table_click_events();
                    $("select.select2").select2({
                        placeholder: django.gettext("Select an option")
                    });
                    $("input.submit-form").on("click", trackmybank.init_submit_form);
                    $("input.cancel-edit").on("click", trackmybank.reset_edit);
                    $("select#months").on("change", trackmybank.change_month);
                    $(document).on("change", "input#link-to-selected", function() {
                        if ($(this).prop("checked")) {
                            $("input#date_t").prop("disabled", true);
                            $("input#date_b").prop("disabled", true);
                        }
                        else {
                            $("input#date_t").prop("disabled", false);
                            $("input#date_b").prop("disabled", false);
                        }
                    });
                    $("#add-month").on("click", trackmybank.show_hide_new_month_form);
                    $("#add-month-valid").on("click", trackmybank.add_new_month);
                    $(document).on("click", "#submit-change-bank_date", trackmybank.set_bank_date);
                    $(document).on("click", "#delete-transactions", trackmybank.delete_transactions);
                    $(window).on("resize", trackmybank.resize_table);
                    $(".main-tab").on("click", trackmybank.toggle_tab);
                    $(document).on("plotly_click", "#pie-chart-category", function(event, data) {
                        let color = $(data.event.path[0]).css("fill");
                        let label = data.points[0].label;
                        if (data.event.path[1] !== django.gettext("Free money")) {
                            trackmybank.toggle_filter(label, "category", color, data.event.path[1]);
                        }
                    });
                    $(document).on("plotly_click", "#pie-chart-range", function(event, data) {
                        let color = $(data.event.path[0]).css("fill");
                        let label = data.points[0].label;
                        trackmybank.toggle_filter(label, "range", color, data.event.path[1]);
                    });
                    $(document).on("click", ".delete-filter", function() {
                        let parent = $(this).parent();
                        let label = parent.attr("value");
                        let type = parent.attr("type-f");
                        trackmybank.remove_filter(label, type);
                    });
                    $(document).on("click", "#clear-filters", trackmybank.clear_filters)
                }
                else {
                    trackmybank.notify("message" in data ? data["message"] :
                        django.gettext("An error has occurred. Please contact the support"), "danger")
                }
                $("input,select,textarea,#add").prop("disabled", false);
                trackmybank.hide_loading();
            }
        );
    }, 0);
};

trackmybank.scroll_to_row = function(id_row) {
    $(".table-wrapper-scroll-y").animate({
        scrollTop: $("#t_" + id_row).offset().top - $(".table-wrapper-scroll-y").offset().top
    }, 500);
};

trackmybank.toggle_clear_filter_button = function() {
    if ($("div.filter").length > 0) {
        $("#clear-filters").show();
    }
    else {
        $("#clear-filters").hide();
        trackmybank.clear_filters_in_table();
    }
};

trackmybank.clear_filters = function() {
    $(".selected-filter").removeClass("selected-filter");
    $("div.filter").remove();
    trackmybank.filters.category = {};
    trackmybank.filters.range = {};
    trackmybank.toggle_clear_filter_button();
};

trackmybank.toggle_filter = function(label, type, color, data) {
    if (label in trackmybank.filters[type]) {
        trackmybank.remove_filter(label, type);
    }
    else {
        trackmybank.add_filter(label, type, color, data);
    }
};

trackmybank.remove_filter = function(label, type) {
    if (label in trackmybank.filters[type]) {
        let data = trackmybank.filters[type][label];
        $("#filters").find(`.filter[type-f='${type}'][value='${label}']`).remove();
        $(data).find("text").removeClass("selected-filter");
        delete trackmybank.filters[type][label];
    }
    else {
        console.warn(`Filter ${label} (${type}) does not exists`);
    }
    trackmybank.apply_filters();
};

trackmybank.add_filter = function(label, type, color, data) {
    $("#filters").append(
        $("<div>").addClass("filter")
            .addClass(type)
            .attr("type-f", type)
            .attr("value", label)
            .css("background-color", color)
            .html(label)
            .append(
                $("<div>").addClass("delete-filter")
            )
    );
    $(data).find("text").addClass("selected-filter");
    trackmybank.filters[type][label] = data;
    trackmybank.apply_filters();
};

trackmybank.keep_for_range = function(tr) {
    let keep = true;
    if (Object.keys(trackmybank.filters.range).length > 0) {
        keep = false;
        let amount = parseFloat($(tr).find("td.amount").attr("value").replace(",", "."));
        $.each(trackmybank.filters.range, function(range_str, data) {
            let range;
            if (range_str.startsWith("> ")) {
                range = [parseFloat(range_str.substr(2)), -1]
            }
            else {
                range = range_str.split("-").map(x => parseFloat(x));
            }
            if ((range[1] < 0 && amount >= range[0]) || (range[0] <= amount && amount < range[1])) {
                keep = true;
                return keep;
            }
        });
    }
    return keep;
};

trackmybank.apply_filters = function() {
    if (Object.keys(trackmybank.filters.category).length > 0) {
        $("div.main-left tr").each(function (i, tr) {
            if (!($(tr).find("td.category").attr("name") in trackmybank.filters.category)) {
                $(tr).hide();
            }
            else if (!trackmybank.keep_for_range(tr)) {
                $(tr).hide();
            }
            else {
                $(tr).show();
            }
        });
    }
    else if (Object.keys(trackmybank.filters.range).length > 0) {
        $("div.main-left tr").each(function (i, tr) {
            if (!trackmybank.keep_for_range(tr)) {
                $(tr).hide();
            }
            else {
                $(tr).show();
            }
        });
    }
    trackmybank.toggle_clear_filter_button();
};

trackmybank.clear_filters_in_table = function() {
    $(".main-left tbody tr").show();
};

trackmybank.toggle_tab = function() {
    if (!$(this).hasClass("selected")) {
        $($(".main-tab.selected").removeClass("selected").attr("show")).hide();
        $($(this).attr("show")).show();
        $(this).addClass("selected");
        trackmybank.resize_table();
    }
};

trackmybank.resize_table = function() {
    if ($(".main-tab").is(":visible") && !$(".main-tab[show='.main-right']").hasClass("selected")) {
        $(".main-right").hide();
    }
    else {
        if (!$(".main-tab").is(":visible")) {
            $(".main-left").show();
        }
        $(".main-right").show();
    }
    if ($(".main-left").is(":visible")) {
        $(".main-tab").removeClass("selected");
        $(".main-tab[show='.main-left']").addClass("selected");
    }
    let window_height = $(window).height();
    let table_position = $(".table-wrapper-scroll-y").position().top;
    $(".table-wrapper-scroll-y").css("height", window_height - table_position - 1 + "px");
    let right_position = $(".main-right").position().top;
    $(".main-right").height(window_height - right_position - 1 + "px");
};

trackmybank.init_special_fields = function() {
    trackmybank.set_datemask();

    //Decimal:
    $('.decimal').inputmask("decimal", {
        radixPoint: ",",
        digits: 2,
        digitsOptional: false,
        allowPlus: false,
        allowMinus: true
    })
};

trackmybank.set_datemask = function(element) {
    // Datetime picker:
    $(element ? element : '.datepicker').datetimepicker({
        format: "DD/MM/YYYY",
        locale: trackmybank.lang
    });

    let placeholder = 'dd/mm/yyyy';
    if (trackmybank.lang.split("-")[0] === "fr")
        placeholder = 'jj/mm/aaaa';
    $(element ? element : '.datemask').inputmask("datetime", {
        mask: "1/2/y",
        placeholder: placeholder,
        alias: "dd/mm/yyyy"
    });
}

trackmybank.is_add_month_form_visible = function() {
    return $("#add-month-form").is(":visible");
}

trackmybank.show_new_month_form = function() {
    $("#add-month-form").show();
};

trackmybank.hide_new_month_form = function() {
    $("#add-month-form").hide();
};

trackmybank.show_hide_new_month_form = function() {
    if (trackmybank.is_add_month_form_visible()) {
        trackmybank.hide_new_month_form();
    }
    else {
        trackmybank.show_new_month_form();
    }
};

trackmybank.set_bank_date = function() {
    let bank_date = $("#date_b_change").val();
    let selection = [];
    $.each($("tr.selected"), function (id, tr) {
        selection.push(parseInt($(tr).attr("id").split("_")[1]));
    });
    if (selection.length > 0) {
        trackmybank.show_loading();
        window.setTimeout(() => {
            trackmybank.post(
                url = "/bank-date/",
                data = {
                    date_b: bank_date,
                    transactions: selection.join("|")
                },
                success = function (data, success) {
                    if (success && data["success"]) {
                        $(".main-content").html(data["html"]);
                        trackmybank.resize_table();
                        $.each(selection, function (i, item) {
                            console.log(item);
                            $("tr#t_" + item.toString()).addClass("selected");
                        });
                        if (selection.length === 1) {
                            trackmybank.show_link_option();
                        }
                        $(".on-select").show();
                        trackmybank.set_datemask("#date_b_change");
                        $("#date_b_change").val(bank_date);
                        trackmybank.scroll_to_row($("tr.selected").first().attr("id").split("_")[1]);
                    }
                    else {
                        trackmybank.notify("message" in data ? data["message"] :
                            django.gettext("An error has occurred. Please contact the support"), "danger")
                    }
                    trackmybank.hide_loading();
                }
            );
        }, 0);
    }
    else {
        trackmybank.notify(django.gettext("Empty selection"), "danger");
    }
};

trackmybank.delete_transactions = function() {
    if (confirm(django.gettext("Delete selected transactions?"))) {
        trackmybank.show_loading();
        let selection = [];
        $.each($("tr.selected"), function (id, tr) {
            selection.push(parseInt($(tr).attr("id").split("_")[1]));
        });
        if (selection.length > 0) {
            trackmybank.show_loading();
            window.setTimeout(() => {
                trackmybank.post(
                    url = "/delete-transaction/",
                    data = {
                        transactions: selection.join("|")
                    },
                    success = function (data, success) {
                        if (success && data["success"]) {
                            trackmybank.clear_selection();
                            $(".main-content").html(data["html"]);
                            trackmybank.resize_table();
                            trackmybank.set_datemask("#date_b_change");
                        }
                    else {
                        trackmybank.notify("message" in data ? data["message"] :
                            django.gettext("An error has occurred. Please contact the support"), "danger")
                    }
                    trackmybank.hide_loading();
                    }
                );
            }, 0);
        }
        else {
            trackmybank.notify(django.gettext("Empty selection"), "danger");
        }
    }
};

trackmybank.add_new_month = function() {
    trackmybank.show_loading();
    window.setTimeout(() => {
        trackmybank.post(
            url = "/month/",
            data = {
                month: $("#select-added-month").val(),
                year: $("#added-month-year").val(),
                salary: $("#added-month-salary").val()
            },
            success = function (data, success) {
                if (success && data["success"]) {
                    window.location.href = "/";
                }
                else {
                    trackmybank.notify("message" in data ? data["message"] :
                        django.gettext("An error has occurred. Please contact the support"), "danger")
                }
                trackmybank.hide_loading();
            }
        );
    }, 0);
};

trackmybank.show_link_option = function() {
    $("div.link-to-selected").show();
};

trackmybank.hide_link_option = function() {
    $("div.link-to-selected").hide();
    $("input#link-to-selected").bootstrapToggle('off');
};

trackmybank.clear_selection = function() {
    $("table#list-tr tbody tr").removeClass("selected");
    trackmybank.hide_link_option();
    $(".on-select").hide();
    trackmybank.last_selected = null;
};

trackmybank.init_table_click_events = function() {
    $(document).on("click", "table#list-tr tbody tr", function(e) {
        if (trackmybank.in_edition == null) {
            let doSelect = true;
            if ($(this).hasClass("selected")) {
                $(this).removeClass("selected");
                doSelect = false;
            }
            if (!e.ctrlKey && !e.shiftKey) {
                $("table#list-tr tbody tr").removeClass("selected");
            }
            if (e.shiftKey) {
                if (trackmybank.last_selected != null) {
                    if($(`tr[nb=${trackmybank.last_selected}]`).hasClass("selected")) {
                        let current_nb = parseInt($(this).attr("nb"));
                        let from_nb = Math.min(current_nb, trackmybank.last_selected);
                        let to_nb = Math.max(current_nb, trackmybank.last_selected);
                        let current = $(`tr[nb=${from_nb}]`).next();
                        current_nb = parseInt(current.attr("nb"))
                        while (current_nb !== to_nb) {
                            current.addClass("selected");
                            current = $(`tr[nb=${current_nb}]`).next();
                            current_nb = parseInt(current.attr("nb"))
                        }
                    }
                }
            }
            if (doSelect) {
                $(this).addClass("selected");
            }

            if ($("tr.selected").length === 1) {
                trackmybank.show_link_option();
                $(".on-select").show();
                trackmybank.last_selected = parseInt($(this).attr("nb"));
            }
            else if ($("tr.selected").length > 0) {
                trackmybank.hide_link_option();
                $(".on-select").show();
                trackmybank.last_selected = parseInt($(this).attr("nb"));
            }
            else {
                trackmybank.hide_link_option();
                $(".on-select").hide();
                trackmybank.last_selected = null;
            }
        }
    });

    $(document).on("dblclick", "table#list-tr tbody tr", function(e) {
        trackmybank.clear_selection();
        $("table#list-tr tbody tr").removeClass("edited");
        document.getSelection().removeAllRanges();
        trackmybank.edit($(this));

    });

    // Remove selection on escape pressed:
    $(document).on("keyup", function(e) {
        if (e.keyCode === 27) {
            if (trackmybank.is_add_month_form_visible()) {
                trackmybank.hide_new_month_form();
            }
            else {
                trackmybank.clear_selection();
                if (trackmybank.in_edition != null) {
                    trackmybank.reset_edit();
                }
            }
        }
    });
};

trackmybank.edit = function(jq_tr) {
    jq_tr.addClass("edited");
    trackmybank.in_edition = parseInt(jq_tr.attr("id").split("_")[1]);
    $("input#date_t").val(jq_tr.find("td.date_t").length === 1 ? jq_tr.find("td.date_t").attr("value") : jq_tr.find("td.total").attr("value").split(",")[0]);
    $("input#date_b").val(jq_tr.find("td.date_b").length === 1 ? jq_tr.find("td.date_b").attr("value") : jq_tr.find("td.total").attr("value").split(",")[1]);
    $("input#amount").val(jq_tr.find("td.amount").attr("value"));
    $("textarea#subject").val(jq_tr.find("td.subject").attr("value"));
    $("select#category").val(jq_tr.find("td.category").attr("value")).trigger("change.select2");
    $("input.submit-form").val(django.gettext("Edit"));
    $("input.cancel-edit").show();
};

trackmybank.reset_edit = function() {
    trackmybank.in_edition = null;
    $("table#list-tr tbody tr").removeClass("edited");
    $("input.submit-form").val(django.gettext("Add"));
    $("input.cancel-edit").hide();
    trackmybank.reset_form();
};

trackmybank.init_submit_form = function () {
    $("label").removeClass("error");

    let date = $("input#date_t").val();
    let date_bank = $("input#date_b").val();
    let amount = $("input#amount").val();
    let subject = $("textarea#subject").val();
    let category = $("select#category").val();
    let month = $("select#months").val();
    if (month == null) {
        trackmybank.notify(django.gettext("You must create a month before"), "danger");
        return false;
    }
    let id_group = null;
    if ($("input#link-to-selected").prop("checked")) {
        let selection = $("table#list-tr tr.selected");
        if (selection.length === 0) {
            trackmybank.notify(django.gettext("Error: empty selection"), "danger");
            return false;
        }
        else if (selection.length > 1) {
            trackmybank.notify(django.gettext("Error: more than one transaction selected"), "danger");
            return false;
        }
        id_group = parseInt(selection.attr("group"));
    }

    if (trackmybank.valid_form(date, date_bank, amount, subject, category)) {
        trackmybank.submit_form(date, date_bank, amount, subject, category, month, id_group);
    }
    else {
        trackmybank.notify(django.gettext("Some required fields are empty"), "danger");
    }
};

trackmybank.reset_form = function() {
    $("input#date_t").val("");
    $("input#date_b").val("");
    $("input#amount").val("");
    $("textarea#subject").val("");
    $("select#category").val("").trigger("change.select2");
};

trackmybank.submit_form = function(date, date_bank, amount, subject, category, month, id_group) {
    trackmybank.show_loading();
    let checkbox = $("input#link-to-selected");
    window.setTimeout(() => {
        trackmybank.post(
            url = "/transaction/",
            data = {
                date_t: checkbox.prop("checked") ? null : date,
                date_bank: checkbox.prop("checked") ? null :  date_bank,
                amount: amount,
                subject: subject,
                category: category,
                month: checkbox.prop("checked") ? null :  month,
                group_id: id_group,
                tr_id: trackmybank.in_edition == null ? null : trackmybank.in_edition
            },
            success = function (data, success) {
                if (success && data["success"]) {
                    $(".main-content").html(data["html"]);
                    trackmybank.resize_table();
                    if (trackmybank.in_edition == null) {
                        trackmybank.reset_form();
                    } else {
                        trackmybank.reset_edit();
                    }
                    trackmybank.clear_selection();
                    trackmybank.scroll_to_row(data["tr_id"]);
                }
                else {
                    trackmybank.notify("message" in data ? data["message"] :
                        django.gettext("An error has occurred. Please contact the support"), "danger")
                }
                trackmybank.hide_loading();
            }
        )
    }, 0);
};

trackmybank.valid_form = function(date, date_bank, amount, subject, category) {
    let valid = true;
    if (date === "" && !$("input#link-to-selected").prop("checked")) {
        valid = false;
        $("label[for=date_t]").addClass("error");
    }
    if (amount === "" || amount === "0,00" || amount === "0.00") {
        valid = false;
        $("label[for=amount]").addClass("error");
    }
    if (subject === "") {
        valid = false;
        $("label[for=subject]").addClass("error");
    }
    if (category === "") {
        valid = false;
        $("label[for=category]").addClass("error");
    }
    return valid
};

trackmybank.change_month = function(e) {
    trackmybank.show_loading();
    window.setTimeout(() => {
        let value = $(this).val();
        trackmybank.post(
            url = "/select-month/",
            data = {
                "month": value
            },
            success = function (data, success) {
                if (success && data["success"]) {
                    $(".main-content").html(data["html"]);
                    trackmybank.resize_table();
                    trackmybank.current_month = value;
                    trackmybank.clear_selection();
                }
                else {
                    $("select#months").val(trackmybank.current_month).trigger("change.select2");
                    trackmybank.notify("message" in data ? data["message"] :
                        django.gettext("An error has occurred. Please contact the support"))
                }
                trackmybank.hide_loading();
            }
        );
    }, 0);
};

trackmybank.notify = function(message, type) {
    $.notify({
            message: message},{
            type: type,
            offset: {x: 5, y: 55},
            animate: {
                enter: 'animated fadeInDown',
                exit: 'animated fadeOutUp'
            },
        })
};

trackmybank.show_loading = function() {
    $(".loading").show();
    $(".lds-facebook").show();
};

trackmybank.hide_loading = function() {
    $(".loading").hide();
    $(".lds-facebook").hide();
}

trackmybank.ajax = function(url, data, success, error, method="POST", async=true) {
    $.ajax(url,
        {
            method: method,
            data: data,
            success: success,
            error: error || function () {
                trackmybank.hide_loading();
                trackmybank.notify(django.gettext("An error occurred! Please contact the support to report the bug"), "danger");
            },
            async: async,
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", trackmybank.csrftocken);
            }
        }
    );
};

trackmybank.post = function(url, data, success, error, async=true) {
    trackmybank.ajax(
        url=url,
        data=data,
        success=success,
        error=error,
        method="POST",
        async=async
    );
};

trackmybank.get = function (url, data, success, error, async = true) {
    trackmybank.ajax(
        url=url,
        data=data,
        success=success,
        error=error,
        method="GET",
        async=async
    );
};