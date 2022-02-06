CVS Система контроля версий
версия 2.0
Автор: Финогенов Всеволод (sevafinogenov@gmail.com)

ОПИСАНИЕ:
данное приложение является консольной реализацией локальной системы контроля версий

ТРЕБОВАНИЯ:
1) Python версии не ниже 3.6
2) библиотека chardet

СОСТАВ:
консольная версия: CVS.py
модули находятся в пакете CVSysModules,
тесты в tests

СПРАВКА ПО ЗАПУСКУ:
для создания системы контроля версий необходимо создать пустую директорию  
и запустить из нее CVS.py <Имя директории> init

использование: CVS.py [-h] [-s] DIRECTORY {init,pull,commit,state,discard,add,stash,merge} ...

позиционные аргументы:
  DIRECTORY             path to working directory
  {init,pull,commit,state,discard,add,stash,merge}
                       	список команд
    init                инициирует систему контроля версий
    pull                переход к коммиту
    commit              добавляет все изменения из списка add
    state               отображает информацию о системе контроля версий
    discard             отменяет изменения
    add                 добавляет изменения в список add
    stash               позволяет управлять стэшем
    merge               (в разработке) позволяет слить два коммита в один
опциональные аргументы:
  -h, --help            показывает инструкцию по использованию и завершает работу
  -s, --silent		если флаг поднят, то программа не будет писать в консоль

подробнее о каждой команде:
1) init:
 
  использование: CVS.py DIRECTORY init [-h] [-c]

  инициирует систему контроля версий

  опциональные аргументы:
    -h, --help   показывает справку
    -c, --clear  если используется, то init очистит перед инициацией DIRECTORY

2) pull:

  usage: CVS.py DIRECTORY pull [-h] [-i INDEX] [-n NAME] [-b] [-B]

  переходит к коммиту

  опциональные аргументы:
    -h, --help            показывает справку
    -i INDEX, --index INDEX
                       	переходит к коммиту по его индексу INDEX (индекс коммита - его порядковый номер при создании. 0 - корень дерева изменений)
    -n NAME, --name NAME  переходит к коммиту по его имени NAME
    -b, --back            переходит к предыдущему коммиту в дереве изменений
    -B, --backTime        перехдит к предыдущему коммиту, сделанному пользователем

3) commit:

  использование: CVS.py DIRECTORY commit [-h] [-n NAME]

  сохраняет все изменения из списка add

  optional arguments:
    -h, --help            показывает справку
    -n NAME, --name NAME  устонавливает имя коммита как NAME

4) state:
  
  использование: CVS.py DIRECTORY state [-h] [-a] [-f] [-t]

  показывает сокращенную информацию об изменениях

  optional arguments:
    -h, --help      показывает справку
    -a, --with_add  также выводит список add
    -f, --full      показывает полную информацию
    -t, --tree      показывает дерево изменений
  

5) add:

  использование: CVS.py DIRECTORY add [-h] [-i INDEX] [-n NAME] [-a]

  при использовании без аргументов показывает список add

  опциональные аргументы:
    -h, --help            показывает справку
    -i INDEX, --index INDEX
                        добавляет изменение в список по его индексу INDEX (индекс можно посмотреть, использовав комманду CVS.py DIRECTORY state)
    -n NAME, --name NAME  добавляет изменение по имени файла NAME
    -a, --all             добавляет все изменения

6) discard:

  использование: CVS.py DIRECTORY discard [-h] [-n] pointer

  отменяет изменение

  позиционные аргументы:
    pointer     по умолчанию - индекс отменяемого изменения (индекс можно посмотреть, использовав комманду CVS.py DIRECTORY state)

  опциональные аргументы:
    -h, --help  покаызвает справку
    -n, --name  вместо индекса в pointer должно быть передано им изменяемого файла

7) stash:

  usage: CVS.py DIRECTORY stash [-h] [-a PATH] [-d] [-e] [-r PATH_TO_SAVE [-c]]
                              [-n NAME] [-i]

  если используется без аргументов - показывает список сохраненных файлов

  optional arguments:
    -h, --help            показывает справку
    -a PATH, --add PATH   сохраняет файл по его пути PATH
    -d, --delete          удаляет файл из сохраненных

    -e, --empth           очищает список сохраненных файлов
    -r PATH_TO_SAVE, --restore PATH_TO_SAVE
                        восстанавливет записанный файл.
			если используется вместе с -d, то файл также будет удален из списка
			если используется вместе с -c, то файл PATH_TO_SAVE будет созданн, если он не существует 
    -n NAME, --name NAME  позволяет указать имя для сохранения
    -c, --create        если используется, то файл PATH_TO_SAVE будет созданн, если он не существует

    -i, --index         позволяет использовать индекс файла вместо его пути при исользовании --add PATH

8) merge

  использования: CVS.py DIRECTORY merge [-h] [-c] [-n NAME] [-r] [-f]

  склеивает коммиты в один

  опциональные аргументы:
    -h, --help            показывает справку
    -c, --conflicts       показывает список неразрешенных конфликтов
    -n NAME, --name NAME  склеивает текущий коммит с коммитом под именем NAME
    -r, --reversed        меняет приоритет с текущего коммита на склеиваемый с ним
    -f, --forget          при использовании все конфликты будут считаться решенными


примеры использования:

для начала необходимо инициировать систему контроля версий:

CVS.py foo init    - инициирует ее в директории foo

если использовать ключ -c, то foo будет предварительно очищена или создана (если ее не существовало)

после того как в foo сделаны какие-то изменения их список можно увидеть с помощью команды state:

CVS.py foo state   - выводит список изменений с индексами. Они могут пригодиться позже.
если использовать ключ -f, то команда выведет боле полные данные


сделанные изменения можно сохранить, это делается в два шага:
1. выбор сохраняемых изменений. Это делается с помощью команды add

CVS.py foo add -n foo\bar - сохраняет все изменения, связанные с foo\bar

CVS.py foo add -i 1 - сохраняет изменение под номером 1 из списка CVS.py foo state

СVS.py foo add -a - сохраняет все изменения

посмотерть сохраненные изменения можно с помощью команды CVS.py foo add или CVS.py foo state -a

ВАЖНО! В ДАННОЙ ВЕРСИИ ПРИЛОЖЕНИЯ НИКАК НЕЛЬЗЯ УДАЛИТЬ СОХРАНЕНИЕ ИЗ СПИСКА ADD

2. добавить сохраненные изменения в коммит

CVS.py foo commit

эта команда попросит ввести уникальное имя, под которым коммит будет сохранен. 
имя можно указать напрямую:

CVS.py foo commit -n <name>


перейти к любому коммиту под именем <name> можно с помощью команды

CVS.py foo pull -n <name>

CVS.py foo pull -i 2 - переход к коммиту, который был сделан вторым,
при этом если указать -i 0, то будет выполнен переход, к корню (пустой директории)

CVS.py foo pull -b  - переход к предыдущему элементу дерева коммитов

само дерево коммитов можно посмотреть с помощью команды

CVS.py foo state -t


изменения, не добавленные в список add, можно отменить с помощью команды discard:

CVS.py foo discard 1  - отменяет изменение под номером 1 из списка CVS.py foo state

CVS.py foo discard -n foo\bar  - отменяет все изменения связанные с foo/bar


кроме того, изменения в файлах можно сохранить в stash и использовать в любом коммите:

CVS.py foo stash -a foo\bar -n <name> - сохраняет текущее состояние файла под именем <name>, при этом
изменения в файле foo\bar будут отменены

ключ -n можно не использовать, тогда программа попросит ввести имя отдельно. Это применимо и к
другим вариантам запуска команды stash

посмотреть файлы в stash можно с помощью команды

CVS.py foo stash 

СVS.py foo stash -n <name> -r foo\baz - записывает состояние в файл foo\baz состояние файла, сохраненного под именем
<name>

при этом файл foo\baz должен существовать, а данные из него будут польностью заменены на данные из <name>

если использовать ключ -с, то foo\baz будет создан, если не существовал, а ключ -d удалит <name> из stash

удалить имя без записи в файл можно с помощью команды 

CVS.py foo stash -d -n <name>

а команда CVS.py foo stash -e полностью очистит список stash


два коммита можно склеить вместе с помощью команды merge

CVS.py foo merge -n <name>  -  эта команда склеивает изменения из текущего коммита с изменениями из 
коммита с именем <name>

использование ключа -r меняет приоритет склеивания (по умолчанию 
приоритетным считается текущий коммит)

при возникновении конфликтов их список можно увидеть с помощью команды

CVS.py foo merge -c

внутри файла конфликтные места помечаются символами >>>>, ====, <<<<
конфликт считается решенным, если была изменена структура этих символов

с помощью команды
 
CVS.py foo merge -f 
можно забыть все конфликты и оставить файлы как есть

после использывания команды merge изменения необходимо закоммитить
с помощью add и commit (смотри выше) как если бы это были изменения,
сделанные вручную пользователем


ПОДРОБНОСТИ РЕАЛИЗАЦИИ:
модули change_step.py, dir_change.py, file_change.py и single_change.py предоставляют
классы, для обработки и записи изменений. Модуль dif_controller.py позволяет сравнивать
две директории и на их основе создавать классы, описанные выше. Модули tree.py и 
storage_controller.py обеспечивают хранение всей информации об изменениях, а также
взаимодействия с ней. Модуль visualizer.py позволяет построить дерево изменений
и вывести его в консоль. CVS.py обеспечивает взаимодействие с пользователем.
тесты находятся в пакете tests и могут быть вызваны командой
pytest из директории с проектом. 

