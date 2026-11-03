import React from 'react';
import {C, Card, Arrow, Page, Pill, Ribbon, W} from './style';

// D1. Принцип работы тестера: полный цикл в одной сессии 1С
export const TesterPipeline: React.FC = () => (
  <Page
    title="Как работает тестер: полный цикл"
    subtitle="Прогон идёт целиком в сеансе 1С — препроцессор готовит данные, раннер гоняет сценарии, отчёт показывается тут же"
  >
    <div style={{display: 'flex', alignItems: 'stretch', justifyContent: 'center'}}>
      <Card
        chip="1"
        chipColor={C.teal}
        accent={C.teal}
        title="Данные в базе"
        width={326}
        bullets={[
          'Документы АПК: путевые листы, наряды, заправки, взвешивания',
          'Животноводство: СВН (опоросы, падёж) и КРС (надой, отёлы, ТТН)',
          'Авторы документов — реальные пользователи базы',
        ]}
        note="Тесты ничего не выдумывают: сценарии повторяют реальные документы базы"
      />
      <Arrow label="скан" width={72} />
      <Card
        chip="2"
        chipColor={C.blue}
        accent={C.blue}
        title="Препроцессор"
        width={318}
        bullets={[
          'Сканирует подсистему АПК и находит документы',
          'Извлекает фикстуры: организация, номенклатура, техника, ответственные',
          'Генерирует .feature из шаблонов + scenario-patches',
        ]}
        note="Запуск всегда от администратора; пропускает типы без данных (skip с причиной)"
      />
      <Arrow label="фичи" width={72} />
      <Card
        chip="3"
        chipColor={C.purple}
        accent={C.purple}
        title="Раннер"
        width={326}
        bullets={[
          'Разбивает план на батчи по пользователям-авторам',
          'Подменяет хэши паролей тестовыми (пароли не знаем!)',
          'Гоняет сценарии Vanessa в TestClient под правами автора',
        ]}
        note="Отказной сценарий: neg-пользователь без прав получает ожидаемую ошибку"
      />
      <Arrow label="итоги" width={72} />
      <Card
        chip="4"
        chipColor={C.green}
        accent={C.green}
        title="Отчёт"
        width={326}
        bullets={[
          'Сводка: сценарий × пользователь × статус (passed/failed/neg)',
          'Сравнение с baseline: что сломалось после обновления',
          'Вердикт: PASS / FAIL прямо в сессии 1С',
        ]}
        note="Пароли восстанавливаются в любом исходе (mismatch = [])"
      />
    </div>
    <Ribbon
      items={[
        {text: 'Регресс = 0 регрессий vs baseline', color: C.green},
        {text: 'Авторские права проверяются честно (RLS/права)', color: C.blue},
        {text: 'Комплект без python / COM / LLM', color: C.ink},
      ]}
    />
  </Page>
);

// D2. Механизм паролей: тесты идут под автором, пароль неизвестен
export const TesterPasswords: React.FC = () => (
  <Page
    title="Секрет живого прогонa: пароль неизвестен, права — настоящие"
    subtitle="Сценарии выполняются под правами автора документа, но его пароль не хранится, не подбирается и не меняется"
  >
    <div style={{display: 'flex', justifyContent: 'center', alignItems: 'stretch'}}>
      <Card
        chip="Шаг 1"
        chipColor={C.amber}
        accent={C.amber}
        title="Хэш спасён"
        width={352}
        bullets={[
          'У автора документа (напр. ФедоровБМ) есть неизвестный нам пароль',
          'Гейт сохраняет СохраняемоеЗначениеПароля (хэш платформы 8.5)',
          'Исходный пароль остаётся в базе — он нам и не нужен',
        ]}
      />
      <Arrow label="подмена" />
      <Card
        chip="Шаг 2"
        chipColor={C.blue}
        accent={C.blue}
        title="Тестовый пароль"
        width={352}
        bullets={[
          'На место хэша ставится тестовый пароль (1 канал настройки)',
          'Vanessa подключает TestClient под именем автора',
          'Никаких «запасных» пользователей с полными правами',
        ]}
      />
      <Arrow label="прогон" />
      <Card
        chip="Шаг 3"
        chipColor={C.purple}
        accent={C.purple}
        title="Настоящие права"
        width={352}
        bullets={[
          'Сценарии выполняются ПОД ПРАВАМИ автора документа',
          'RLS/роли/права реально ограничивают доступ',
          'Что автор не мог — тест подтвердит отказом',
        ]}
      />
      <Arrow label="закрытие" />
      <Card
        chip="Шаг 4"
        chipColor={C.green}
        accent={C.green}
        title="Хэш возвращён"
        width={352}
        bullets={[
          'После прогона исходный хэш восстанавливается',
          'Проверка mismatch=[] — пароли не изменены',
          'Работает и в отказных ветках (прогон прерван)',
        ]}
      />
    </div>
    <div style={{display: 'flex', justifyContent: 'center', marginTop: 36}}>
      <Pill
        big
        color={C.ink}
        text="Пароль пользователя не известен, не меняется и не покидает базу"
      />
    </div>
    <Ribbon
      items={[
        {text: 'Позитив: автор может провести документ', color: C.green},
        {text: 'Негатив: без прав — ожидаемая ошибка (neg-сценарий)', color: C.red},
      ]}
    />
  </Page>
);

// D3. Батчевый прогон и вердикт
export const TesterBatches: React.FC = () => (
  <Page
    title="Батчевый прогон и вердикт"
    subtitle="План сценариев разбивается по пользователям-авторам; каждый батч — отдельный сеанс Vanessa со своим ReturnStatus"
  >
    <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 26}}>
      <Card
        chip="план"
        chipColor={C.teal}
        accent={C.teal}
        title="Сценарии + фикстуры"
        width={300}
        bullets={[
          '46 сценариев (45 позитив + 1 neg)',
          'Контур-фильтр: растениеводство, СВН, КРС, АРМ',
          'Ключ базы сравнения: сценарий + пользователь',
        ]}
      />
      <Arrow label="батчи" width={72} />
      <div style={{display: 'flex', flexDirection: 'column', gap: 18}}>
        {[
          {u: 'СоколовМИ (админ)', p: 'порт 48501 · Vanessa single', r: 'ReturnStatus=0', c: C.blue},
          {u: 'ФедоровБМ (животноводство)', p: 'порт 48502 · Vanessa single', r: 'ReturnStatus=0', c: C.purple},
          {u: 'Негатив1 (нет прав)', p: 'порт 48503 · ожидаемая ошибка', r: 'neg = успех', c: C.red},
        ].map((b) => (
          <div
            key={b.u}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              background: C.card,
              border: `2px solid ${C.border}`,
              borderLeft: `10px solid ${b.c}`,
              borderRadius: 14,
              padding: '12px 18px',
              width: 500,
              boxShadow: '0 8px 20px rgba(15,23,42,0.10)',
            }}
          >
            <div style={{flex: 1}}>
              <div style={{fontSize: 22, fontWeight: 700}}>{b.u}</div>
              <div style={{fontSize: 17, color: C.muted, marginTop: 2}}>{b.p}</div>
            </div>
            <Pill text={b.r} color={b.c} />
          </div>
        ))}
      </div>
      <Arrow label="итоги" width={72} />
      <Card
        chip="свод"
        chipColor={C.green}
        accent={C.green}
        title="summary + вердикт"
        width={300}
        bullets={[
          'summary.json: totals passed / failed / neg',
          'Сверка с baseline-real.json (46 ключей)',
          'Вердикт-панель и Allure-отчёт',
        ]}
      />
    </div>
    <div style={{display: 'flex', justifyContent: 'center', marginTop: 38, gap: 24}}>
      <Pill big color={C.green} text="PASS 45 / 0 / neg-1" />
      <Pill big color={C.blue} text="регрессий 0 vs baseline" />
    </div>
  </Page>
);

// D4. Регресс-конвейер после обновления релиза
export const TesterRegression: React.FC = () => (
  <Page
    title="Регресс после обновления релиза"
    subtitle="One-command воспроизведение «до/после»: бэкап → обновление → прогон → откат → отчёт"
  >
    <div style={{display: 'flex', alignItems: 'stretch', justifyContent: 'center'}}>
      <Card
        chip="Шаг 1"
        chipColor={C.teal}
        accent={C.teal}
        title="Бэкап"
        width={268}
        bullets={['Выгрузка ИБ в dt-файл (архив до изменений)', 'Запрет регл. заданий на время операции']}
      />
      <Arrow />
      <Card
        chip="Шаг 2"
        chipColor={C.amber}
        accent={C.amber}
        title="Обновление"
        width={268}
        bullets={['Загрузка cf/dt нового релиза', 'Обновление конфигурации БД']}
      />
      <Arrow />
      <Card
        chip="Шаг 3"
        chipColor={C.purple}
        accent={C.purple}
        title="E2E-гейт"
        width={268}
        bullets={['Полный конвейер: скан → генерация → прогон', 'Вердикт + summary.json']}
      />
      <Arrow />
      <Card
        chip="Шаг 4"
        chipColor={C.blue}
        accent={C.blue}
        title="Сравнение"
        width={268}
        bullets={['Сверка статусов с baseline', 'REGRESSION / MISSING / NEW — классы диффа']}
      />
      <Arrow />
      <Card
        chip="Шаг 5"
        chipColor={C.green}
        accent={C.green}
        title="Откат"
        width={268}
        bullets={['Восстановление ИБ из dt', 'База в исходном состоянии, отчёт готов']}
      />
    </div>
    <Ribbon
      items={[
        {text: 'Одна команда: regress_run.py --rehearsal / --update', color: C.ink},
        {text: 'Красный сценарий → диагностическая петля (фиксы → перепрогон)', color: C.red},
      ]}
    />
    <div style={{display: 'flex', justifyContent: 'center', marginTop: 26}}>
      <Pill color={C.green} text="Exit 0 = зелёный и без регрессий · Exit 1 = есть сломанные · Exit 2 = инфраструктурный сбой" />
    </div>
  </Page>
);
