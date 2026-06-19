"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
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

export type ChatSummary = { chat_id: string; started_at: string; preview: string | null };
export type ChatMessage = { message_id: string; role: string; content: string; created_at: string };

export function useChatList() {
  const api = useApiClient();
  return useQuery({ queryKey: ["advisor", "chats"], queryFn: () => api.get<ChatSummary[]>("/advisor/chats") });
}

/** Returns a loader for a chat's messages (fetched on demand when one is opened). */
export function useChatLoader() {
  const api = useApiClient();
  return (chatId: string) => api.get<ChatMessage[]>(`/advisor/chats/${chatId}/messages`);
}

export function useFeedback() {
  const api = useApiClient();
  return useMutation({
    mutationFn: ({ messageId, rating }: { messageId: string; rating: -1 | 1 }) =>
      api.post<{ message: string }>(`/advisor/messages/${messageId}/feedback`, { rating }),
  });
}
