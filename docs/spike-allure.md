# Спайк: Allure-отчёт из VA (single 1.2.043)

Фича: `smoke-01-connect.feature`. База: `localhost\dev_erpapk_demo`. Вердикт: **PASS** (ReturnStatus-файл: 0; 84 c).

## Коды ReturnStatus (первичный вердикт)

0=ок · 1=ошибки сценариев · 2=проблемы подключения TestClient ·
3=нет сценариев · 4=не встала компонента.

## Структура allure-каталога (`КаталогВыгрузкиAllureБазовый`)

Всего файлов: 2. Примеры:
- spike-allure-01\5c167d2d-d684-44f4-bdce-43172cb4ce27-container.json
- spike-allure-01\5c167d2d-d684-44f4-bdce-43172cb4ce27-result.json

## Образец result-json

`spike-allure-01\5c167d2d-d684-44f4-bdce-43172cb4ce27-result.json`:

```json
{
	"uuid": "5c167d2d-d684-44f4-bdce-43172cb4ce27",
	"historyId": "Смоук подключения TestClient.(spike-allure-01) Подключение TestClient и закрытие окон",
	"name": "(spike-allure-01) Подключение TestClient и закрытие окон",
	"fullName": null,
	"testCaseId": null,
	"start": 1791727125629,
	"stop": 1791727151454,
	"statusDetails": {
		"known": false,
		"muted": false,
		"flaky": false
	},
	"status": "passed",
	"stage": "finished",
	"steps": [
		{
			"name": "Когда я закрываю все окна клиентского приложения",
			"start": 1791727150019,
			"stop": 1791727151453,
			"status": "passed",
			"stage": "finished",
			"statusDetails": {
				"known": false,
				"muted": false,
				"flaky": false
			},
			"parameters": [],
			"attachments": [],
			"steps": []
		}
	],
	"parameters": [],
	"labels": [
		{
			"name": "story",
			"value": "Подключение TestClient и закрытие окон"
		},
		{
			"name": "feature",
			"value": "Подключение TestClient и закрытие окон"
		},
		{
			"name": "package",
			"value": "features"
		},
		{
			"name": "host",
			"value": "DESKTOP-3PDA7V4"
		}
	],
	"links": [],
	"attachments": [],
	"description": null
}
```

## Лог 1С (хвост)

```
(пусто)
```