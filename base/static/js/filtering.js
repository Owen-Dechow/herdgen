function filterAll() {
    let query = $("*[autofilter]");
    query.each((idx) => {
        for (let key in Filter) {
            if (Filter.hasOwnProperty(key)) {
                let val = Filter[key];
                let elem = query[idx];

                if (typeof val === "string") {
                    elem.textContent = elem.textContent.replace(key, val);

                    let capKey = key.charAt(0).toUpperCase() + key.slice(1);
                    let capVal = val.charAt(0).toUpperCase() + val.slice(1);
                    elem.textContent = elem.textContent.replace(capKey, capVal);
                } else if (typeof val == "object") {
                    for (let key in val) {
                        if (val.hasOwnProperty(key)) {
                            elem.textContent = elem.textContent.replace(key, val[key]["abbreviation"]);
                        }
                    }
                }
            }
        }
    });
}
