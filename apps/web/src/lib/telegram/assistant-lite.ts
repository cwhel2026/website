/** Lightweight OpenAI reply when FastAPI is not running on this container. */

export async function assistantLiteReply(question: string): Promise<string> {
  const key = process.env.OPENAI_API_KEY?.trim();
  if (!key) {
    return (
      "I received your message. Full business tools need the combined API deploy; " +
      "OPENAI_API_KEY on this service enables chat replies here."
    );
  }
  const model = process.env.OPENAI_MODEL?.trim() || "gpt-4o-mini";
  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model,
      messages: [
        {
          role: "system",
          content:
            "You are the private Revive My Drive business assistant for the owner. Be concise, UK English, practical.",
        },
        { role: "user", content: question },
      ],
      max_tokens: 600,
    }),
  });
  if (!res.ok) {
    return "I could not reach OpenAI right now. Try again in a minute.";
  }
  const data = (await res.json()) as {
    choices?: Array<{ message?: { content?: string } }>;
  };
  return data.choices?.[0]?.message?.content?.trim() || "No reply from assistant.";
}