function filterAll() {
    let query = $("*[autofilter]");
    query.each((idx) => {
        for (let key in Filter) {
            if (Filter.hasOwnProperty(key)) {
                let val = Filter[key];
                let elem = query[idx];

                let search_key = "<" + key + ">";

                if (typeof val === "string") {
                    elem.textContent = elem.textContent.replace(search_key, val);
                } else if (typeof val == "object") {
                    elem.textContent = elem.textContent.replace(search_key, val["name"]);
                }
            }
        }
    });
}
