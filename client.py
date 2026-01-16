import asyncio
import json
from fastmcp import Client

client = Client("http://localhost:8000/mcp")


async def main() -> None:
    async with client:
        greet_res = await client.call_tool("greet", {"name": "Ford"})
        print("greet:", greet_res.data)

        preview_res = await client.call_tool(
            "preview_email",
            {
                "to": ["ford@example.com"],
                "subject": "Prueba",
                "body": "Hola mundo",
            },
        )

        # preview_res.data suele ser el dict “limpio”
        print("preview_email (data):")
        print(json.dumps(preview_res.data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
