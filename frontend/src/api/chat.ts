export async function fetchStreamedResponse(
  message: string,
  onData: (chunk: string) => void
) {
  const response = await fetch(`${import.meta.env.VITE_API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!response.body) throw new Error("No response body");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let done = false;

  while (!done) {
    const { value, done: doneReading } = await reader.read();
    done = doneReading;

    // only decode if value is not undefined
    if (value) {
      const chunk = decoder.decode(value, { stream: true });
      onData(chunk);
    }
  }
}
