# NBIF General Inquiries Integration

This project is an Azure Function App that monitors the `info@nbif.ca` inbox using Microsoft Graph webhooks. It processes incoming emails—including website form submissions—and automatically creates and populates corresponding list entries in Affinity CRM.

## Technologies Used

* **Language:** Python 3
* **Compute:** Azure Functions (v2 Programming Model)
* **Storage:** Azure Table Storage (`azure-data-tables`)
* **APIs:** * Microsoft Graph API (for email retrieval and webhook subscriptions)
  * Affinity API (for CRM data entry)
* **Authentication:** Azure Identity (`ClientSecretCredential` for Microsoft Graph), HTTP Basic Auth (Affinity API)
* **HTTP Client:** `requests`

## Workflow: How Data Travels

1. **Email Arrival:** A new email arrives in the monitored inbox. This can be a direct email or a forwarded submission from the website form.
2. **Webhook Notification:** Microsoft Graph sends a JSON payload to the Azure Function's HTTP Trigger (`graphWebhook`). This payload contains the `message_id` but not the email content.
3. **Data Retrieval:** The Azure Function authenticates with Microsoft Azure Active Directory and uses the `message_id` to fetch the full email metadata and body from the Microsoft Graph API.
4. **Parsing & Source Detection:** * The function checks the email subject against a configured form prefix. 
   * If it is a website form submission, it uses regular expressions to extract the submitter's Name, Email, and Message from the email body. 
   * If it is a direct email, it uses the sender's email address and the raw email body.
5. **Deduplication Check:** The function queries Azure Table Storage using the email's `conversationId`. If a record exists, the email is identified as a reply to an existing thread (or a webhook retry) and processing halts.
6. **Affinity CRM Sync:**
   * **Person Resolution:** The function queries Affinity for an existing Person using the sender's email address. If no match is found, a new Person record is created.
   * **List Entry Creation:** The Person is added to the specified "General Inquiries" list.
   * **Field Population:** Custom fields on the list entry are updated via `PUT` requests. These fields include the Message, Date Received, Source (Website Form vs. Direct Email), Thread ID, and an initial "New" Status.
7. **State Persistence:** Upon successful CRM entry, the `conversationId` is written to Azure Table Storage to ensure future replies in the same email thread do not create duplicate entries.

## Automated Maintenance

Microsoft Graph mail subscriptions expire after 3 days. This application includes a Timer Trigger Function (`renew_subscription`) scheduled to run at midnight every 2 days. It reads the active `graph_subscription_id` from Azure Table Storage and sends a `PATCH` request to Microsoft Graph to extend the expiration date, ensuring uninterrupted operation.

## Project Structure

* `function_app.py`: Contains the Azure Function routing and trigger definitions.
* `core.py`: Orchestrates the main data processing and syncing logic.
* `microsoft_graph/`: Modules for Azure AD authentication, email fetching/parsing, and webhook renewal.
* `affinity/`: Modules for querying and updating Affinity CRM records and list fields.
* `azure_table_storage/`: Modules for handling idempotent processing logs and subscription state.
* `config.py`: Loads environment variables and maps required configuration IDs.
* `tools/`: A suite of standalone scripts used for initial setup, including registering the initial webhook subscription (`register_subscription.py`) and identifying specific Affinity field IDs.