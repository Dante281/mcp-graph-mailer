import asyncio
import json
from fastmcp import Client

client = Client("http://localhost:8000/mcp")


async def main() -> None:
    async with client:
        # Step 1: Preview email
        print("📧 Step 1: Preview email...")
        preview_res = await client.call_tool(
            "preview_email",
            {
                "to": ["rubencalvo@outlook.com"],
                "subject": "test MCP via graph v0.1",
                "body": "mail va",
            },
        )

        print("Preview result:")
        print(json.dumps(preview_res.data, indent=2, ensure_ascii=False))

        if not preview_res.data.get("ok"):
            print("❌ Preview failed!")
            return

        # Step 2: Prepare email (create draft)
        print("\n📝 Step 2: Prepare email (create draft)...")
        prepare_res = await client.call_tool(
            "prepare_email",
            {
                "to": ["rubencalvo@outlook.com"],
                "subject": "test MCP via graph v0.1",
                "body": "mail va",
            },
        )

        print("Prepare result:")
        print(json.dumps(prepare_res.data, indent=2, ensure_ascii=False))

        draft_id = prepare_res.data.get("draft_id")
        if not draft_id:
            print("❌ Prepare failed!")
            return
        print(f"✅ Draft created: {draft_id}")

        # Step 3: Confirm and send
        print("\n🚀 Step 3: Confirm and send email...")
        confirm_res = await client.call_tool(
            "confirm_send",
            {
                "draft_id": draft_id,
            },
        )

        print("Send result:")
        print(json.dumps(confirm_res.data, indent=2, ensure_ascii=False))

        if confirm_res.data.get("ok"):
            print("\n✅ Email sent successfully!")
        else:
            print("\n❌ Send failed!")


if __name__ == "__main__":
    asyncio.run(main())
