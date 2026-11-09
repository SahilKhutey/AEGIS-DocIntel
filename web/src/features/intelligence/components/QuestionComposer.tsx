"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";

type Props = {
  onSubmit: (question: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  submitLabel?: string;
  placeholder?: string;
};

export function QuestionComposer({
  onSubmit,
  isLoading = false,
  disabled = false,
  submitLabel = "Ask AEGIS",
  placeholder = "Ask a question about your authorized documents...",
}: Props) {
  const [question, setQuestion] = useState("");

  function submit() {
    const value = question.trim();
    if (!value || isLoading || disabled) return;
    onSubmit(value);
    setQuestion("");
  }

  return (
    <form
      className="space-y-3"
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <div className="flex flex-col">
        <label
          htmlFor="aegis-question"
          className="block text-sm font-semibold text-gray-900 mb-1"
        >
          Your Question
        </label>
        <label htmlFor="aegis-question" className="sr-only">
          Ask AEGIS a question
        </label>
        <textarea
          id="aegis-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder={placeholder}
          disabled={disabled || isLoading}
          rows={3}
          className="w-full resize-y rounded-xl border border-gray-300 p-3 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
        />
      </div>

      <div className="flex justify-end">
        <Button
          type="submit"
          disabled={!question.trim() || disabled || isLoading}
          variant="primary"
          className="rounded-xl px-5 py-2.5 text-sm font-semibold"
        >
          {isLoading ? "Thinking..." : submitLabel}
        </Button>
      </div>
    </form>
  );
}
