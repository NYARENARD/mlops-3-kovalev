# Отчёт: версионирование данных с DVC и ClearML

Дата выполнения: 2026-10-24.

## Статус выполнения

DVC-часть выполнена, включая feature-ветки, слияние, отправку объектов в remote и восстановление в чистом clone. ClearML-часть не выполнена: на машине отсутствуют `~/.clearml.conf` и переменные `CLEARML_API_HOST`, `CLEARML_WEB_HOST`, `CLEARML_FILES_HOST`. SDK установлен и закреплён, но без настройки сервера нельзя создать Dataset или подтвердить lineage. IDs ниже не выдуманы.

В исходном Git-репозитории не настроен удалённый Git URL; выполненная история доступна в локальном репозитории `mlops-3-kovalev`.

## Окружение

| Компонент | Версия |
|---|---|
| Python | 3.12.7 |
| DVC | 3.67.1 |
| ClearML | 2.1.12 |
| scikit-learn | 1.9.1 |
| pandas | 3.0.6 |
| NumPy | 2.5.3 |

Версии зависимостей закреплены в `pyproject.toml` и `poetry.lock`.

## DVC

Использован локальный DVC remote вне репозитория: `../mlops-3-kovalev-dvc-remote` (на этой машине: `C:\CodeMonkey\5 sem\mlops\3\mlops-3-kovalev-dvc-remote`). Конфигурация remote не содержит credentials и сохранена в `.dvc/config`. Merge driver задан локальной Git-конфигурацией, атрибут `*.dvc merge=dvc` сохранён в `.gitattributes`.

| Версия | Git commit | Состояние |
|---|---|---|
| `data-v1` | `05a6506db9f8270709362973471fee17b2d8f3f3` | Iris, 150 строк, 5 столбцов |
| `feature/wine` | `d0d3f2702191776946828362b076ee98e6a95c9f` | Iris без изменений и Wine, 178 строк, 14 столбцов |
| `feature/iris-features` | `50d93b0375c9cfcac08d086b6a29851d35b98e9d` | Iris с `sepal_area`, `petal_area` |
| Слияние веток; итоговый `main` | `a263f467871e1c84df70d0b1f388e7cd9d5cb4dd` | Iris с вычисляемыми столбцами и Wine |

Финальный SHA-256 `data.dvc`: `96dfda4219f2457ea0fdce7cb7d69cb89dd0e55680d6be9b639f3f5624c1aefb`.

| Итоговый файл | Форма | Столбцы | Пропуски | SHA-256 |
|---|---:|---:|---:|---|
| `data/iris.csv` | 150 × 7 | исходные 5, `sepal_area`, `petal_area` | 0 | `3e1ba63f55da2aabc432d00b1670140f5162bf9ef34b837598ec2fc176c9ff26` |
| `data/wine.csv` | 178 × 14 | исходные признаки Wine и `target` | 0 | `38860ba04ace4d402242340bcf40be4bd6f4ebde9144a3dc89dc12c20f7f8e60` |

Базовый `iris.csv` имел SHA-256 `6d700503c9c2e2c71d187b889a87af8a8d3a6dd5bae1266d46f4ee4db5a6349f`; этот хэш не изменился в `feature/wine`. Генератор сортирует строки по всем столбцам и использует единые параметры CSV (`index=False`, `lineterminator="\\n"`, `float_format="%.10g"`). Повторная генерация base дала идентичный SHA-256.

`dvc status` чистый на итоговом `main`. После Git merge потребовался `dvc checkout`: он применил объединённый `data.dvc` к workspace. Затем `dvc push` завершился успешно.

Чистый clone создан в `mlops-3-kovalev-clean-clone` без копирования workspace и cache. `dvc pull` получил 3 объекта из remote и восстановил оба CSV с теми же хэшами; `check_data.py --state merged` прошёл.

Git-файлы отслеживают исходный код, зависимости и DVC-метаданные. Сами CSV не находятся в Git; `git ls-files data` не вывел файлов.

## ClearML

| Поле | Результат |
|---|---|
| Project | `MIIT/MLOps/practice_3/Kovalev` (требуется использовать после настройки сервера) |
| Dataset name | `sklearn-tabular-Kovalev` (требуется использовать после настройки сервера) |
| `BASE_ID` | Не создан: нет конфигурации ClearML server |
| `WINE_ID` | Не создан: нет конфигурации ClearML server |
| `IRIS_FEATURES_ID` | Не создан: нет конфигурации ClearML server |
| Parent IDs, dependency graph и списки файлов | Не получены |
| Скачанные копии и SHA-256 ClearML versions | Не получены |

Создание, скачивание и сравнение ClearML versions остаётся незавершённым и требует локальной авторизации ClearML. Credentials и конфигурация пользователя в репозиторий не добавлялись.

## Сравнение по наблюдениям

| Свойство | DVC | ClearML Dataset |
|---|---|---|
| Идентификатор версии | Git commit вместе с хэшем `data.dvc`; для базы создан tag `data-v1` | Dataset ID не получен, сервер не настроен |
| Расположение метаданных | `data.dvc` в Git; итоговый файл имеет указанный выше SHA-256 | Не наблюдалось |
| Расположение содержимого | DVC remote вне репозитория; CSV восстановлены через `dvc pull` | Не наблюдалось |
| Создание дочернего состояния | Новая Git-ветка, повторный `dvc add data`, коммит `data.dvc` | Не проверено; по теории задаётся `parent_datasets` |
| Переключение | `git switch`, затем `dvc checkout`; проверено удаление Wine на `main` | Не проверено; получение должно выполняться по Dataset ID |
| Восстановление на чистой машине | Чистый clone и `dvc pull` восстановили точные хэши | Не проверено |
| Ветвление | Git-ветки `feature/wine` и `feature/iris-features` созданы от общей базы | Не проверено |
| Слияние | Настроенный DVC merge driver объединил разные изменения; после merge применён `dvc checkout` | Не проверено |
| Связь с Git | Метаданные версии входят в Git history | Не проверено на сервере; Dataset ID отделён от Git commit в модели ClearML |
| UI | Использован локальный DVC remote, отдельный UI не проверялся | Web UI не проверялся |

## Ответы на вопросы

1. Версию данных DVC однозначно задаёт состояние DVC-метаданных (`data.dvc`) в конкретном Git commit; файл указывает на содержимое по хэшу.
2. Git хранит DVC-метаданные, но не сами CSV. Без remote новый clone не сможет получить содержимое, если нужных объектов нет в локальном cache.
3. Dataset version — человекочитаемая метка вроде `1.1.0`; Dataset ID — уникальный идентификатор конкретного объекта версии на ClearML server.
4. `finalize()` закрывает текущий Dataset и делает его неизменяемым. Следующую версию создают отдельным Dataset с нужным parent.
5. Нужно проверить `parent_datasets`/dependency graph версии `2.0.0` и убедиться, что единственный parent — `BASE_ID`, а `WINE_ID` не является её предком. На этом запуске проверка не выполнена, поскольку сервер не настроен.
6. `git switch` меняет DVC-метаданные в Git, но не гарантирует синхронизацию файлов workspace. Без `dvc checkout` останутся данные предыдущей ветки; это наблюдалось до checkout при слиянии.
7. В выполненном сценарии DVC удобен для версий, привязанных к Git-веткам и локального восстановления через remote. ClearML Dataset подходит для независимых Dataset IDs, lineage и доступа через сервер/UI, но эта часть требует настроенного ClearML server и здесь не проверена.