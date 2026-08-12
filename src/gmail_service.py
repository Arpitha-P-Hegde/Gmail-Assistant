from gmail_client import get_gmail_service


class GmailService:

    def __init__(self):
        self.service = get_gmail_service()

    def list_recent_messages(self, max_results=10):
        """
        Returns a list of recent Gmail message IDs.
        """
        response = (
            self.service.users()
            .messages()
            .list(
                userId="me",
                maxResults=max_results,
            )
            .execute()
        )

        return response.get("messages", [])

    def get_message(self, message_id):
        """
        Fetch metadata of a single message.
        """
        return (
            self.service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="metadata",
            )
            .execute()
        )

    @staticmethod
    def get_header(message, header_name):
        """
        Returns the requested email header.
        """
        headers = message["payload"]["headers"]

        for header in headers:
            if header["name"].lower() == header_name.lower():
                return header["value"]

        return ""