trackmybank = {};

trackmybank.init = function () {
    trackmybank.init_date_fields();
};

trackmybank.init_date_fields = function() {
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
};