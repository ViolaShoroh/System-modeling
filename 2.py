import random
import multiprocessing

class Reader:
    def __init__(self, arrival_time):
        self.arrival_time = arrival_time #время прибытия читателя в библиотеку (в секундах)
        self.books_requested = 0 #количество книг, запрошенных читателем
        self.wait_time = 0 # Время ожидания в очереди к оператору
        
class Library:
    def __init__(self, R, Tn, To, Tz, Tk, Ts, Tp, Tu, Tv, reading_room_capacity):
        self.R = R
        self.Tn = Tn
        self.To = To
        self.Tz = Tz
        self.Tk = Tk
        self.Ts = Ts
        self.Tp = Tp
        self.Tu = Tu
        self.Tv = Tv
        self.reading_room_time = 55 * 60 # Время, которое читатель проводит в читальном зале
        self.reading_room_capacity = reading_room_capacity 

        # Очереди
        self.queue_operator = multiprocessing.Queue() # Очередь к оператору
        self.librarian_queue = multiprocessing.Queue() # Очередь к библиотекарю
        self.reading_room = [] # Читальный зал
        self.reading_room_queue = multiprocessing.Queue() # Очередь в читальный зал

        # Счетчики
        self.total_readers = 0 #общее количество обслуживаемых читателей
        self.operator_work_time = 0 #время, которое оператор потратил на обслу-живание (в секундах)
        self.total_wait_time = 0 #общее время ожидания всех читателей (в секун-дах)
        self.next_reader_time = 0 #время прихода следующего читателя
        self.books_issued = 0 #общее количество выданных книг

        self.book_request_probabilities = {
            1: 0,
            2: 0.7,
            3: 0.2,
            4: 0.03,
            5: 0,
            6: 0.03,
            7: 0.04
        }
        #состоит из books_requested и probability

    def add_reader(self, reader):
        self.queue_operator.put(reader) #добавление читателя в очередь к операто-ру

    def process_requests(self):
        current_time = 0 #текущее время рабочего дня
        while current_time < self.R:
            # Генерация нового читателя 
            if current_time >= self.next_reader_time:
                new_reader = Reader(current_time)
                self.add_reader(new_reader)
                self.next_reader_time = current_time + self.Tn #приход следующего читателя
                hours = current_time // 3600 #Целое количество часов
                minutes = (current_time % 3600) // 60 #Остаток в минутах
                print(f"Читатель прибыл в {hours:.0f} ч {minutes:.0f} мин")
                self.total_readers += 1

            # Обработка очереди к оператору
            if not self.queue_operator.empty():
                reader = self.queue_operator.get() #берется 1 читатель

                #Определение количества книг, запрошенных читателем
                self.generate_book_request(reader)
                self.books_issued += reader.books_requested

                # Обслуживание оператором
                operator_service_time = self.To + self.Tz + self.Tk + self.Tp + self.Tu * reader.books_requested
                self.operator_work_time += operator_service_time
                print(f"Читатель обслужился у оператора")

                # Вычисление времени ожидания 
                reader.wait_time = current_time - reader.arrival_time
                self.total_wait_time += reader.wait_time

                # Перевод читателя в очередь к библиотекарю
                self.librarian_queue.put(reader)

                # Увеличение текущего времени
                current_time += operator_service_time
                
            # Обработка очереди к библиотекарю
            if not self.librarian_queue.empty():
                reader = self.librarian_queue.get()
                current_time += self.Tv
                print(f"Читатель обслуживается библиотекарем, взяв {reader.books_requested} книг")

                # Перевод читателя в очередь на вход в читальный зал
                self.reading_room_queue.put(reader)
                
            # Проверка и обработка читателей в читальном зале
            self.check_reading_room(current_time)

        self.print_results()

    def check_reading_room(self, current_time):
        # Проверка, не пора ли читателям покинуть читальный зал
        for i, reader in enumerate(self.reading_room):
            if reader.arrival_time + self.reading_room_time <= current_time:
                hours = current_time // 3600
                minutes = (current_time % 3600) // 60
                print(f"Читатель покинул читальный зал в {hours:.0f} ч {minutes:.0f} мин")
                self.reading_room.pop(i)

        # Проверка очереди на вход в читальный зал
        if not self.reading_room_queue.empty() and len(self.reading_room) < self.reading_room_capacity:
            reader = self.reading_room_queue.get()
            self.reading_room.append(reader)
            print(f"Читатель вошел в читальный зал")

        if current_time >= self.R: # Проверка на конец рабочего дня
            return len(self.reading_room)

    def generate_book_request(self, reader):
        # Генерация кол-ва книг
        random_number = random.random() #создаётся случайное число от 0 до 1
        cumulative_probability = 0 #для накопления вероятностей
        for books_requested, probability in self.book_request_probabilities.items():
            cumulative_probability += probability 
            if random_number <= cumulative_probability:
                reader.books_requested = books_requested
                break

    def print_results(self):
        print("-" * 30)
        print(f"Общее количество читателей: {self.total_readers}")
        print(f"Общее количество выданных книг: {self.books_issued}")
        print(f"Количество читателей в читальном зале под конец рабочего дня: {len(self.reading_room)}")
        print(f"Среднее время ожидания к оператору ПК: {self.total_wait_time / self.total_readers} сек")

def calculate_intensity_for_target_utilization(simulation, target_utilization):
    total_operator_time = simulation.operator_work_time #общее время работы оператора
    average_operator_time = total_operator_time / simulation.total_readers #среднее время обслуживания оператора
    intensity = (target_utilization * 3600) / average_operator_time #интенсивность потока читателей (чел/час)
    return intensity

def main():
    R = 8 * 3600  #рабочий день в сек
    Tn = random.randint(48, 360)  #интервал между приходом читателей в сек
    To = random.randint(33, 75)  #время объяснения требований оператору (сек)
    Tz = random.randint(33, 75)  #время печати запроса (сек)
    Tk = random.randint(1, 4)  #время поиска информации (сек)
    Ts = 0  #время выбора книг (сек)
    Tp = random.randint(0, 4)  #время печати листка требования (сек)
    Tu = random.randint(7, 17)  #время уточнения запроса (сек)
    Tv = random.uniform(2.7, 4) * 60  #время библиотекаря в секундах
    reading_room_capacity = 50 #ёмкость читального зала

    library = Library(R, Tn, To, Tz, Tk, Ts, Tp, Tu, Tv, reading_room_capacity)

    # Запуск моделирования
    library.process_requests()

    #Интенсивность
    intensity_80 = calculate_intensity_for_target_utilization(library, 0.8)
    intensity_85 = calculate_intensity_for_target_utilization(library, 0.85)
    print(f"Интенсивность при загрузке на 80%: {intensity_80:.2f} чел/час")
    print(f"Интенсивность при загрузке на 85%: {intensity_85:.2f} чел/час")

if __name__ == "__main__":
    main()
