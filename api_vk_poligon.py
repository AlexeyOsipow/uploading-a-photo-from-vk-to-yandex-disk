import sys
import time
import requests
import json
from tqdm import tqdm

with open ('tokens.txt', encoding='utf-8') as file_object:
    token_Vk = file_object.readline().strip('token_Vk = ')
    disk_token = file_object.readline().strip('disk_token = "')

def photo_time_convert(time_unix: int):
    time_utc = time.gmtime(time_unix)
    str_date = time.strftime("%m/%d/%Y", time_utc)
    return str_date

class UserVk:
    """Класс по обработк фотографий из вк"""
    def __init__(self, vk_id, quantity_photo):
        self.vk_id = input("Введите id: ")
        self.quantity_photo = input("Введите необходимое количество фотографий: ")

    def get_photo(self):
        response = requests.get('https://api.vk.com/method/photos.get',
                        params={
                            'v': 5.131,
                            'access_token': token_Vk,
                            'owner_id': self.vk_id,
                            'album_id': 'profile',
                            'extended': '1',
                            'count': self.quantity_photo
                        })
        if response.status_code == 200:
            return response.json()
        sys.exit(f"Ошибка , код: {response.status_code}")


    def parsed_photo(self):
        vk_list = self.get_photo()
        vk_list_sorted = vk_list['response']['items']
        vk_list3 = []
        for photos in vk_list_sorted:
            sizes = photos['sizes'][-1]
            vk_list2 = []
            vk_list2.append(sizes['url'])
            vk_list2.append(sizes['type'])
            vk_list2.append(photo_time_convert(photos['date']))
            vk_list2.append(photos['likes']['count'])
            vk_list3.append(vk_list2)
        return vk_list3

    def info_photos_vk_json(self):
        json_file_list = []
        json_file = {
            "count": self.quantity_photo,
            "info": json_file_list
                    }
        for max_photo_url in self.parsed_photo():
            json_file_list.append({
                "file_name": f"{max_photo_url[3]}.jpg",
                'date': max_photo_url[2],
                'url': max_photo_url[0],
                'size': max_photo_url[1]
            })
        return json_file

class UserYandex:
    """Класс по передачи фотографий на Яндекс диск"""
    def __init__(self, token, folder_path, count=5):  # Метод передаваемых переменных
        self.token = token
        self.url = "https://cloud-api.yandex.net/v1/disk/resources"
        self.count = count
        self.folder_path = folder_path
        self.headers = {
            "Authorization": f"OAuth {self.token}",
            "Content-Type": "application/json"
        }

    def create_folder(self):  # метод создаёт папку на диске по указанному пути
        params = {
            "path": self.folder_path
        }
        create_folder = requests.put(self.url, headers=self.headers, params=params)
        if create_folder.status_code == 409:
            return f'По указанному пути /{self.folder_path} уже существует папка ' \
                   f'с таким именем файлы будут загруженны туда'
        elif create_folder.status_code != 201 != 409:
            sys.exit(f"Ошибка ответа, код: {create_folder.status_code}")
        return f'По указанному пути /{self.folder_path} успешно создана папка'

    def delete_folder(self): # Функция удаляет файлы по url
        params = {
            "path": self.folder_path
        }
        delete_folder = requests.delete(self.url, headers=self.headers, params=params)
        if delete_folder.status_code < 300:
            return
        sys.exit(f'Ошибка ответа, код: {delete_folder.status_code}')

    def upload_files(self, info_list):  # Функция загружает файлы по url
        print(self.create_folder())
        url_upload = self.url + "/upload"
        info = info_list['info']
        for index in tqdm(range(len(info)), desc="Прогресс загрузки файлов", unit=" File"):
            name = info[index]['file_name']
            print(name)
            url_photo = info[index]['url']
            params = {
                "path": f"{self.folder_path}/{name}",
                "url": url_photo
            }
            upload_photo = requests.post(url_upload, headers=self.headers, params=params)
            if upload_photo.status_code != 202:
                self.delete_folder()
                sys.exit(f"Ошибка ответа, код: {upload_photo.status_code}\n"
                         f"Папка перемещена в корзину")
        return "Все фотографии успешно загрузились в папку"


if __name__ == '__main__':
    json_name = input('Введите название папки на яндекс диске: ')
    vk = UserVk('vk_id', 'quantity_photo')  # передаём вк токен классу
    with open(json_name + ".json", "w") as file:  # Создаём JSON файл с именем папки
        json.dump(vk.info_photos_vk_json(), file, indent=4)  # Запаковываем JSON информацию в JSON файл
    yandex = UserYandex(disk_token, json_name)  # Передаём  яндекс токен классу
    print(yandex.upload_files(vk.info_photos_vk_json()))