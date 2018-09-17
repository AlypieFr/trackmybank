trackmybank = {};

trackmybank.csrftocken = null;
trackmybank.current_month = null;
trackmybank.in_edition = null;

trackmybank.init = function (csrftoken) {
    trackmybank.csrftocken = csrftoken;
    trackmybank.current_month = $("select#months").val();
    trackmybank.init_special_fields();
    trackmybank.init_table_click_events();
    $("select.select2").select2({
        placeholder: django.gettext("Select an option")
    });
    $("input.submit-form").on("click", trackmybank.init_submit_form);
    $("input.cancel-edit").on("click", trackmybank.reset_edit);
    $("select#months").on("change", trackmybank.change_month);
};

trackmybank.init_special_fields = function() {
    let lang = "fr-fr";
    // Datetime picker:
    $(".datepicker").datetimepicker({
        format: "DD/MM/YYYY",
        locale: lang
    });
    let placeholder = 'dd/mm/yyyy';
    if (lang.split("-")[0] === "fr")
        placeholder = 'jj/mm/aaaa';
    $('.datemask').inputmask("datetime", {
        mask: "1/2/y",
        placeholder: placeholder,
        alias: "dd/mm/yyyy"
    });

    //Decimal:
    $('.decimal').inputmask("decimal", {
        radixPoint: ",",
        digits: 2,
        digitsOptional: false,
        allowPlus: false,
        allowMinus: true
    })
};

trackmybank.init_table_click_events = function() {
    $(document).on("click", "table#list-tr tbody tr", function(e) {
        if (trackmybank.in_edition == null) {
            let doSelect = true;
            if ($(this).hasClass("selected")) {
                $(this).removeClass("selected");
                doSelect = false;
            }
            if (!e.ctrlKey) {
                $("table#list-tr tbody tr").removeClass("selected");
            }
            if (doSelect) {
                $(this).addClass("selected");
            }
        }
    });

    $(document).on("dblclick", "table#list-tr tbody tr", function(e) {
        $("table#list-tr tbody tr").removeClass("selected");
        $("table#list-tr tbody tr").removeClass("edited");
        document.getSelection().removeAllRanges();
        trackmybank.edit($(this));

    });

    // Remove selection on escape pressed:
    $(document).on("keyup", function(e) {
        if (e.keyCode == 27) {
            $("table#list-tr tbody tr").removeClass("selected");
            if (trackmybank.in_edition != null) {
                trackmybank.reset_edit();
            }
        }
    });
};

trackmybank.edit = function(jq_tr) {
    jq_tr.addClass("edited");
    trackmybank.in_edition = parseInt(jq_tr.attr("id").split("_")[1]);
    $("input#date_t").val(jq_tr.find("td.date_t").length === 1 ? jq_tr.find("td.date_t").html() : jq_tr.find("total").attr("value").split(" ")[0]);
    $("input#date_b").val(jq_tr.find("td.date_b").length === 1 ? jq_tr.find("td.date_b").html() : jq_tr.find("total").attr("value").split(" ")[1]);
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

    if (trackmybank.valid_form(date, date_bank, amount, subject, category)) {
        trackmybank.submit_form(date, date_bank, amount, subject, category, month);
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

trackmybank.submit_form = function(date, date_bank, amount, subject, category, month) {
    trackmybank.show_loading();
    window.setTimeout(() => {
        trackmybank.post(
            url = "/transaction/",
            data = {
                date_t: date,
                date_bank: date_bank,
                amount: amount,
                subject: subject,
                category: category,
                month: month,
                tr_id: trackmybank.in_edition == null ? null : trackmybank.in_edition,
                csrfmiddlewaretoken: trackmybank.csrftocken
            },
            success = function (data, success) {
                if (success && data["success"]) {
                    $(".main-content").html(data["html"]);
                    if (trackmybank.in_edition == null) {
                        trackmybank.reset_form();
                    } else {
                        trackmybank.reset_edit();
                    }
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
    if (date === "") {
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
                "month": value,
                csrfmiddlewaretoken: trackmybank.csrftocken
            },
            success = function (data, success) {
                if (success && data["success"]) {
                    $(".main-content").html(data["html"]);
                    trackmybank.current_month = value;
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

trackmybank.ajax = function(url, data, success, error, method="POST") {
    $.ajax(url,
        {
            method: method,
            data: data,
            success: success,
            error: error || function () {
                trackmybank.hide_loading();
                trackmybank.notify("An error occurred! Please contact us to report the bug", "danger");
            },
        }
    );
};

trackmybank.post = function(url, data, success, error, async=true) {
    trackmybank.ajax({
        url: url,
        data: data,
        success: success,
        error: error,
        type: "POST",
        async: async
    });
};
