# WhatsApp Business Cloud API

This adapter adds a guarded outbound channel; it does not bypass WhatsApp's
business messaging rules or send anything automatically at installation time.

## The only manual setup needed next

Open the official Meta setup: https://developers.facebook.com/docs/whatsapp/cloud-api/get-started/

In Meta for Developers, create/select an app, add the WhatsApp product, and follow the Cloud API getting-started flow. Use Meta's test sender first if offered; a production sender can be configured after the test path works.

When Meta shows the WhatsApp API setup panel, the two values needed for integration are:
- **Phone Number ID** (an identifier, not the phone number itself)
- **Access token** (secret — never paste it into ChatGPT, GitHub issues, or source code)

Keep the token in a private runtime secret store or an untracked local environment file. A temporary setup token may expire; before production, use Meta's supported production-token setup. The Graph API version must be a currently supported version for the app.

Once you've reached that panel, the smallest useful thing to send back here is just: **“Meta setup ready”** plus the non-secret **Phone Number ID**. Do not send the token. I can then finish wiring the configuration instructions around the actual sender setup. The integration stays disabled until the PR's security checks pass, it is reviewed/merged, the private runtime config is installed, and the approved message template is ready.

## One-time provider setup

1. Configure the WhatsApp product in Meta for Developers and add a WhatsApp
   Business sender number.
2. Obtain an access token and the sender's phone-number ID from Meta. Store the
   token only in a runtime secret manager or an untracked local environment.
3. Set the Graph API version supported by your Meta app explicitly.
4. Create and obtain approval for a WhatsApp message template for business-
   initiated updates. Free-form text is only allowed inside the recipient's
   active 24-hour customer-service window.
5. Record each recipient's explicit WhatsApp opt-in before adding their number
   to the opt-in list. Knowing a phone number is not consent.

## Runtime configuration

Set these in the private runtime environment, never in tracked source files:

- WHATSAPP_ACCESS_TOKEN — secret access token.
- WHATSAPP_PHONE_NUMBER_ID — sender phone number ID from Meta.
- WHATSAPP_GRAPH_API_VERSION — explicit supported version, e.g. v24.0.
- WHATSAPP_ALLOWED_RECIPIENTS — comma-separated E.164 numbers approved by the
  operator for this system.
- WHATSAPP_OPTED_IN_RECIPIENTS — comma-separated E.164 numbers with recorded
  WhatsApp opt-in.

Both recipient lists must include a number before sending. The adapter fails
closed if configuration, allowlisting, or opt-in is missing. It does not log
authorization headers and does not retry failed sends, avoiding accidental
duplicates.

## Use

Within a 24-hour customer-service window:

    from messaging.whatsapp_cloud import send_text
    send_text("+972547385735", "Your update here")

For an outbound message that starts a conversation, use an approved template:

    from messaging.whatsapp_cloud import send_template
    send_template("+972547385735", "project_update", "en_US")

Template names and language codes must match templates approved in Meta.
A successful return means the provider accepted the message, not that it was
delivered or read. Track delivery webhooks separately before reporting delivery.

## Tests

    python -m unittest tests.test_whatsapp_cloud -v

No real provider request is made by the tests.
