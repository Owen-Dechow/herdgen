var ActiveMessages = 0;

function sendMessage(messageText, okCallBack, makeRed) {
    let message = $("<div></div>")
    message.css("--shadow", "#333")
    message.addClass("message")
    message.addClass("grid-auto-row")
    message.addClass(makeRed ? "background-red" : "background-green")
    message.addClass("full-width")
    message.addClass("pad-small")
    message.addClass("border-radius")
    message.addClass("center-text")
    message.addClass("box-shadow")
    message.css("top", `${ActiveMessages * 20}px`)

    let text = $("<p></p>")
    text.text(messageText)
    message.append(text)

    let ok = $("<button></button>")
    ok.text("Ok")
    ok.addClass("background-a");
    ok.addClass("as-btn")
    ok.addClass("pad-small")
    ok.addClass("border-radius")
    ok.click(() => {
        message.remove()
        ActiveMessages -= 1;

        if (okCallBack)
            okCallBack();

    })
    message.append(ok)

    $("body").append(message)
    ActiveMessages += 1;
}
