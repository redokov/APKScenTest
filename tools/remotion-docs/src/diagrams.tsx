import React from 'react';
import {C, Card, Arrow, Page, Pill, Ribbon} from './style';

// D1. Принцип работы тестера: полный цикл в одной сессии 1С
export const TesterPipeline: React.FC = () => (
  <Page
    title="Как работает тестер: полный цикл"
    subtitle="Проверка идёт целиком в сеансе 1С: обработчик подготовки читает базу, составитель сценариев готовит проверки, исполнитель запускает их, отчёт показывается там же"
  >
    <div style={{display: 'flex', alignItems: 'stretch', justifyContent: 'center'}}>
      <Card
        chip="1"
        chipColor={C.teal}
        accent={C.teal}
        title="Документы в базе"
        width={326}
        bullets={[
          'Документы АПК: путевые листы, наряды, заправки, взвешивания',
          'Животноводство: свинотоварные фермы и молочный КРС',
          'Авторы документов — реальные пользователи базы',
        ]}
        note="Проверки ничего не выдумывают: они повторяют настоящие документы базы"
      />
      <Arrow label="чтение" width={72} />
      <Card
        chip="2"
        chipColor={C.blue}
        accent={C.blue}
        title="Подготовка данных"
        width={318}
        bullets={[
          'Обработчик сканирует подсистему АПК и находит документы',
          'Извлекает данные: организация, номенклатура, техника, ответственные',
          'Формирует проверки из шаблонов и дополнений',
        ]}
        note="Запуск всегда от администратора; типы без данных пропускаются с указанием причины"
      />
      <Arrow label="проверки" width={72} />
      <Card
        chip="3"
        chipColor={C.purple}
        accent={C.purple}
        title="Исполнение"
        width={326}
        bullets={[
          'Проверки делятся на группы по авторам документов',
          'Пароли авторов временно подменяются (настоящие пароли не нужны)',
          'Каждая группа выполняется под правами своего автора',
        ]}
        note="Отказная проверка: пользователь без прав получает ожидаемую ошибку"
      />
      <Arrow label="итоги" width={72} />
      <Card
        chip="4"
        chipColor={C.green}
        accent={C.green}
        title="Отчёт"
        width={326}
        bullets={[
          'Сводка: проверка × пользователь × результат (прошла / провалилась / отказ)',
          'Сравнение с эталоном: что сломалось после обновления',
          'Вердикт: ГОДЕН / НЕ ГОДЕН прямо в сеансе 1С',
        ]}
        note="Пароли возвращаются на место при любом исходе"
      />
    </div>
    <Ribbon
      items={[
        {text: 'Регресс = нет расхождений с эталоном', color: C.green},
        {text: 'Права авторов проверяются всерьёз', color: C.blue},
        {text: 'Комплект без python, COM и LLM', color: C.ink},
      ]}
    />
  </Page>
);

// D2. Механизм паролей: автор настоящий, пароль неизвестен
export const TesterPasswords: React.FC = () => (
  <Page
    title="Как тестер ходит под настоящими авторами, не зная их паролей"
    subtitle="Проверки выполняются под правами автора документа, но его пароль не хранится, не подбирается и не меняется"
  >
    <div style={{display: 'flex', justifyContent: 'center', alignItems: 'stretch'}}>
      <Card
        chip="Шаг 1"
        chipColor={C.amber}
        accent={C.amber}
        title="Хэш сохранён"
        width={352}
        bullets={[
          'У автора документа (например, ФедоровБМ) есть пароль, которого мы не знаем',
          'Тестер сохраняет служебное значение пароля — хэш платформы 8.5',
          'Настоящий пароль остаётся в базе — он нам и не нужен',
        ]}
      />
      <Arrow label="подмена" />
      <Card
        chip="Шаг 2"
        chipColor={C.blue}
        accent={C.blue}
        title="Временный пароль"
        width={352}
        bullets={[
          'На место хэша ставится временный пароль',
          'Тестер подключает окно проверки под именем автора',
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
          'Проверки идут ПОД ПРАВАМИ автора документа',
          'Роли и ограничения доступа действуют всерьёз',
          'Что автор не мог — тест подтвердит отказом',
        ]}
      />
      <Arrow label="возврат" />
      <Card
        chip="Шаг 4"
        chipColor={C.green}
        accent={C.green}
        title="Хэш возвращён"
        width={352}
        bullets={[
          'После прогона исходный хэш восстанавливается',
          'Проверка расхождений показывает: пароли не изменены',
          'Работает и при прерванной проверке',
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
        {text: 'Автор может провести документ — проверка проходит', color: C.green},
        {text: 'Нет прав — получаем ожидаемый отказ', color: C.red},
      ]}
    />
  </Page>
);

// D3. Групповой прогон и вердикт
export const TesterBatches: React.FC = () => (
  <Page
    title="Группы проверок и вердикт"
    subtitle="План проверок делится по авторам документов; каждая группа — отдельный сеанс Vanessa со своим кодом завершения"
  >
    <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 26}}>
      <Card
        chip="план"
        chipColor={C.teal}
        accent={C.teal}
        title="Проверки и данные"
        width={300}
        bullets={[
          '46 проверок (45 обычных + 1 отказная)',
          'Отбор по контурам: растениеводство, свинотоварные, КРС, АРМ',
          'Ключ сравнения: проверка + пользователь',
        ]}
      />
      <Arrow label="группы" width={72} />
      <div style={{display: 'flex', flexDirection: 'column', gap: 18}}>
        {[
          {u: 'СоколовМИ (админ)', p: 'порт 48501 · сеанс Vanessa', r: 'код 0 — годен', c: C.blue},
          {u: 'ФедоровБМ (животноводство)', p: 'порт 48502 · сеанс Vanessa', r: 'код 0 — годен', c: C.purple},
          {u: 'Негатив1 (нет прав)', p: 'порт 48503 · ожидаемый отказ', r: 'отказ = успех', c: C.red},
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
        title="Сводка и вердикт"
        width={300}
        bullets={[
          'Сводка: прошли / провалились / отказ',
          'Сверка с эталоном статусов (46 ключей)',
          'Итоговая панель и отчёт Allure',
        ]}
      />
    </div>
    <div style={{display: 'flex', justifyContent: 'center', marginTop: 38, gap: 24}}>
      <Pill big color={C.green} text="ГОДЕН: 45 прошло / 0 провалилось / 1 отказ" />
      <Pill big color={C.blue} text="расхождений с эталоном: 0" />
    </div>
  </Page>
);

// D4. Регресс-конвейер после обновления релиза
export const TesterRegression: React.FC = () => (
  <Page
    title="Регресс после обновления релиза"
    subtitle="Одна команда воспроизводит состояние «до/после»: запасная копия → обновление → прогон → сравнение → возврат"
  >
    <div style={{display: 'flex', alignItems: 'stretch', justifyContent: 'center'}}>
      <Card
        chip="Шаг 1"
        chipColor={C.teal}
        accent={C.teal}
        title="Запасная копия"
        width={268}
        bullets={['Выгрузка базы в файл dt (снимок до изменений)', 'Запрет регламентных заданий на время операции']}
      />
      <Arrow />
      <Card
        chip="Шаг 2"
        chipColor={C.amber}
        accent={C.amber}
        title="Обновление"
        width={268}
        bullets={['Загрузка cf/dt нового релиза', 'Обновление конфигурации базы']}
      />
      <Arrow />
      <Card
        chip="Шаг 3"
        chipColor={C.purple}
        accent={C.purple}
        title="Полный прогон"
        width={268}
        bullets={['Чтение базы → подготовка данных → исполнение групп', 'Вердикт и сводка']}
      />
      <Arrow />
      <Card
        chip="Шаг 4"
        chipColor={C.blue}
        accent={C.blue}
        title="Сравнение"
        width={268}
        bullets={['Сверка результатов с эталоном', 'Расхождение / пропущено / новое — виды отличий']}
      />
      <Arrow />
      <Card
        chip="Шаг 5"
        chipColor={C.green}
        accent={C.green}
        title="Возврат"
        width={268}
        bullets={['Восстановление базы из файла dt', 'База в исходном состоянии, отчёт готов']}
      />
    </div>
    <Ribbon
      items={[
        {text: 'Одна команда: скрипт --rehearsal / --update', color: C.ink},
        {text: 'Провалившаяся проверка → диагностика (исправление → повтор)', color: C.red},
      ]}
    />
    <div style={{display: 'flex', justifyContent: 'center', marginTop: 26}}>
      <Pill color={C.green} text="Код 0 = годен и без расхождений · Код 1 = есть сломанные · Код 2 = сбой окружения" />
    </div>
  </Page>
);
