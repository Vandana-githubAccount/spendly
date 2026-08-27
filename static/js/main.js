document.addEventListener("DOMContentLoaded", function () {
    var rangeSelect = document.getElementById("range");
    var customFields = document.getElementById("custom-range-fields");

    if (!rangeSelect || !customFields) {
        return;
    }

    function toggleCustomFields() {
        if (rangeSelect.value === "custom") {
            customFields.classList.remove("is-hidden");
        } else {
            customFields.classList.add("is-hidden");
        }
    }

    toggleCustomFields();
    rangeSelect.addEventListener("change", toggleCustomFields);
});
