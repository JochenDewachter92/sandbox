import { ChatKit, useChatKit } from "@openai/chatkit-react";

const API_BASE = "http://localhost:8001"; // FastAPI backend

function Chat() {
  const { control } = useChatKit({
    api: {
      // Simple mode: ChatKit calls this when it needs a client_secret.
      async getClientSecret(_existing) {
        // If you implement refresh logic, use `_existing` to check expiry.
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
        height: "100vh",
        width: "100vw",
        position: "fixed",
        top: 0,
        left: 0,
        overflow: "hidden",
      }}
    >
      <ChatKit control={control} className="h-full w-full" />
    </div>
  );
}

export default function App() {
  return <Chat />;
}
