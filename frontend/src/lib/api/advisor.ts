"use client";

import { useMutation } from "@tanstack/react-query";
import { useApiClient } from "./client";

export type ChatResponse = {
  chat_id: string;
  message_id: string;
  response: string;
  tool_calls_made: string[];
  provider: string;
  tokens_used: number;
};

export function useSendMessage() {
  const api = useApiClient();
  return useMutation({
    mutationFn: (input: { message: string; chat_id?: string }) =>
      api.post<ChatResponse>("/advisor/chat", input),
  });
}

export function useFeedback() {
  const api = useApiClient();
  return useMutation({
    mutationFn: ({ messageId, rating }: { messageId: string; rating: -1 | 1 }) =>
      api.post<{ message: string }>(`/advisor/messages/${messageId}/feedback`, { rating }),
  });
}
