var Herd;
var Assignments;
var CurrentAssignmentStep;
var RevalidateMalesForBreeding = false;
var ValidatingMalesForBreeding = false;
var MalesValidatedForBreeding = false;

const PTA_DECIMALS = 3;

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
    let key = sortKeyCp.shift();
    animal = animal[key];

    if (sortKeyCp.length == 0) {
        let val = animal;
        return val;
    }
    else {
        return resolveSortKey(sortKeyCp, animal);
    }

}

function compareValuesForSort(a, b) {
    if (typeof a === "string") {
        return a.localeCompare(b);
    } else {
        return Math.abs(a - b) / (a - b);
    }
}

function loadHerd(sortKey, reversed, contains, classId, herdId) {
    $("#males").html("");
    $("#females").html("");

    let animals = [];
    for (let animal in Herd["animals"]) {
        if (contains) {
            let name = Herd["animals"][animal]["name"];
            for (c of contains) {
                if (name.includes(c)) {
                    animals.push(Herd["animals"][animal]);
                }
                break;
            };
        } else {
            animals.push(Herd["animals"][animal]);
        }
    }

    let males = animals.filter(a => a.male);
    let females = animals.filter(a => !a.male);

    males.sort((a, b) => {
        a = resolveSortKey(sortKey, a);
        b = resolveSortKey(sortKey, b);
        let comp = compareValuesForSort(a, b);
        return comp;
    });

    females.sort((a, b) => {
        a = resolveSortKey(sortKey, a);
        b = resolveSortKey(sortKey, b);
        let comp = compareValuesForSort(a, b);
        return comp;
    });

    if (!reversed) {
        males.reverse();
        females.reverse();
    }

    males.forEach(animal => $("#males").append(createAnimalCard(animal["id"], animal["name"], animal, classId, herdId)));
    females.forEach(animal => $("#females").append(createAnimalCard(animal["id"], animal["name"], animal, classId, herdId)));
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
    $("#sort-options").append(createSortOptionCard(Filter["Sire"], `sire`));
    $("#sort-options").append(createSortOptionCard(Filter["Dam"], `dam`));

    if (Herd["summary"]["NM$"])
        $("#sort-options").append(createSortOptionCard("NM$", `NM$`));


    for (let t in Herd["summary"]["genotype"]) {
        $("#sort-options").append(createSortOptionCard(`${Filter["genotype_prefix"]}: <${t}>`, `genotype,${t}`));
    }

    for (let t in Herd["summary"]["phenotype"]) {
        $("#sort-options").append(createSortOptionCard(`(${Filter["dam"]}) ${Filter["phenotype_prefix"]}: <${t}>`, `phenotype,${t}`));
    }

    for (let t in Herd["summary"]["ptas"]) {
        $("#sort-options").append(createSortOptionCard(`${Filter["pta_prefix"]} <${t}> `, `ptas,${t}`));
    }

    let keys = Object.keys(Herd["animals"]);
    if (keys.length > 0) {
        let recessives = Herd["animals"][keys[0]]["recessives"];
        for (let r in recessives) {
            $("#sort-options").append(createSortOptionCard(`<${r}>`, `recessives,${r}`));
        }
    }
}

async function setUpHerd(classId, herdId) {
    await getHerd(classId, herdId);
    loadHerd(["id"], false, false, classId, herdId);
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

function formatInfoValue(value, decimals, prefix, suffix) {
    let pow = Math.pow(10, decimals);
    let roundedValue = Math.round(value * pow) / pow;
    return prefix + roundedValue + suffix;
}

function showSummary() {
    $('#info-header').text("~");
    let info = $("#info");
    info.html("");

    info.append(createInfoCard("Name", Herd["name"]));

    if (Herd["summary"]["NM$"])
        info.append(createInfoCard("NM$", formatInfoValue(Herd["summary"]["NM$"], 2, "$", "")));

    for (let g in Herd["summary"]["genotype"]) {
        info.append(
            createInfoCard(
                `${Filter["genotype_prefix"]}: <${g}>`,
                formatInfoValue(
                    Herd["summary"]["genotype"][g] * Filter[g]["standard_deviation"],
                    PTA_DECIMALS,
                    "",
                    Filter[g]["unit"]
                )
            )
        );
    }

    for (let p in Herd["summary"]["phenotype"]) {
        info.append(
            createInfoCard(
                `${Filter["phenotype_prefix"]}: <${p}>`,
                formatInfoValue(
                    Herd["summary"]["phenotype"][p] * Filter[p]["standard_deviation"] + Filter[p]["phenotype_average"],
                    PTA_DECIMALS,
                    "",
                    Filter[p]["unit"]
                )
            )
        );
    }

    for (let p in Herd["summary"]["ptas"]) {
        info.append(
            createInfoCard(
                `${Filter["pta_prefix"]}: <${p}>`,
                formatInfoValue(
                    Herd["summary"]["ptas"][p] * Filter[p]["standard_deviation"],
                    PTA_DECIMALS,
                    "",
                    Filter[p]["unit"]
                )
            )
        );
    }

    filterAll();
}

function createSubmitFormCard(animal, classId, herdId) {
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
    form.append($("input[name=csrfmiddlewaretoken]").first().clone());
    form.append(button);

    return form;
}

function animalSelected(animal, classId, herdId) {
    $('#info-header').text(animal["name"]);

    let info = $("#info");
    info.html("");

    let pedigreeBtn = $("<button></button>", { class: ["pad", "as-btn", "background-green", "border-radius", "full-width"].join(" ") });
    pedigreeBtn.text("Load Pedigree");
    pedigreeBtn.click(() => {
        showPedigree(classId, herdId, animal);
    });
    let pedigreeDiv = $("<div></div>", { class: "pad-small" });
    pedigreeDiv.append(pedigreeBtn);
    info.append(pedigreeDiv);

    if (animal["male"]) {
        let button = $("<button></button>", { class: ["pad", "as-btn", "background-green", "border-radius", "full-width"].join(" ") });
        let div = $("<div></div>", { class: "pad-small" });
        button.text("Save");
        button.click(() => {
            let cookie = "savedMales" + classId;
            let savedMales = getCookie(cookie);
            if (savedMales) {
                savedMales += "," + animal["id"];
                sendMessage(`${animal["id"]} saved`);
            } else {
                savedMales = animal["id"];
                sendMessage(`${animal["id"]} saved`);
            }
            setCookie("savedMales" + classId, savedMales, 10);
        });
        div.append(button);
        info.append(div);

        if (CurrentAssignmentStep && CurrentAssignmentStep["key"] == "msub") {
            let form = createSubmitFormCard(animal, classId, herdId);
            info.append(form);
        }
    } else {
        if (CurrentAssignmentStep && CurrentAssignmentStep["key"] == "fsub") {
            let form = createAnimalCard(animal, classId, herdId);
            info.append(form);
        }
    }

    info.append(createInfoCard("Id", animal["id"]));
    info.append(createInfoCard("Name", animal["name"]));
    info.append(createInfoCard("Generation", animal["generation"]));
    info.append(createInfoCard(Filter["Sire"], animal["sire"] ? animal["sire"] : "N/A"));
    info.append(createInfoCard(Filter["Dam"], animal["dam"] ? animal["dam"] : "N/A"));
    info.append(createInfoCard("Inbreeding Percentage", animal["inbreeding"] * 100 + "%"));

    if (animal["NM$"])
        info.append(createInfoCard("NM$", formatInfoValue(animal["NM$"], 2, "$", "")));

    for (let g in animal["genotype"]) {
        info.append(createInfoCard(`${Filter["genotype_prefix"]}: <${g}>`,
            formatInfoValue(
                animal["genotype"][g] * Filter[g]["standard_deviation"],
                PTA_DECIMALS,
                "",
                Filter[g]["unit"],
            )
        ));
    }

    for (let p in animal["phenotype"]) {
        info.append(createInfoCard(
            animal["male"]
                ? `${Filter["dam"]} ${Filter["phenotype_prefix"]}: <${p}>`
                : `${Filter["phenotype_prefix"]}: <${p}>`,
            animal["phenotype"][p] === null
                ? "~"
                : formatInfoValue(
                    animal["phenotype"][p] * Filter[p]["standard_deviation"] + Filter[p]["phenotype_average"],
                    PTA_DECIMALS,
                    "",
                    Filter[p]["unit"],
                )
        ));
    }

    for (let p in animal["ptas"]) {
        info.append(createInfoCard(`${Filter["pta_prefix"]}: <${p}>`,
            formatInfoValue(
                animal["ptas"][p] * Filter[p]["standard_deviation"],
                PTA_DECIMALS,
                "",
                Filter[p]["unit"],
            )
        ));
    }

    for (let r in animal["recessives"]) {
        info.append(
            createInfoCard(
                `<${r}>`,
                {
                    "he": "Carrier",
                    "ho(c)": "Positive",
                    "ho(f)": "Tested Free"
                }[animal["recessives"][r]]
            )
        );
    }

    filterAll();
}

function resortAnimals(classId, herdId) {
    let sortKey = $("#sort-options").val().split(",");
    let reversed = $("#sort-order").val() === "ascending";
    let contains = $("#contains").val().split(" ");
    loadHerd(sortKey, reversed, contains, classId, herdId);
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
        sendMessage("Breeding selections are invalid.", null, true);
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
        fail: () => { sendMessage("Error: Could not validate breeding selections.", null, true); }
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

async function showPedigree(classId, herdId, animal) {
    let data = await $.ajax({
        url: `/class/${classId}/herd/${herdId}/get-pedigree/${animal.id}`,
        dataType: "JSON",
        fail: () => { sendMessage("Error: Could not get pedigree.", null, true); }
    });

    let info = $("#info");
    let textArea = $("<pre></pre>");
    let div = $("<div></div>");
    div.css("font-weight", "bold");
    textArea.html(`Pedigree: ` + formatPedigreeData(data, animal.male ? "m" : "f", ""));

    div.append(textArea);
    info.append(div);
}

function formatPedigreeData(data, sex, pad) {
    let wrapA = (a) => `<span style="color: grey; font-weight: normal">${a}</span>`;

    let string = `${data.id} (${sex})`;

    let spad = pad + "├─";
    let dpad = pad + "└─";
    if (data.sire) {
        let npad = wrapA(pad + "│ ");
        string += wrapA("\n" + spad) + "sire: " + formatPedigreeData(data.sire, "m", npad);
    } else {
        string += wrapA("\n" + spad + "sire: N/A");
    }

    if (data.dam) {
        let npad = pad + "  ";
        string += wrapA("\n" + dpad) + "dam: " + formatPedigreeData(data.dam, "f", npad);
    } else {
        string += wrapA("\n" + dpad + "dam: N/A");
    }

    return string;
}

function loadSavedMales(classId, herdId) {
    let cookie = "savedMales" + classId;
    let savedMales = getCookie(cookie);
    if (savedMales) {
        savedMales.split(",").forEach(e => {
            addMaleForBreeding(classId, herdId, e);
        });
    } else {
        sendMessage("No saved breeding males.");
    }
}

function clearSavedMales(classId) {
    setCookie("savedMales" + classId, "", 10);
    sendMessage("Successfully cleared saved breeding males.");
}
