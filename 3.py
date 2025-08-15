import random
import multiprocessing
from queue import PriorityQueue
import matplotlib.pyplot as plt
import seaborn as sns
import collections
from collections import defaultdict


class Reader:
    def __init__(self, arrival_time, is_teacher):
        self.arrival_time = arrival_time #время прибытия читателя в библиотеку 
        self.books_requested = 0 #количество книг, запрошенных читателем
        self.wait_time1 = 0 #время ожидания в очереди к оператору1 (студенты)
        self.wait_time2 = 0 #время ожидания в очереди к оператору2 (преподаватели)
        self.is_teacher = is_teacher #флаг преподавателя

    def __lt__(self, other):
        # Проверка приоритета
        if self.is_teacher and not other.is_teacher:
            return True
        elif not self.is_teacher and other.is_teacher:
            return False

class Library:
    def __init__(self, R, To, Tz, Tk, Ts, Tp, Tu, Tv, Tn, reading_room_capacity,
                 teacher_Tn, teacher_To, teacher_Tz, teacher_Tk, teacher_Ts, teacher_Tp, teacher_Tu, teacher_Tv):
        self.R = R
        self.Tn = Tn
        self.To = To
        self.Tz = Tz 
        self.Tk = Tk
        self.Ts = Ts
        self.Tp = Tp 
        self.Tu = Tu 
        self.Tv = Tv
        
        
        self.reading_room_time = 55 * 60 # Время, которое читатель проводит в читальном зале (55 минут = 3300 секунд)
        self.reading_room_capacity = reading_room_capacity 

        # Параметры для преподавателей
        self.teacher_Tn = teacher_Tn 
        self.teacher_To = teacher_To 
        self.teacher_Tz = teacher_Tz 
        self.teacher_Tk = teacher_Tk 
        self.teacher_Ts = teacher_Ts 
        self.teacher_Tp = teacher_Tp 
        self.teacher_Tu = teacher_Tu 
        self.teacher_Tv = teacher_Tv

        # Очереди
        self.queue_operator = multiprocessing.Queue() #очередь к оператору (для студентов)
        self.queue_operator_teacher = multiprocessing.Queue() #очередь к оператору (для преподавателей)
        self.librarian_queue = PriorityQueue() #очередь к библиотекарю
        self.reading_room = [] #читальный зал
        self.reading_room_hourly_data = collections.defaultdict(int) #словарь для хранения количества читателей по часам
        self.reading_room_queue = multiprocessing.Queue() #очередь в читальный зал

        # Счетчики
        self.total_readers1 = 0 #общее количество обслуживаемых читателей у оператора1
        self.total_readers2 = 0 #общее количество обслуживаемых читателей у оператора2
        self.operator1_work_time = 0 #время, которое оператор1 потратил на обслуживание
        self.operator2_work_time = 0 #время, которое оператор2 потратил на обслуживание
        self.total_wait_time1 = 0 #общее время ожидания всех читателей (в секундах) у оператора1
        self.total_wait_time2 = 0 #общее время ожидания всех читателей (в секундах) у оператора2
        self.next_reader_time = 0 #время прихода следующего читателя-студента
        self.next_reader_time_teacher = 0 #время прихода следующего читателя-преподавателя
        self.books_issued = 0 # общее количество выданных книг

        self.librarian_hourly_data = [] #данные по работе библиотекаря по часам
        self.librarian_work_time = 0
        self.librarian_busy_times = [] #список интервалов занятости библиотекаря
        self.librarian_hourly_busy_time = collections.defaultdict(int) #время занятости библиотекаря для каждого часа

        # Вероятности запроса книг
        self.book_request_probabilities = {
            1: 0,
            2: 0.7,
            3: 0.2,
            4: 0.03,
            5: 0,
            6: 0.03,
            7: 0.04
        }

    def process_requests(self):
        current_time = 0
        while current_time < self.R:
            # Генерация нового студента
            if current_time >= self.next_reader_time:
                reader = Reader(current_time, is_teacher=False)
                self.next_reader_time = current_time + self.Tn # приход следующего студента
                hours = current_time // 3600 # Целое количество часов
                minutes = (current_time % 3600) // 60 # Остаток в минутах
                print(f"Студент прибыл в {hours:.0f} ч {minutes:.0f} мин")
                self.total_readers1 += 1
                self.queue_operator.put(reader)

            # Генерация нового преподавателя
            if current_time >= self.next_reader_time_teacher:
                reader = Reader(current_time, is_teacher=True)
                self.next_reader_time_teacher = current_time + self.teacher_Tn # приход следующего преподавателя
                hours = current_time // 3600 # Целое количество часов
                minutes = (current_time % 3600) // 60 # Остаток в минутах
                print(f"Преподаватель прибыл в {hours:.0f} ч {minutes:.0f} мин")
                self.total_readers2 += 1
                self.queue_operator_teacher.put(reader)

            # Обработка очереди к оператору (для студентов)
            if not self.queue_operator.empty():
                reader = self.queue_operator.get()
                self.generate_book_request(reader)
                self.books_issued += reader.books_requested
                
                operator1_service_time = self.To + self.Tz + self.Tk + self.Tp + self.Tu * reader.books_requested
                reader.service_time1 = operator1_service_time
                self.operator1_work_time += operator1_service_time
                current_time += operator1_service_time
                if current_time > self.R:
                    break
                print(f"Оператор (студенты) обслужил читателя с {reader.books_requested} книгами")

                if current_time > reader.arrival_time:
                    current_time = reader.arrival_time

                # Вычисление времени ожидания
                reader.wait_time1 = current_time - reader.arrival_time
                if reader.wait_time1 < 0:
                    reader.wait_time1 = 0
                self.total_wait_time1 += reader.wait_time1
                
                # Перевод читателя в очередь к библиотекарю
                self.librarian_queue.put((reader.wait_time1, reader))
                
                
            # Обработка очереди к оператору (для преподавателей)
            if not self.queue_operator_teacher.empty():
                reader = self.queue_operator_teacher.get()
                self.generate_book_request(reader)
                self.books_issued += reader.books_requested
                operator2_service_time = self.teacher_To + self.teacher_Tz + self.teacher_Tk + self.teacher_Tp + self.teacher_Tu * reader.books_requested + self.teacher_Ts
                reader.service_time2 = operator2_service_time
                self.operator2_work_time += operator2_service_time
                current_time += operator2_service_time
                if current_time > self.R:
                    break
                print(f"Оператор (преподаватели) обслужил читателя с {reader.books_requested} книгами")

                if current_time > reader.arrival_time:
                    current_time = reader.arrival_time

                # Вычисление времени ожидания
                reader.wait_time2 = current_time - reader.arrival_time
                if reader.wait_time2 < 0:
                    reader.wait_time2 = 0
                self.total_wait_time2 += reader.wait_time2

                # Перевод читателя в очередь к библиотекарю
                self.librarian_queue.put((reader.wait_time2, reader))
                

            # Обработка очереди к библиотекарю
            if not self.librarian_queue.empty():
                _, reader = self.librarian_queue.get()
                if current_time >= self.R:
                    break
                
                if reader.is_teacher:
                    current_time += self.teacher_Tv
                    if current_time >= self.R:
                        break
                    hour = current_time // 3600 # Текущий час
                    self.librarian_hourly_busy_time[hour] += self.teacher_Tv
                    print(f"Библиотекарь обслуживает читателя-преподавателя")
                    self.librarian_hourly_data.append((current_time // 3600, 1, self.teacher_Tv)) 
                else:
                    current_time += self.Tv
                    if current_time >= self.R:
                        break
                    hour = current_time // 3600 # Текущий час
                    self.librarian_hourly_busy_time[hour] += self.Tv
                    print(f"Библиотекарь обслуживает читателя-студента")
                    self.librarian_hourly_data.append((current_time // 3600, 1, self.Tv))
                
                reader.departure_time = current_time
                self.reading_room_queue.put(reader)

            # Проверка и обработка читателей в читальном зале
            self.check_reading_room(current_time)


        self.print_statistics()

    def check_reading_room(self, current_time):
        hour = current_time // 3600 # Текущий час

        # Проверка, не пора ли читателям покинуть читальный зал
        self.reading_room = [reader for reader in self.reading_room if reader.arrival_time + self.reading_room_time > current_time]

        # Обновление статистики по количеству читателей в текущем часу
        self.reading_room_hourly_data[hour] = len(self.reading_room)
        
        if not self.reading_room_queue.empty() and len(self.reading_room) < self.reading_room_capacity:
            reader = self.reading_room_queue.get()
            self.reading_room.append(reader)
            print(f"Читатель вошел в читальный зал")

    def generate_book_request(self, reader):
        # Генерация кол-ва книг
        random_number = random.random() # создаётся случайное число от 0 до 1
        cumulative_probability = 0 # для накопления вероятностей
        for books_requested, probability in self.book_request_probabilities.items():
            cumulative_probability += probability
            if random_number <= cumulative_probability:
                reader.books_requested = books_requested
                break

    def calculate_librarian_utilization(self, total_simulation_time):
        total_busy_time = sum(end - start for start, end in self.librarian_busy_times)
        utilization = total_busy_time / total_simulation_time if total_simulation_time > 0 else 0
        return utilization

    def print_statistics(self):
        print("-" * 30)
        print(f"Общее количество обслуживаемых читателей: {self.total_readers1 + self.total_readers2}")
        print(f"Общее количество выданных книг: {self.books_issued}")
        print(f"Количество читателей в читальном зале под конец рабочего дня: {len(self.reading_room)}")
        print(f"Среднее время ожидания к оператору ПК 1: {self.total_wait_time1 / self.total_readers1} сек")
        print(f"Среднее время ожидания к оператору ПК 2: {self.total_wait_time2 / self.total_readers2} сек")

    def visualize_data(self, total_simulation_time, expected_service_time=240):
        #a.	количество обслуженных библиотекарем читателей в час 
        hourly_served_readers = defaultdict(int) # Используем defaultdict для упрощения
        for hour, count, _ in self.librarian_hourly_data:
            hourly_served_readers[hour] += count

        hours = sorted(hourly_served_readers.keys())
        counts = [hourly_served_readers[h] for h in hours]
        max_count = max(counts) # Находим максимальное количество обслуженных читателей
        plt.figure(figsize=(10, 6))
        plt.bar([h + 1 for h in hours], counts)
        plt.xlabel("Час работы библиотеки")
        plt.ylabel("Количество обслуженных читателей")
        plt.title("Количество обслуженных библиотекарем читателей в час")

        #ось OY с шагом 1 от 0 до максимального значения + 1
        plt.yticks(range(0, max_count + 1, 1))
        plt.show()

        #b. среднее время обслуживания читателей у библиотекаря
        service_times = [time for _, _, time in self.librarian_hourly_data]
        noisy_data = [x + random.gauss(0, 1) for x in service_times]
        # Создание boxplot
        plt.figure(figsize=(10, 6))
        sns.boxplot(y=noisy_data, orient='v')
        #print(service_times)
        
        plt.ylabel("Время обслуживания (секунды)")
        plt.title("Распределение времени обслуживания читателей у библиотекаря")
        plt.grid(axis='y')
        plt.show()

        # c. среднее количество читателей в читальном зале в час
        hours = sorted(self.reading_room_hourly_data.keys())
        counts = [self.reading_room_hourly_data[hour] for hour in hours]
        plt.figure(figsize=(10, 6))
        plt.bar([h + 1 for h in hours], counts)
        plt.xlabel("Час работы библиотеки")
        plt.ylabel("Среднее количество читателей в читальном зале")
        plt.title("Среднее количество читателей в читальном зале по часам")
        plt.xticks(range(1, len(hours) + 1))
        plt.grid(True)
        plt.show()

        # d. Загруженность библиотекаря
        hourly_data = defaultdict(lambda: {'served': 0, 'busy_time': 0})
        for hour, served, busy_time in self.librarian_hourly_data:
            hourly_data[hour]['served'] += served
            hourly_data[hour]['busy_time'] += busy_time

        hours = sorted(hourly_data.keys())
        busy_times = [hourly_data[h]['busy_time'] for h in hours]
        served_readers = [hourly_data[h]['served'] for h in hours]

        expected_busy_time = [readers * expected_service_time for readers in served_readers]

        busy_percentage = []
        for busy_time, expected_time in zip(busy_times, expected_busy_time):
            if expected_time > 0:
                percentage = (busy_time / expected_time) * 100
            else:
                percentage = 0
            busy_percentage.append(percentage)

        fig, ax = plt.subplots()
        ax.bar([h + 1 for h in hours], busy_percentage, label='Занятость')
        for i, p in enumerate(busy_percentage):
            ax.text(i + 1, p / 2, f"{p:.0f}%", ha="center", va="center", color="white")

        ax.set_xlabel("Час")
        ax.set_ylabel("Загруженность (%)")
        ax.set_title("Загруженность библиотекаря по часам")
        ax.set_xticks(range(1, len(hours) + 1))
        ax.set_yticks(range(0, 101, 10))
        ax.legend()
        plt.show()


def calculate_intensity_for_target_utilization1(simulation, target_utilization):
    total_operator_time1 = simulation.operator1_work_time # общее время работы оператора
    average_operator_time1 = total_operator_time1 / simulation.total_readers1 # среднее время обслуживания оператора
    intensity1 = (target_utilization * 3600) / average_operator_time1 # интенсивность потока читателей (чел/час)
    return intensity1

def calculate_intensity_for_target_utilization2(simulation, target_utilization):
    total_operator_time2 = simulation.operator2_work_time # общее время работы оператора
    average_operator_time2 = total_operator_time2 / simulation.total_readers2 # среднее время обслуживания оператора
    intensity2 = (target_utilization * 3600) / average_operator_time2
    return intensity2

def main():
    R = 8 * 3600 # Рабочий день в секундах
    
    Tn = random.randint(48, 360) # интервал между приходом читателей в сек
    To = random.randint(33, 75) # время объяснения требований оператору (сек)
    Tz = random.randint(33, 75) # время печати запроса (сек)
    Tk = random.randint(1, 4) # время поиска информации (сек)
    Ts = 0 # время выбора книг (сек)
    Tp = random.randint(0, 4) # время печати листка требования (сек)
    Tu = random.randint(7, 17) # время уточнения запроса (сек)
    Tv = random.randint(162, 240) # время библиотекаря в секундах


    reading_room_capacity = 50 # ёмкость читального зала

    # Параметры для преподавателей
    teacher_Tn = random.randint(10, 20) * 60 
    teacher_To = random.randint(5, 10) 
    teacher_Tz = random.randint(10, 20) 
    teacher_Tk = random.randint(15, 20) 
    teacher_Ts = random.randint(5, 7) 
    teacher_Tp = random.randint(5, 10)
    teacher_Tu = random.randint(10, 30) 
    teacher_Tv = random.randint(90, 180)


    # Создание экземпляра библиотеки
    library = Library(R, To, Tz, Tk, Tp, Tu, Ts, Tv, Tn, reading_room_capacity, 
                      teacher_Tn, teacher_To, teacher_Tz, teacher_Tk, teacher_Ts, teacher_Tp, teacher_Tu, teacher_Tv)

    #запуск моделирования
    library.process_requests()

    #функция для визуализации данных
    library.visualize_data(library.R)

    #интенсивностб оператора 1
    intensity_80_1 = calculate_intensity_for_target_utilization1(library, 0.8)
    intensity_85_1 = calculate_intensity_for_target_utilization1(library, 0.85)
    print(f"Интенсивность для 1 оператора при загрузке на 80%: {intensity_80_1:.2f} чел/час")
    print(f"Интенсивность для 1 оператора при загрузке на 85%: {intensity_85_1:.2f} чел/час")

    #интенсивность оператора 2
    intensity_80_2 = calculate_intensity_for_target_utilization2(library, 0.8)
    intensity_85_2 = calculate_intensity_for_target_utilization2(library, 0.85)
    print(f"Интенсивность для 2 оператора при загрузке на 80%: {intensity_80_2:.2f} чел/час")
    print(f"Интенсивность для 2 оператора при загрузке на 85%: {intensity_85_2:.2f} чел/час")

if __name__ == "__main__":
    main()
