package com.amdi.os.exceptions;

public class AmdiException extends RuntimeException {
    private final int statusCode;
    private final String responseBody;

    public AmdiException(String message) {
        super(message);
        this.statusCode = 0;
        this.responseBody = "";
    }

    public AmdiException(String message, int statusCode, String responseBody) {
        super(message);
        this.statusCode = statusCode;
        this.responseBody = responseBody;
    }

    public int getStatusCode() {
        return statusCode;
    }

    public String getResponseBody() {
        return responseBody;
    }
}
