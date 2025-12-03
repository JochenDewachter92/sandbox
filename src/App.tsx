import { ChatKit, useChatKit } from "@openai/chatkit-react";

const API_BASE = "http://localhost:8001"; // FastAPI backend

function Chat() {
  const { control } = useChatKit({
    api: {
      // Simple mode: ChatKit calls this when it needs a client_secret.
      async getClientSecret(existing) {
        // If you implement refresh logic, use `existing` to check expiry.
        const res = await fetch(`${API_BASE}/api/chatkit/session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });

        if (!res.ok) {
          throw new Error("Failed to create ChatKit session");
        }

        const data = await res.json();
        return data.client_secret as string;
      },
    },
    // Optional niceties:
    startScreen: {
      greeting: "Hoi! Ik ben je AI agent. Waarmee kan ik helpen?",
      prompts: [
        { label: "Leg het product uit", prompt: "Kun je het product kort uitleggen?" },
        { label: "Technische vraag", prompt: "Ik heb een technische vraag over de API." },
      ],
    },
    composer: {
      placeholder: "Typ je vraag...",
    },
  });

  return (
    <div
      style={{
        height: "600px",
        width: "400px",
        maxWidth: "100%",
        margin: "2rem auto",
        border: "1px solid #ddd",
        borderRadius: "12px",
        overflow: "hidden",
      }}
    >
      <ChatKit control={control} className="h-full w-full" />
    </div>
  );
}

export default function App() {
  return (
    <div>
      <h1 style={{ textAlign: "center", marginTop: "1.5rem" }}>
        ChatKit
      </h1>
      <Chat />
    </div>
  );
}
