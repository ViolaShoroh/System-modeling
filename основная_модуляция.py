import numpy as np
from collections import deque

# Константы
WORK_STATIONS = 3  # Количество рабочих станций
CYCLE_TIME = 30  # Время обслуживания одной рабочей станции (в секундах)
SIMULATION_TIME = 18000  # Время симуляции (5 часов в секундах)
PROCESSING_SPEED = 10  # Скорость обработки заданий (знаков/с)

TASK_LENGTH_MEAN = 300  # Средняя длина задания (знаков)
TASK_LENGTH_VARIANCE = 50  # Отклонение длины задания (знаков)

ARRIVAL_INTERVAL_MEAN = 30  # Среднее время между поступлением заявок (секунд)
ARRIVAL_INTERVAL_VARIANCE = 5  # Отклонение времени поступления заявок (секунд)


def format_time(seconds):
    hours = round(seconds // 3600)
    minutes = round((seconds % 3600) // 60)
    seconds = round(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class Task:
    count = 0
    max_length = 0  # поле для хранения максимальной длины задачи

    def __init__(self, length, creation_time, station, task_id=None):
        self.length = round(length)  # Изначальная длина задачи
        self.creation_time = creation_time  # Время создания задачи
        self.remaining_length = round(length)  # Оставшаяся длина задачи
        self.start_time = None  # Время начала обработки
        self.end_time = None  # Время завершения обработки
        self.id = task_id  # Уникальный идентификатор задачи
        self.station = station  # Ссылка на станцию
        self.waiting_time = 0  # Время ожидания в очереди

        if task_id is None:
            Task.count += 1
            self.id = Task.count
            print(f"Задача №{self.id} в {format_time(creation_time)} на {self.remaining_length} знаков в очереди станции {self.station.id + 1}")
        
        if self.length > Task.max_length:
            Task.max_length = self.length
            
    # Обработка
    def process(self, time): 
        start_time = time

        # Рассчет оставшееся время для обработки
        remaining_time = max(0, self.remaining_length / PROCESSING_SPEED)

        # Успевает ли задача завершиться в текущий цикл
        if remaining_time <= CYCLE_TIME:
            processed = self.remaining_length
            self.remaining_length = 0
            end_time = start_time + (processed / PROCESSING_SPEED)
        else:
            processed = min(CYCLE_TIME * PROCESSING_SPEED, self.remaining_length)
            self.remaining_length -= processed
            end_time = start_time + (processed / PROCESSING_SPEED)

        # Возвращение оставшихся символов в очередь
        if self.remaining_length > 0:
            self.waiting_time = end_time - self.creation_time
            end_time = start_time + (processed / PROCESSING_SPEED)
            self.station.incomplete_tasks.append(self)
        
        return processed, end_time


class Station:
    def __init__(self, id):
        self.id = id  # Идентификатор станции
        self.queue = deque()  # Очередь
        self.current_task = None  # Наличие активной задачи
        self.time = 0  # Инициализация времени станции
        self.last_cycle_end_time = 0  # Время последнего завершения цикла
        self.next_arrival_time = self.generate_next_arrival_time()  # Время следующей задачи
        self.incomplete_tasks = deque()  # Очередь незавершенных задач для данной станции
        self.total_waiting_time = 0 #общее временя ожидания задач в очереди
        self.total_tasks_in_queue = 0 #общее кол-ва задач, которые находились в очереди на станции
        self.task_count = 0 #счетчик для общего числа задач
        self.next_arrival_time = 0 #сброс времени поступления
        self.processed_tasks = [] #список для хранения информации о обработанных задачах
        self.total_queue_length = 0 #длина всех задач
        self.queue_cycle_count = 0 #счетчик циклов, во время которых очередь была не пустой

    def generate_next_arrival_time(self):
        #Генерация следующего времени прибытия задачи
        interval = np.clip(np.random.normal(ARRIVAL_INTERVAL_MEAN, ARRIVAL_INTERVAL_VARIANCE),
                           ARRIVAL_INTERVAL_MEAN - ARRIVAL_INTERVAL_VARIANCE,
                           ARRIVAL_INTERVAL_MEAN + ARRIVAL_INTERVAL_VARIANCE)
        self.next_arrival_time = self.time + interval
        return self.next_arrival_time

    def create_new_task(self, current_time):
        #Создание новой задачи и добавление её в очередь
        task_length = np.clip(round(np.random.normal(TASK_LENGTH_MEAN, TASK_LENGTH_VARIANCE)), TASK_LENGTH_MEAN - TASK_LENGTH_VARIANCE, TASK_LENGTH_MEAN + TASK_LENGTH_VARIANCE)
        new_task = Task(task_length, current_time, self, task_id=None)
        self.queue.append(new_task)

    def process_task(self, central_computer, current_time):
        task = self.get_next_task()
        end_time = current_time  # Начинаем с текущего времени

        if task is not None:
            if end_time < SIMULATION_TIME:
                processed_chars, end_time = task.process(end_time)
                central_computer.total_processed_chars += processed_chars
                central_computer.busy_time += (processed_chars / PROCESSING_SPEED)
                #Вид списка хранения данных
                task_data = {
                    'id': task.id,
                    'start_time': task.start_time,
                    'end_time': task.end_time,
                    'initial_length': task.remaining_length,
                    'processed_length': task.length - task.remaining_length,
                    'waiting_time': task.waiting_time
                    }
                
                self.processed_tasks.append(task_data)
                self.task_count += 1  
                self.total_waiting_time += task.waiting_time
                
                if round(task.remaining_length) == 0:
                    print(f"В {format_time(end_time)} со станции {self.id + 1} обработано {processed_chars} знаков.")
                    central_computer.completed_tasks += 1
                else:
                    print(f"В {format_time(end_time)} со станции {self.id + 1} обработано {processed_chars} знаков. Осталось {round(task.remaining_length)} знаков.")
                    central_computer.incomplete_tasks.append(task)

                # Обработка задач из очереди незавершенных задач, если остался цикл
                remaining_cycle_time = CYCLE_TIME - (end_time - current_time)
                while remaining_cycle_time > 0 and central_computer.incomplete_tasks:
                    incomplete_task = central_computer.incomplete_tasks.popleft()
                    # Проверяем, сколько символов можно обработать за оставшееся время
                    max_processable_chars = remaining_cycle_time * PROCESSING_SPEED
                    processed_chars_incomplete = min(max_processable_chars, incomplete_task.remaining_length)

                    # Обработка задачи
                    incomplete_task.remaining_length -= processed_chars_incomplete
                    central_computer.total_processed_chars += processed_chars_incomplete
                    central_computer.busy_time += (processed_chars_incomplete / PROCESSING_SPEED)

                    # Обновление времени окончания обработки
                    end_time += (processed_chars_incomplete / PROCESSING_SPEED)
    
                    if round(incomplete_task.remaining_length) == 0:
                        print(f"В {format_time(end_time)} со станции {self.id + 1} обработано {round(processed_chars_incomplete)} знаков из спец. очереди.")
                        central_computer.completed_tasks += 1
                        self.processed_tasks.append(incomplete_task.id)
                    else:
                        print(f"В {format_time(end_time)} со станции {self.id + 1} обработано {round(processed_chars_incomplete)} знаков из спец. очереди. Осталось {round(incomplete_task.remaining_length)} знаков.")
                        # Если задача не завершена, добавляем ее обратно в очередь незавершенных задач
                        incomplete_task.waiting_time = end_time - incomplete_task.creation_time
                        central_computer.incomplete_tasks.append(incomplete_task)

                    # Обновляем оставшееся время цикла
                    remaining_cycle_time -= (processed_chars_incomplete / PROCESSING_SPEED)
                        
                # Расчет среднего времени ожидания и среднего количества задач в очереди
                avg_waiting_time = 0
                avg_tasks_in_queue = 0

                if self.queue:
                    avg_waiting_time = sum(task.waiting_time for task in self.queue) / len(self.queue)
                    avg_tasks_in_queue = len(self.queue)


    def calculate_average_waiting_time(self, cycle_count):
        return self.total_waiting_time / cycle_count if cycle_count > 0 else 0

    def calculate_average_tasks(self, cycle_count):
        return self.task_count / cycle_count if cycle_count > 0 else 0

    def calculate_average_tasks_in_queue(self, cycle_count):
        return self.total_queue_length / cycle_count if cycle_count > 0 else 0

    def update_queue_stats(self, current_time):
          self.total_queue_length += len(self.queue)
          self.queue_cycle_count += 1

    def get_next_task(self):
        if self.queue:
            return self.queue.popleft()
        else:
            return None

class CentralComputer:
    def __init__(self):
        self.stations = [Station(i) for i in range(WORK_STATIONS)]
        self.incomplete_tasks = deque()  # Очередь незавершенных задач
        self.total_processed_chars = 0 #общее количество символов, которые были обработаны всеми станциями
        self.busy_time = 0 #время, в течение которого система была занята обработкой задач
        self.completed_tasks = 0 #счётчик завершённых задач
        self.simulation_time = 0  #отслеживание времени симуляции
        self.cycle_count = 0  # Для подсчета количества циклов
        self.cycle_tasks = []  # Список для хранения данных о задачах, обрабатываемых в каждом цикле

    def simulate(self):
        current_time = 0
        while current_time <= SIMULATION_TIME:
            tasks_to_process = []  # Временный список для хранения задач, готовых к обработке
            
            for station in self.stations:
                if current_time >= station.next_arrival_time:
                    station.create_new_task(current_time)
                    station.next_arrival_time = station.generate_next_arrival_time()
                tasks_to_process.extend(station.queue)
                station.process_task(self, current_time)
                station.update_queue_stats(current_time)

            # Добавляем все задачи, которые должны быть обработаны в этот цикл
            self.cycle_tasks.append([])
            for task in tasks_to_process:
                self.cycle_tasks[-1].append({
                    'id': task.id,
                    'station': task.station.id,
                    'creation_time': task.creation_time,
                    'remaining_length': task.remaining_length,
                    'waiting_time': task.waiting_time
                })

            # Обновляем время последнего завершения цикла
            for station in self.stations:
                station.last_cycle_end_time = current_time
            
            self.cycle_count += 1  # Увеличиваем счетчик циклов
            current_time += CYCLE_TIME
            self.simulation_time = current_time
        
        self.print_results()


    def calculate_average_tasks_per_cycle(self):
        if not self.cycle_tasks:
            return 0  
        total_tasks = 0
        for cycle in self.cycle_tasks:
            tasks_in_cycle = len(cycle)
            total_tasks += tasks_in_cycle
        
        average_tasks_per_cycle = total_tasks / len(self.cycle_tasks)
        return average_tasks_per_cycle

    def calculate_queue_statistics(self):
        total_waiting_time = 0
        total_tasks_in_queue = 0
        total_incomplete_length = sum(task.remaining_length for task in self.incomplete_tasks)
        # Статистика для каждой станции
        station_statistics = {}
        
        # Вычисление среднего времени ожидания для незавершенных задач
        for task in self.incomplete_tasks:
            if task.start_time is not None:
                waiting_time = task.start_time - task.creation_time
                total_waiting_time += waiting_time

        # Вычисление среднего времени ожидания
        avg_waiting_time = total_waiting_time / len(self.incomplete_tasks) if self.incomplete_tasks else 0
        
        # Статистика для специальной очереди
        special_queue_avg_waiting_time = total_waiting_time / len(self.incomplete_tasks) if self.incomplete_tasks else 0
        special_queue_avg_tasks_in_queue = len(self.incomplete_tasks) if self.incomplete_tasks else 0

        # Возвращаем полную статистику
        return {
            "average_waiting_time": avg_waiting_time,
            "total_incomplete_length": total_incomplete_length,
            "station_statistics": station_statistics,
            "special_queue_avg_waiting_time": special_queue_avg_waiting_time,
            "special_queue_avg_tasks_in_queue": special_queue_avg_tasks_in_queue
        }

    def calculate_average_waiting_time_and_tasks(self):
        average_waiting_times = []
        average_task_counts = []
        
        for task in self.processed_tasks:
            if isinstance(task, dict) and 'waiting_time' in task and 'processed_length' in task:
                #количество задач
                task_count = 1
                
                #средняя длина задачи
                avg_task_size = task['processed_length']
                
                #среднее количество задач остается прежним
                avg_task_count = task_count
                
                #среднее время ожидания
                waiting_times = [task['waiting_time']]
                avg_waiting_time = sum(waiting_times) / len(waiting_times)
                
                average_waiting_times.append(avg_waiting_time)
                average_task_counts.append(avg_task_count)
            else:
                #если ни одна из задач не имеет нужных ключей, то они - нулевые
                average_waiting_times.append(0)
                average_task_counts.append(0)
        return average_waiting_times, average_task_counts

    def calculate_average_waiting_time(self):
        total_waiting_time = 0
        total_tasks_in_queue = 0
        num_cycles = len(self.cycle_tasks)
        
        # Проходимся по каждому циклу
        for cycle in self.cycle_tasks:
            waiting_times = []
            task_count = 0
            
            # Проходимся по каждой задаче в данном цикле
            for task in cycle:
                waiting_times.append(task['waiting_time'])
                task_count += 1
            
            # Рассчитываем среднее время ожидания и количество задач для данного цикла
            avg_waiting_time = sum(waiting_times) / len(waiting_times) if waiting_times else 0
            avg_tasks_in_queue = task_count / num_cycles if num_cycles > 0 else 0
            
            # Сохраняем результаты
            total_waiting_time += avg_waiting_time
            total_tasks_in_queue += avg_tasks_in_queue
        
        # Рассчитываем итоговое среднее время ожидания
        avg_waiting_time = total_waiting_time / num_cycles if num_cycles > 0 else 0
        
        # Теперь рассчитываем среднее время ожидания на основе средней длины очереди и интенсивности потока заявок
        arrival_rate = self.completed_tasks / self.simulation_time  # Интенсивность потока заявок
        avg_waiting_time_based_on_queue = avg_tasks_in_queue / arrival_rate if arrival_rate > 0 else 0
        
        return avg_waiting_time, avg_waiting_time_based_on_queue

    def print_results(self):
        total_tasks = Task.count
        completed_tasks = self.completed_tasks
        total_waiting_time = sum(station.total_waiting_time for station in self.stations)
        
        # Загрузка центрального компьютера
        load_percentage = (self.busy_time / (self.simulation_time * WORK_STATIONS)) * 100
        
        # Рассчитываем среднее время ожидания на основе средней длины очереди и интенсивности потока заявок
        avg_waiting_time, avg_waiting_time_based_on_queue = self.calculate_average_waiting_time()

        # Выводим среднее количество задач за цикл
        average_tasks_per_cycle = self.calculate_average_tasks_per_cycle()
        
        
        print("\nРезультаты симуляции:")
        print(f"Общее количество созданных задач: {total_tasks}")
        print(f"Общее количество завершенных задач: {completed_tasks}")
        print(f"Количество задач на станциях на конец моделирования: {total_tasks - completed_tasks - len(self.incomplete_tasks)}")
        print(f"Общее количество обработанных символов: {round(self.total_processed_chars)}")
        print(f"В среднем обработанных символов за цикл: {round(self.total_processed_chars / self.cycle_count)}")
        print(f"Среднее количество задач в одном цикле: {average_tasks_per_cycle:.2f}")
        print(f"Среднее время ожидания обслуживания заявки: {format_time(total_waiting_time / self.cycle_count)}")
        print(f"Загрузка центрального компьютера: {load_percentage:.2f}%")
        print(f"Цикл терминала без использования спец. очереди: {Task.max_length / PROCESSING_SPEED:.2f} сек")

        # Данные из очереди незаконченных задач
        if self.incomplete_tasks:
            avg_length = sum(task.remaining_length for task in self.incomplete_tasks) / len(self.incomplete_tasks)
            print("\nНезавершенные задачи на конец программы:")
            print(f"Количество задач в спец. очереди: {len(self.incomplete_tasks)}")
            print(f"Средняя длина задач в спец. очереди:{round(avg_length)}")
            for task in self.incomplete_tasks:
                print(f"ID: {task.id}, Создана в: {format_time(task.creation_time)}, "
                      f"Осталось: {round(task.remaining_length)}")
        else:
            print("Все задачи завершены.")
            
if __name__ == "__main__":
    computer = CentralComputer()
    computer.simulate()
