var StepOptions;

function updateSteps() {
    let selects = $("#assignment-steps select");
    let steps = [];
    selects.each(e => {
        steps.push(selects[e].value);
    });

    $("#assignment-steps-input").val(JSON.stringify(steps));
}

function createStepCard() {
    let id = Math.floor(Math.random() * Math.pow(10, 16));
    let div = $("<div></div>", {
        class: ["grid-auto-col", "gap"].join(" "),
        id: id
    });

    let select = $("<select></select>");
    StepOptions.forEach(e => {
        let option = $("<option></option>", { value: e[0] });
        option.text(e[1]);
        select.append(option);
    });
    select.change(updateSteps);

    let button = $("<button></button>", {
        class: ["as-btn", "pad", "border-radius", "background-red"].join(" "),
        type: "button",
    });
    button.text("Remove");
    button.click(() => {
        $(`#${id}`).remove();
        updateSteps();
    });


    div.append(select);
    div.append(button);

    return div;
}

function addStep() {
    $("#assignment-steps").append(createStepCard());
    updateSteps();
}

function submitNewAssignment() {
    $("#id_steps").val($("#assignment-steps-input").val());
}