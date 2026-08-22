"use client";

import { useRef } from "react";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";

type PhotoPickerProps = {
  name: string;
  preview: string | null;
  onChange: (file: File | null) => void;
};

export function PhotoPicker({ name, preview, onChange }: PhotoPickerProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="flex items-center gap-4 rounded-xl border border-dashed border-border bg-bg p-4">
      <Avatar name={name} src={preview} size="lg" />

      <div className="min-w-0">
        <p className="text-sm font-medium">Photo</p>
        <p className="mt-0.5 text-xs text-text-muted">PNG or JPG, up to 2 MB.</p>

        <div className="mt-2 flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => inputRef.current?.click()}
          >
            {preview ? "Change" : "Upload"}
          </Button>
          {preview && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                onChange(null);
                if (inputRef.current) inputRef.current.value = "";
              }}
            >
              Remove
            </Button>
          )}
        </div>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg"
        className="hidden"
        onChange={(event) => onChange(event.target.files?.[0] ?? null)}
      />
    </div>
  );
}
