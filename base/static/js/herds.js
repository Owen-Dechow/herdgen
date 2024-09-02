var Herd;
var Assignments;
var CurrentAssignmentStep;
var RevalidateMalesForBreeding = false;
var ValidatingMalesForBreeding = false;
var MalesValidatedForBreeding = false;

async function getHerd(classId, herdId) {
    Herd = await $.ajax({
        url: `/class/${classId}/herd/${herdId}/get`,
        dataType: "json",
    }).fail("Error: Could not load herd data.");
};

function createAnimalCard(animalId, animalName, animal, classId, herdId) {
    let btn = $("<button></button>", { id: `anim-${animalId}`, class: "animal-btn", autofilter: true });
    btn.text(animalName);
    btn.click(() => {
        $(".animal-btn.selected").removeClass("selected");
        btn.addClass("selected");
        animalSelected(animal, classId, herdId);
    });

    return btn;
}

function resolveSortKey(sortKey, animal) {
    let sortKeyCp = [...sortKey];
    key = sortKeyCp.shift();
    animal = animal[key];

    if (sortKeyCp.length == 0)
        return animal;
    else
        return resolveSortKey(sortKeyCp, animal);

}

function loadHerd(sortKey, reversed, classId, herdId) {
    $("#males").html("");
    $("#females").html("");

    let animals = [];
    for (let animal in Herd["animals"]) {
        animals.push(Herd["animals"][animal]);
    }

    animals.sort((b, a) => { return resolveSortKey(sortKey, a) - resolveSortKey(sortKey, b); });
    if (reversed)
        animals.reverse();

    animals.forEach((animal) => {
        if (animal["male"])
            $("#males").append(createAnimalCard(animal["id"], animal["name"], animal, classId, herdId));
        else
            $("#females").append(createAnimalCard(animal["id"], animal["name"], animal, classId, herdId));
    });
}

function createSortOptionCard(text, value) {
    let opt = $(`<option></option>`, { value: value, autofilter: true });
    opt.text(text);
    return opt;
}

function loadSortOptions() {
    $("#sort-options").append(createSortOptionCard("Id", `id`));
    $("#sort-options").append(createSortOptionCard("Generation", `generation`));
    $("#sort-options").append(createSortOptionCard("Inbreeding Percentage", `inbreeding`));

    if (Herd["summary"]["NM$"])
        $("#sort-options").append(createSortOptionCard("NM$", `NM$`));


    let traits = Herd["summary"]["genotype"];
    for (let t in traits) {
        $("#sort-options").append(createSortOptionCard(`<${t}>`, `genotype,${t}`));
    }

    for (let t in traits) {
        $("#sort-options").append(createSortOptionCard(`ph: <${t}>`, `phenotype,${t}`));
    }
}

async function setUpHerd(classId, herdId) {
    await getHerd(classId, herdId);
    loadHerd(["id"], false, classId, herdId);
    showSummary();
    loadSortOptions();
    clearLoadingSymbol("herd");
    filterAll();
}

function createInfoCard(field, value) {
    let div = $("<div></div>");
    let span1 = $("<span></span>", { autofilter: true });
    span1.text(field);

    let span2 = $("<span></span>", { autofilter: true });
    span2.text(value);

    div.append(span1);
    div.append(span2);

    return div;
}

function showSummary() {
    $('#info-header').text("~");
    let info = $("#info");
    info.html("");

    info.append(createInfoCard("Name", Herd["name"]));

    if (Herd["summary"]["NM$"])
        info.append(createInfoCard("NM$", Herd["summary"]["NM$"]));

    for (let g in Herd["summary"]["genotype"]) {
        info.append(createInfoCard(`<${g}>`, Herd["summary"]["genotype"][g] * Filter[g]["standard_deviation"]));
    }

    for (let p in Herd["summary"]["phenotype"]) {
        let phenotype = Herd["summary"]["phenotype"][p] * Filter[p]["standard_deviation"] + Filter[p]["phenotype_average"];
        info.append(createInfoCard(`ph: <${p}>`, phenotype + Filter[p]["unit"]));
    }

    filterAll();
}

function animalSelected(animal, classId, herdId) {
    $('#info-header').text(animal["name"]);

    let info = $("#info");
    info.html("");
    if (animal["male"]) {
        let button = $("<button></button>", { class: ["pad", "as-btn", "background-green", "border-radius", "full-width"].join(" ") });
        let div = $("<div></div>", { class: "pad-small" });
        button.text("Save");
        button.click(() => {
            let cookie = "savedMales" + classId;
            let savedMales = getCookie(cookie);
            if (savedMales) {
                savedMales += "," + animal["id"];
                alert(`${animal["id"]} saved`);
            } else {
                savedMales = animal["id"];
                alert(`${animal["id"]} saved`);
            }
            setCookie("savedMales" + classId, savedMales, 10);
        });
        div.append(button);
        info.append(div);

        if (CurrentAssignmentStep && CurrentAssignmentStep["key"] == "msub") {
            let form = $("<form></form>", {
                class: "pad-small",
                action: `/class/${classId}/herd/${herdId}/assignments/submit-animal/${animal["id"]}`,
                method: "POST"
            });
            let button = $("<button></button>", {
                class: ["pad", "as-btn", "background-green", "border-radius", "full-width"].join(" "),
                type: "submit"
            });
            button.text("Submit to class herd");
            form.append($("<input></input>", { type: "hidden", name: "assignment", value: $("#assignment-select").val() }));
            form.append($("input[name=csrfmiddlewaretoken]").first());
            form.append(button);
            info.append(form);
        }
    } else {
        if (CurrentAssignmentStep && CurrentAssignmentStep["key"] == "fsub") {
            let form = $("<form></form>", {
                class: "pad-small",
                action: `/class/${classId}/herd/${herdId}/assignments/submit-animal/${animal["id"]}`,
                method: "POST"
            });
            let button = $("<button></button>", {
                class: ["pad", "as-btn", "background-green", "border-radius", "full-width"].join(" "),
                type: "submit"
            });
            button.text("Submit to class herd");
            form.append($("<input></input>", { type: "hidden", name: "assignment", value: $("#assignment-select").val() }));
            form.append($("input[name=csrfmiddlewaretoken]").first());
            form.append(button);
            info.append(form);
        }
    }

    info.append(createInfoCard("Id", animal["id"]));
    info.append(createInfoCard("Name", animal["name"]));
    info.append(createInfoCard("Generation", animal["generation"]));
    info.append(createInfoCard("Sire", animal["sire"] ? animal["sire"] : "N/A"));
    info.append(createInfoCard("Dam", animal["dam"] ? animal["dam"] : "N/A"));
    info.append(createInfoCard("Inbreeding Percentage", animal["inbreeding"] * 100 + "%"));

    if (animal["NM$"])
        info.append(createInfoCard("NM$", animal["NM$"]));

    for (let g in animal["genotype"]) {
        info.append(createInfoCard(`<${g}> `, animal["genotype"][g] * Filter[g]["standard_deviation"]));
    }

    if (!animal["male"]) {
        for (let p in animal["phenotype"]) {
            let phenotype = animal["phenotype"][p] * Filter[p]["standard_deviation"] + Filter[p]["phenotype_average"];
            info.append(createInfoCard(`ph: <${p}>`, phenotype + Filter[p]["unit"]));
        }
    }

    for (let r in animal["recessives"]) {
        info.append(
            createInfoCard(
                `<${r}>`,
                {
                    "he": "Heterozygous",
                    "ho(c)": "Homozygous Carrier",
                    "ho(f)": "Homozygous Free"
                }[animal["recessives"][r]]
            )
        );
    }

    filterAll();
}

function resortAnimals(classId, herdId) {
    let sortKey = $("#sort-options").val().split(",");
    let reversed = $("#sort-order").val() === "ascending";
    loadHerd(sortKey, reversed, classId, herdId);
    filterAll();
}

function loadAssignments() {
    let assignmentSelect = $("<select></select>", { id: "assignment-select" });

    if (Object.keys(Assignments).length == 0) {
        assignmentSelect.remove();
        return;
    }

    for (let assignment in Assignments) {
        assignment = Assignments[assignment];
        let option = $("<option></option>", { value: assignment["id"] });
        option.text(assignment["name"]);
        assignmentSelect.append(option);
    }
    assignmentSelect.change(() => showAssignment());

    $("#assignments").append(assignmentSelect);
    showAssignment();
}

function showAssignment() {
    $("#assignment-steps").remove();
    let assignmentSelected = $("#assignment-select").val();
    let stepsFulfilled = Assignments[assignmentSelected]["fulfillment"];

    if (!assignmentSelected)
        return;

    let div = $("<div></div>", {
        id: "assignment-steps",
        class: ["assignment-steps"].join(" ")
    });
    for (let stepIdx in Assignments[assignmentSelected]["steps"]) {
        step = Assignments[assignmentSelected]["steps"][stepIdx];
        let fulfilled = stepIdx < stepsFulfilled ? "complete" : "incomplete";
        let span = $("<span></span>", { class: ["pad-small", fulfilled, "step"].join(" ") });
        span.text(step["verbose"]);
        div.append(span);
    }

    let span = $("<span></span>", { class: ["pad-small", "status"].join(" ") });
    span.text(`${Assignments[assignmentSelected]["fulfillment"]}/${Assignments[assignmentSelected]["steps"].length} steps complete`);
    div.append(span);

    CurrentAssignmentStep = Assignments[assignmentSelected]["steps"][stepsFulfilled];
    if (CurrentAssignmentStep && CurrentAssignmentStep["key"] == "breed") {
        $("#breed-herd").removeClass("hide");
    } else {
        $("#breed-herd").addClass("hide");
    }

    $("#assignments").append(div);
    $("#id_assignment").val(assignmentSelected);
}

async function getAssignments(classId, herdId) {
    Assignments = await $.ajax({
        url: `/class/${classId}/herd/${herdId}/assignments/get`,
        dataType: "json",
    }).fail("Error: Could not load assignment data.");
}

async function setUpAssignments(classId, herdId) {
    await getAssignments(classId, herdId);
    loadAssignments();
}

function confirmBreedingSubmission() {
    if (!MalesValidatedForBreeding) {
        alert("Breeding selections are invalid.");
        return false;
    }

    if (!confirm("Are you sure you want to submit this breeding?"))
        return false;
    else
        $("#id_males").attr("disabled", false);
}

function createMaleCardForBreeding(classId, herdId, val) {
    let id = Math.round(Math.random() * Math.pow(10, 16));
    let div = $("<div></div>", { id: id, class: [].join(" ") });
    let input = $("<input></input>", { type: "number", min: "max" });
    input.on("input", () => updateMaleDataForBreeding(classId, herdId));
    input.val(val);
    let button = $(
        "<button></button>",
        {
            class: ["as-btn", "background-red", "pad", "border-radius"].join(" "),
            type: "button"
        }
    );
    button.text("Remove");
    button.click(() => {
        $(`#${id}`).remove();
        updateMaleDataForBreeding(classId, herdId);
    });

    div.append(input);
    div.append(button);
    return div;
}

function addMaleForBreeding(classId, herdId, val = null) {
    $("#malelist").append(createMaleCardForBreeding(classId, herdId, val));
    updateMaleDataForBreeding(classId, herdId);
}

function updateMaleDataForBreeding(classId, herdId) {
    let males = [];
    let inputs = $("#malelist input");
    inputs.each((e) => {
        males.push(parseInt(inputs[e].value));
    });

    $("#id_males").val(JSON.stringify(males));
    validateMalesForBreeding(classId, herdId);
}

async function validateMalesForBreeding(classId, herdId) {
    if (ValidatingMalesForBreeding) {
        RevalidateMalesForBreeding = true;
        return;
    }

    ValidatingMalesForBreeding = true;
    MalesValidatedForBreeding = false;

    let status = $("#malelist-validation-status");
    status.removeClass("background-red");
    status.removeClass("background-green");
    status.addClass("background-b");
    status.text("Validating...");

    let data = await $.ajax({
        url: `/class/${classId}/herd/${herdId}/breed/get-validation`,
        dataType: "JSON",
        data: { males: $("#id_males").val(), assignment: $("#id_assignment").val() },
        fail: () => { alert("Error: Could not validate breeding selections."); }
    });
    ValidatingMalesForBreeding = false;

    if (RevalidateMalesForBreeding) {
        RevalidateMalesForBreeding = false;
        validateMalesForBreeding(classId, herdId);
        return;
    }

    if (data["status"] === "pass") {
        status.removeClass("background-red");
        status.removeClass("background-b");
        status.addClass("background-green");
        MalesValidatedForBreeding = true;
        status.text("Valid");
    } else {
        status.addClass("background-red");
        status.removeClass("background-b");
        status.removeClass("background-green");
        MalesValidatedForBreeding = false;
        status.text("Invalid");
    }
}

function loadSavedMales(classId, herdId) {
    let cookie = "savedMales" + classId;
    let savedMales = getCookie(cookie);
    if (savedMales) {
        savedMales.split(",").forEach(e => {
            addMaleForBreeding(classId, herdId, e);
        });
    } else {
        alert("None saved");
    }
}

function clearSavedMales(classId) {
    setCookie("savedMales" + classId, "", 10);
    alert("Clear successful");
}