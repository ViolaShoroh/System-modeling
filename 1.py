import random
import queue

class Reader:
    def __init__(self, arrival_time):
        self.arrival_time = arrival_time #время прибытия читателя в библио-теку (в секундах)
        self.service_time = 0 #время, проведенное у оператора (в секундах)
        self.departure_time = 0 #время ухода из библиотеки (в секундах)

class Library:
    def __init__(self, R, Tn, To, Tz, Tk, Ts, Tp, Tu, Tv):
        self.R = R 
        self.Tn = Tn 
        self.To = To 
        self.Tz = Tz 
        self.Tk = Tk 
        self.Ts = Ts 
        self.Tp = Tp 
        self.Tu = Tu 
        self.Tv = Tv 
        self.readers = [] #список всех читателей
        self.queue_operator = queue.Queue() #очередь к оператору
        self.librarian_queue = queue.Queue() #очередь к библиотекарю
        self.total_wait_time = 0 #общее время ожидания всех читателей (в секундах)
        self.total_readers = 0 #общее количество обслуживаемых читателей
        self.operator_work_time = 0 #время, которое оператор потратил на обслуживание (в секундах)
        self.librarian_work_time = 0 #время, которое библиотекарь потратил на обслуживание (в секундах)

    def add_reader(self, reader):
        self.queue_operator.put(reader) #добавление читателя в очередь к оператору

    def process_requests(self):
        current_time = 0 #текущее время рабочего дня
        while current_time < self.R: 
            # Обработка оператора
            if not self.queue_operator.empty(): 
                reader = self.queue_operator.get() #беретсяя 1 читатель
                hours = reader.arrival_time // 3600 # Целое количество часов
                minutes = (reader.arrival_time % 3600) // 60 # Остаток в минутах
                print(f"Читатель прибыл в {hours:.0f} ч {minutes:.0f} мин")
                
                #время, проведенное у оператора (по сути, время обслужива-ния)
                operator_service_time = self.To + self.Tz + self.Tk + self.Ts + self.Tp + self.Tu
                reader.service_time = operator_service_time #время обслужива-ния для этого читателя
                self.operator_work_time += operator_service_time #увеличение общего времени работы оператора
                print(f"Читатель обслужился у оператором")

                self.total_wait_time += reader.service_time #увеличение общего времени ожидания
                self.total_readers += 1 #увеличиваем общего количества обслу-живаемых читателей
                
                self.librarian_queue.put(reader) #читатель уходит в очередь к библиотекарю
                current_time += operator_service_time #увеличение текущего времени обслуживания

            # Обработка библиотекаря
            if not self.librarian_queue.empty(): 
                reader = self.librarian_queue.get()
                print(f"Читатель обслуживается библиотекарем")
                
                self.librarian_work_time += self.Tv #увеличение времени рабо-ты библиотекаря
                reader.departure_time = current_time + self.Tv #время ухода чи-тателя
                current_time += self.Tv #увеличение текущего времени обслу-живания библиотекаря
                hours = reader.departure_time // 3600 
                minutes = (reader.departure_time % 3600) // 60 
                print(f"Читатель покинул библиотеку в {hours:.0f} ч {minutes:.0f} мин") 

            # Если нет читателей в очереди, продвигаем время
            else:
                current_time += 1 #+ время на 1 секунду

    def average_wait_time(self):
        if self.total_readers > 0:
            return self.total_wait_time / self.total_readers #среднее время ожи-дания = (общее время ожидания) / (количество обслуживаемых читателей)
        return 0 #tсли читателей нет

def calculate_intensity_for_target_utilization(simulation, target_utilization):
    total_operator_time = simulation.operator_work_time #общее время ра-боты оператора
    average_operator_time = total_operator_time / simulation.total_readers #среднее время обслуживания оператора
    intensity = (target_utilization * 3600) / average_operator_time #интен-сивность потока читателей (чел/час)
    return intensity

def main():
    R = 8 * 3600 #рабочий день в сек
    Tn = random.randint(48, 360) #интервал между приходом читателей в сек
    To = random.randint(33, 75) #время объяснения требований оператору (сек)
    Tz = random.randint(33, 75) #время печати запроса (сек)
    Tk = random.randint(1, 4) #время поиска информации (сек)
    Ts = 0 #время выбора книг (сек)
    Tp = random.randint(0, 4) #время печати листка требования (сек)
    Tu = random.randint(7, 17) #время уточнения запроса (сек)
    Tv = random.uniform(2.7, 4) * 60 #время библиотекаря в секундах
    library = Library(R, Tn, To, Tz, Tk, Ts, Tp, Tu, Tv) #объект библиотеки с заданными параметрами

    arrival_time = 0 # Текущее время
    
    while arrival_time < R:
        library.add_reader(Reader(arrival_time)) #создаем нового читателя с текущим временем прибытия и добавляем его в очередь к оператору
        arrival_time += Tn 
    library.process_requests()

    avg_wait_time = library.average_wait_time() #среднее время ожидания
    print(f"Среднее время ожидания к оператору ПК: {avg_wait_time / 60:.2f} минут")
    
    #Интенсивность
    intensity_80 = calculate_intensity_for_target_utilization(library, 0.8) 
    intensity_85 = calculate_intensity_for_target_utilization(library, 0.85) 
    print(f"Интенсивность при загрузке на 80%: {intensity_80:.2f} чел/час")
    print(f"Интенсивность при загрузке на 85%: {intensity_85:.2f} чел/час")

if __name__ == "__main__":
    main()
