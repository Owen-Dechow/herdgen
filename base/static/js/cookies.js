function setCookie(cookieName, cookieValue, expirationDays) {
    const d = new Date();
    d.setTime(d.getTime() + (expirationDays * 24 * 60 * 60 * 1000));
    let expires = "expires=" + d.toUTCString();
    document.cookie = cookieName + "=" + cookieValue + ";" + expires + ";path=/";
}

function getCookie(cookieName) {
    let name = cookieName + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
}

$(window).on("load", () => {
    const CookieName = "acceptedcookies";
    const CookieExpiration = 10;
    const CookieValue = "true"
    if (getCookie(CookieName) != CookieValue) {
        sendMessage(
            "This website uses cookies for authentication and animal caching. "
            + 'Herd Genetics can not run without these cookies. By selecting "Ok" '
            + "and using this website you are accepting these cookies. No cookie "
            + "will be shared outside of Herd Genetics or with third parties.",
            () => {setCookie(CookieName, CookieValue, CookieExpiration)}
        )
    }
})
