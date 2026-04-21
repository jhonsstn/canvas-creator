import { useEffect, useRef, useState } from "react";

export interface SelectOption<T> {
  value: T;
  label: string;
}

interface Props<T> {
  value: T;
  options: SelectOption<T>[];
  onChange: (value: T) => void;
  disabled?: boolean;
  ariaLabel?: string;
}

export default function Select<T extends string | number | null>({
  value,
  options,
  onChange,
  disabled,
  ariaLabel,
}: Props<T>) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(() =>
    Math.max(0, options.findIndex((o) => o.value === value))
  );
  const rootRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const current = options.find((o) => o.value === value) ?? options[0];

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [open]);

  useEffect(() => {
    if (open) {
      setActive(Math.max(0, options.findIndex((o) => o.value === value)));
    }
  }, [open, options, value]);

  useEffect(() => {
    if (!open) return;
    const el = listRef.current?.children[active] as HTMLElement | undefined;
    el?.scrollIntoView({ block: "nearest" });
  }, [open, active]);

  const commit = (idx: number) => {
    onChange(options[idx].value);
    setOpen(false);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (!open) setOpen(true);
      else commit(active);
    } else if (e.key === "Escape") {
      setOpen(false);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!open) setOpen(true);
      else setActive((i) => Math.min(options.length - 1, i + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (!open) setOpen(true);
      else setActive((i) => Math.max(0, i - 1));
    } else if (e.key === "Home") {
      e.preventDefault();
      setActive(0);
    } else if (e.key === "End") {
      e.preventDefault();
      setActive(options.length - 1);
    }
  };

  return (
    <div
      ref={rootRef}
      className={`select${open ? " open" : ""}${disabled ? " disabled" : ""}`}
    >
      <button
        type="button"
        className="select-trigger"
        onClick={() => !disabled && setOpen((o) => !o)}
        onKeyDown={onKeyDown}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
      >
        <span className="select-value">{current?.label}</span>
        <span className="select-caret" aria-hidden="true">
          ▾
        </span>
      </button>
      {open && (
        <ul
          ref={listRef}
          className="select-list"
          role="listbox"
          tabIndex={-1}
        >
          {options.map((opt, i) => (
            <li
              key={String(opt.value)}
              role="option"
              aria-selected={opt.value === value}
              className={`select-option${i === active ? " active" : ""}${
                opt.value === value ? " selected" : ""
              }`}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => {
                e.preventDefault();
                commit(i);
              }}
            >
              <span className="select-option-label">{opt.label}</span>
              {opt.value === value && (
                <span className="select-check" aria-hidden="true">
                  ·
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
