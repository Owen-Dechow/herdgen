class LoadingSymbol extends HTMLElement {
    constructor() {
        super();
    }
}

customElements.define("loading-symbol", LoadingSymbol);

function clearLoadingSymbol(name) {
    $(`loading-symbol[name=${name}]`).remove();
}