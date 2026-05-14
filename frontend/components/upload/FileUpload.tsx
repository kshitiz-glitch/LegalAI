"use client";

import React, { useState, useCallback } from "react";
import { useDropzone, type FileRejection } from "react-dropzone";
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  X,
  Loader2,
} from "lucide-react";
import { cn, formatFileSize } from "@/lib/utils";

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>;
  disabled?: boolean;
  className?: string;
}

type UploadState = "idle" | "selected" | "uploading" | "success" | "error";

export const FileUpload = React.memo(function FileUpload({
  onUpload,
  disabled = false,
  className,
}: FileUploadProps) {
  const [state, setState] = useState<UploadState>("idle");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string>("");
  const [progress, setProgress] = useState(0);

  const onDrop = useCallback(
    (accepted: File[], rejected: FileRejection[]) => {
      if (rejected.length > 0) {
        setError(
          rejected[0].errors[0]?.message ?? "Invalid file. Please upload a PDF."
        );
        setState("error");
        return;
      }
      if (accepted.length > 0) {
        setSelectedFile(accepted[0]);
        setState("selected");
        setError("");
      }
    },
    []
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxSize: 10 * 1024 * 1024,
    maxFiles: 1,
    disabled: disabled || state === "uploading",
  });

  const handleUpload = useCallback(async () => {
    if (!selectedFile) return;
    setState("uploading");
    setProgress(0);

    // Simulate progress (actual upload is instant via fetch)
    const interval = setInterval(() => {
      setProgress((p) => {
        if (p >= 90) {
          clearInterval(interval);
          return 90;
        }
        return p + Math.random() * 15;
      });
    }, 200);

    try {
      await onUpload(selectedFile);
      clearInterval(interval);
      setProgress(100);
      setState("success");
      setTimeout(() => {
        setState("idle");
        setSelectedFile(null);
        setProgress(0);
      }, 2000);
    } catch (err) {
      clearInterval(interval);
      setError(err instanceof Error ? err.message : "Upload failed");
      setState("error");
      setProgress(0);
    }
  }, [selectedFile, onUpload]);

  const reset = useCallback(() => {
    setState("idle");
    setSelectedFile(null);
    setError("");
    setProgress(0);
  }, []);

  return (
    <div className={cn("w-full", className)}>
      {state === "idle" && (
        <div
          {...getRootProps()}
          className={cn(
            "group relative flex flex-col items-center justify-center gap-3",
            "rounded-xl border-2 border-dashed p-8 text-center",
            "transition-all duration-200 cursor-pointer",
            isDragActive
              ? "border-primary bg-primary/5 scale-[1.01]"
              : "border-border hover:border-primary/40 hover:bg-muted/50"
          )}
        >
          <input {...getInputProps()} />
          <div
            className={cn(
              "flex h-14 w-14 items-center justify-center rounded-xl transition-colors duration-200",
              isDragActive
                ? "bg-primary/10 text-primary"
                : "bg-muted text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary"
            )}
          >
            <Upload className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">
              {isDragActive ? "Drop your contract here" : "Drag & drop your contract"}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              PDF files up to 10MB
            </p>
          </div>
          <button
            type="button"
            className="mt-1 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
          >
            Browse files
          </button>
        </div>
      )}

      {(state === "selected" || state === "uploading") && selectedFile && (
        <div className="rounded-xl border border-border bg-card p-4 animate-scale-in">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <FileText className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-foreground">
                {selectedFile.name}
              </p>
              <p className="text-xs text-muted-foreground">
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
            {state === "selected" && (
              <button
                onClick={reset}
                className="shrink-0 rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            )}
            {state === "uploading" && (
              <Loader2 className="h-5 w-5 shrink-0 animate-spin text-primary" />
            )}
          </div>

          {/* Progress bar */}
          {state === "uploading" && (
            <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-primary transition-all duration-300 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          )}

          {state === "selected" && (
            <button
              onClick={handleUpload}
              className="mt-3 w-full rounded-lg bg-primary py-2.5 text-sm font-medium text-white transition-all duration-150 hover:bg-primary/90 hover:shadow-button-hover active:scale-[0.98]"
            >
              Analyze Contract
            </button>
          )}
        </div>
      )}

      {state === "success" && (
        <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 animate-scale-in">
          <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" />
          <p className="text-sm font-medium text-emerald-700">
            Contract uploaded! Analysis starting...
          </p>
        </div>
      )}

      {state === "error" && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 animate-scale-in">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
            <p className="text-sm font-medium text-red-700">{error}</p>
            <button
              onClick={reset}
              className="ml-auto shrink-0 text-sm font-medium text-red-600 hover:text-red-800 transition-colors"
            >
              Try again
            </button>
          </div>
        </div>
      )}
    </div>
  );
});
