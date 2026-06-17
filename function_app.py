import logging
import azure.functions as func
import requests

from azure_table_storage.value import get_stored_value
from config import GRAPH_WEBHOOK_SECRET, SUBSCRIPTION_ROW_KEY
from core import process_notification
from microsoft_graph.authentication import get_graph_token
from microsoft_graph.webhook_subscriptions import renew_graph_subscription

app = func.FunctionApp()
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Azure Function 1 — graphWebhook (HTTP Trigger)
# ─────────────────────────────────────────────────────────────────────────────


@app.route(
    route="graphWebhook",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION,
)
def graph_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP-triggered function that receives all incoming events from the
    Microsoft Graph Change Notification subscription on info@nbif.ca.

    This function handles two distinct request types:

    Type 1 — Validation handshake
      When a new subscription is first registered (Step 7), Graph sends a POST
      with a `validationToken` query parameter. We must respond within 10 seconds
      with HTTP 200 and the token as plain text, otherwise the subscription
      registration fails.

    Type 2 — Change notifications
      For each new email that arrives in the inbox, Graph POSTs a JSON payload
      containing the message ID. We validate the clientState, then call
      process_notification() for each notification in the batch.

    Error strategy:
      - If a single notification fails, we log the error and continue processing
        the rest of the batch. We always return 200 to Graph so it does not
        flood us with retries for the entire batch due to one bad message.
      - If we cannot acquire a Graph token at all, we return 500 so Graph
        will retry the full batch.
    """

    # ── Type 1: Validation handshake ──────────────────────────────────────
    validation_token = req.params.get("validationToken")
    if validation_token:
        logger.info("Graph subscription validation handshake received — responding.")
        return func.HttpResponse(
            body=validation_token,
            status_code=200,
            mimetype="text/plain",
        )

    # ── Type 2: Change notifications ──────────────────────────────────────
    try:
        body = req.get_json()
    except ValueError:
        logger.error("Request body is not valid JSON.")
        return func.HttpResponse(status_code=400)

    notifications = body.get("value", [])
    if not notifications:
        # Empty payload — Graph sometimes sends keep-alive pings.
        return func.HttpResponse(status_code=200)

    # Acquire a Graph token once and reuse it for the entire batch.
    try:
        token = get_graph_token()
    except Exception as exc:
        logger.exception("Could not acquire Graph token: %s", exc)
        return func.HttpResponse(status_code=500)

    for notification in notifications:

        # Reject notifications that don't carry our expected clientState value.
        # This guards against spoofed requests to the function endpoint.
        if notification.get("clientState") != GRAPH_WEBHOOK_SECRET:
            logger.warning(
                "Notification rejected — clientState mismatch. "
                "Expected secret not received."
            )
            continue

        message_id = notification.get("resourceData", {}).get("id")
        if not message_id:
            logger.warning("Notification missing message ID — skipping.")
            continue

        try:
            process_notification(token, message_id)
        except requests.HTTPError as exc:
            logger.error(
                "HTTP error processing message %s: %s — %s",
                message_id,
                exc.response.status_code,
                exc.response.text,
            )
        except Exception as exc:
            logger.exception(
                "Unexpected error processing message %s: %s", message_id, exc
            )

    return func.HttpResponse(status_code=200)


# ─────────────────────────────────────────────────────────────────────────────
# Azure Function 2 — renewSubscription (Timer Trigger)
# ─────────────────────────────────────────────────────────────────────────────


@app.timer_trigger(
    schedule="0 0 0 */2 * *",  # midnight every 2 days (cron: s m h day-of-month month day-of-week)
    arg_name="timer",
    run_on_startup=False,
)
def renew_subscription(timer: func.TimerRequest) -> None:
    """
    Timer-triggered function that renews the Microsoft Graph webhook subscription
    every 2 days.

    Graph mail subscriptions have a maximum lifetime of 3 days. Running this
    renewal on a 2-day cycle gives a 1-day safety buffer — if a single renewal
    fails (e.g., a transient network error), there is still time for the next
    scheduled run or a manual retry before the subscription expires and
    notifications stop.

    The subscription ID is read from Table Storage.
    If the ID is missing (subscription not yet registered) or the subscription
    is not found on Graph (it already expired), a clear error is logged to
    Application Insights so the issue can be diagnosed and resolved quickly.
    """
    logger.info("renewSubscription timer fired.")

    # Retrieve the subscription ID written to Table Storage.
    subscription_id = get_stored_value(SUBSCRIPTION_ROW_KEY)
    if not subscription_id:
        logger.error(
            "No subscription ID found in Table Storage (row key: '%s'). "
            "Register the Graph subscription, then store "
            "the returned subscription ID.",
            SUBSCRIPTION_ROW_KEY,
        )
        return

    try:
        token = get_graph_token()
        new_expiry = renew_graph_subscription(token, subscription_id)
        logger.info(
            "Subscription %s successfully renewed. New expiry: %s",
            subscription_id,
            new_expiry,
        )
    except requests.HTTPError as exc:
        if exc.response.status_code == 404:
            logger.error(
                "Subscription %s not found on Graph — it has likely expired. "
                "Re-register the subscription, update the Table Storage "
                "row with the new subscription ID, and verify renewal is working.",
                subscription_id,
            )
        else:
            logger.exception(
                "HTTP error renewing subscription %s: %s",
                subscription_id,
                exc,
            )
    except Exception as exc:
        logger.exception(
            "Unexpected error renewing subscription %s: %s", subscription_id, exc
        )
