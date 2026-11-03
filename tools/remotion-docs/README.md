# remotion-docs — генератор картинок «Как работает тестер»

Remotion-проект, рендерящий PNG-схемы в `docs/diagrams/` (см.
`docs/how-tester-works.md`). Работает от локального Chrome (headless-shell
не скачивается — настроено в `remotion.config.ts`).

## Состав

| Файл | Назначение |
|---|---|
| `src/diagrams.tsx` | 4 сцены: TesterPipeline, TesterPasswords, TesterBatches, TesterRegression |
| `src/style.tsx` | палитра, шрифт, компоненты Page/Card/Arrow/Pill/Ribbon |
| `src/Root.tsx` | регистрация композиций (1600×900, still) |
| `remotion.config.ts` | browser executable = локальный Chrome |

## Перегенерация

```bash
npm install            # один раз (~250 пакетов, node_modules в gitignore)
npx remotion still src/index.ts TesterPipeline ../../docs/diagrams/TesterPipeline.png
npx remotion still src/index.ts TesterPasswords ../../docs/diagrams/TesterPasswords.png
npx remotion still src/index.ts TesterBatches ../../docs/diagrams/TesterBatches.png
npx remotion still src/index.ts TesterRegression ../../docs/diagrams/TesterRegression.png
```

Или через npm-script: `npm run still -- <ID> <путь.png>`.

## Замечания по вёрстке

- Текст меток стрелок (`Arrow label`) держи коротким (≤7 симв.) или давай
  `width={72}`; длинные подписи обрезаются на канвасе 1600 px.
- Имена батчей в D3 не должны упираться в `text-overflow` — колонка
  фиксированной ширины 500 px.
- Кириллица рендерится корректно (Segoe UI); проверять глазами после
  каждой правки сцен.
