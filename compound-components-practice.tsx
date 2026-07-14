// compound-components-practice.tsx
// ─────────────────────────────────────────────────────────────────────────────
// Практика compound-компонентів: <Accordion> з підтримкою controlled + uncontrolled.
//
// Майже все вже написано. Твоє завдання — реалізувати ЛОГІКУ ПЕРЕМИКАННЯ секцій
// у функції `useAccordionState` (позначено TODO). Це рішення з кількома валідними
// підходами: саме тут "живе" поведінка всього компонента.
// ─────────────────────────────────────────────────────────────────────────────

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useId,
  type ReactNode,
} from "react";

// ── 1. КОНТЕКСТ ──────────────────────────────────────────────────────────────
// Неявний спільний стан, який бачать усі під-компоненти. Споживач про нього
// не знає — він лише розставляє <Accordion.Item> у потрібному порядку.
type AccordionContextValue = {
  openItems: Set<string>;
  toggle: (value: string) => void;
};

const AccordionContext = createContext<AccordionContextValue | null>(null);

// Безпечний доступ: кидає ЗРОЗУМІЛУ помилку, якщо під-компонент застосували
// поза <Accordion>. Це стандартний захист compound-патерну — без нього була б
// незрозуміла "Cannot read properties of null".
function useAccordionContext(component: string): AccordionContextValue {
  const ctx = useContext(AccordionContext);
  if (!ctx) {
    throw new Error(
      `<Accordion.${component}> можна використовувати лише всередині <Accordion>`
    );
  }
  return ctx;
}

// ── 2. 🟢 ТВОЯ ЧАСТИНА: логіка стану ─────────────────────────────────────────
type UseAccordionStateArgs = {
  type: "single" | "multiple"; // скільки секцій можуть бути відкриті одночасно
  value?: string[]; // controlled: джерело правди ЗЗОВНІ
  defaultValue?: string[]; // uncontrolled: лише ПОЧАТКОВИЙ стан
  onValueChange?: (value: string[]) => void;
};

function useAccordionState(args: UseAccordionStateArgs): AccordionContextValue {
  const { type, value, defaultValue, onValueChange } = args;

  // controlled, якщо `value` передали ЯВНО (навіть порожній масив вважається
  // контролем; саме `undefined` означає "керуй собою сам").
  const isControlled = value !== undefined;
  const [internal, setInternal] = useState<string[]>(defaultValue ?? []);

  // У controlled-режимі показуємо зовнішній value, інакше — власний стан.
  const openItems = new Set(isControlled ? value : internal);

  const toggle = useCallback(
    (itemValue: string) => {
      setInternal((prev) => {
        // Джерело правди для обчислення: у controlled беремо зовнішній value.
        const current = isControlled ? value ?? [] : prev;

        // ───────────────────────────────────────────────────────────────────
        // TODO(ти): обчисли `next: string[]` — новий список відкритих секцій.
        //
        //   • Секція вже відкрита (current.includes(itemValue))?
        //       → клік має її ЗАКРИТИ.
        //   • Секція закрита?
        //       → type === "single"   : відкрита лишається ЛИШЕ вона ([itemValue]);
        //         type === "multiple" : додай її до вже відкритих.
        //
        // 4–6 рядків. Заміни рядок нижче на свою логіку.
        const next: string[] = current; // ← ЗАМІНИ ЦЕ

        onValueChange?.(next);
        // controlled: НЕ чіпаємо internal (батько сам оновить value через
        // onValueChange). uncontrolled: зберігаємо next у власний стан.
        return isControlled ? prev : next;
      });
    },
    [isControlled, value, type, onValueChange]
  );

  return { openItems, toggle };
}

// ── 3. КОРЕНЕВИЙ КОМПОНЕНТ ───────────────────────────────────────────────────
// Приймає конфіг поведінки, кладе стан у Provider, рендерить children як є.
type AccordionProps = UseAccordionStateArgs & { children: ReactNode };

export function Accordion({ children, ...stateArgs }: AccordionProps) {
  const state = useAccordionState(stateArgs);
  return (
    <AccordionContext.Provider value={state}>
      <div className="accordion">{children}</div>
    </AccordionContext.Provider>
  );
}

// ── 4. ПІД-КОМПОНЕНТИ ────────────────────────────────────────────────────────
// Кожен читає спільний стан з контексту. Прив'язуємо їх як статичні властивості
// (Accordion.Item) — звідси читабельний API <Accordion.Item> у розмітці.

// Локальний контекст для одного Item — щоб Trigger і Content знали свій value
// та id (для aria-controls), не отримуючи їх пропсами вручну.
const ItemContext = createContext<{ value: string; contentId: string } | null>(
  null
);

function AccordionItem({ value, children }: { value: string; children: ReactNode }) {
  const contentId = useId();
  return (
    <ItemContext.Provider value={{ value, contentId }}>
      <div className="accordion-item">{children}</div>
    </ItemContext.Provider>
  );
}

function AccordionTrigger({ children }: { children: ReactNode }) {
  const { openItems, toggle } = useAccordionContext("Trigger");
  const item = useContext(ItemContext)!;
  const isOpen = openItems.has(item.value);
  return (
    <button
      className="accordion-trigger"
      aria-expanded={isOpen}
      aria-controls={item.contentId}
      onClick={() => toggle(item.value)}
    >
      {children}
      <span aria-hidden>{isOpen ? "▲" : "▼"}</span>
    </button>
  );
}

function AccordionContent({ children }: { children: ReactNode }) {
  const { openItems } = useAccordionContext("Content");
  const item = useContext(ItemContext)!;
  if (!openItems.has(item.value)) return null;
  return (
    <div id={item.contentId} className="accordion-content" role="region">
      {children}
    </div>
  );
}

Accordion.Item = AccordionItem;
Accordion.Trigger = AccordionTrigger;
Accordion.Content = AccordionContent;

// ── 5. ЯК ЦЕ ВИКОРИСТОВУВАТИ (для перевірки) ─────────────────────────────────
export function Demo() {
  return (
    <Accordion type="single" defaultValue={["faq-1"]}>
      <Accordion.Item value="faq-1">
        <Accordion.Trigger>Що таке compound-компонент?</Accordion.Trigger>
        <Accordion.Content>Набір компонентів зі спільним неявним станом.</Accordion.Content>
      </Accordion.Item>
      <Accordion.Item value="faq-2">
        <Accordion.Trigger>Навіщо Context?</Accordion.Trigger>
        <Accordion.Content>Щоб уникнути prop drilling між частинами.</Accordion.Content>
      </Accordion.Item>
    </Accordion>
  );
}
