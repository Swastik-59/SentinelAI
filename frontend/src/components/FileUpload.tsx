"use client";

import { useCallback, useState, useRef } from "react";

interface FileUploadProps {
  accept: string;
  label: string;
  hint: string;
  icon: React.ReactNode;
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export default function FileUpload({
  accept,
  label,
  hint,
  icon,
  onFileSelected,
  disabled = false,
}: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      setFileName(file.name);
      onFileSelected(file);
    },
    [onFileSelected]
  );

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);
      if (e.dataTransfer.files?.[0]) {
        handleFile(e.dataTransfer.files[0]);
      }
    },
    [handleFile]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files?.[0]) {
        handleFile(e.target.files[0]);
      }
    },
    [handleFile]
  );

  return (
    <div
      className={`relative rounded-xl border-2 border-dashed transition-all duration-300 ${
        dragActive
          ? "border-sentinel-400 bg-sentinel-600/10"
          : fileName
          ? "border-emerald-500/30 bg-emerald-500/5"
          : "border-white/[0.08] hover:border-white/[0.12] hover:bg-white/[0.02]"
      } ${disabled ? "opacity-50 pointer-events-none" : "cursor-pointer"}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        className="hidden"
        disabled={disabled}
      />

      <div className="flex flex-col items-center gap-3 p-8">
        <div
          className={`flex h-12 w-12 items-center justify-center rounded-xl transition-colors ${
            fileName
              ? "bg-emerald-500/15 text-emerald-400"
              : "bg-white/[0.05] text-slate-500"
          }`}
        >
          {icon}
        </div>

        {fileName ? (
          <>
            <p className="text-sm font-medium text-emerald-400">{fileName}</p>
            <p className="text-xs text-slate-500">Click or drag to replace</p>
          </>
        ) : (
          <>
            <div>
              <p className="text-sm font-medium text-slate-300">{label}</p>
              <p className="mt-1 text-xs text-slate-600">{hint}</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
