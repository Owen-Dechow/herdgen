function addOutOfEnrollmentTokensWarning() {
    let enrollmentTokens = $("#id_enrollment_tokens");

    if (enrollmentTokens.val() == 0) {
        sendMessage(
            "You can not accept any enrollment request "
            + "until you have more enrollment tokens. "
            + "Email herdgenetics@gmail.com with "
            + "your class code to get more tokens."
        );
    }
}
